"""Track A backtest engine: simulate the dial (target weight) on real
TQQQ/SQQQ dollar prices, 2010-onward.

No leverage simulation, no synthetic decay modeling -- this only ever
multiplies real historical TQQQ/SQQQ closing prices, so daily-reset decay
and fund costs are already baked in exactly as they happened.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import config
from .exits import ExitConfig, apply_exit_overlay
from .signals import compute_signal
from .sizing import SizingConfig, apply_sizing

TRADING_DAYS_PER_YEAR = 252

# Job1-only baseline: an ExitConfig with every Job 3 rule turned off exactly
# reproduces the raw entry-signal-flip-only exit (see test_exits.py), so this
# doubles as run_backtest's "no overlay" default.
_NO_EXIT_OVERLAY = ExitConfig(
    enable_stop_loss=False, enable_fast_trend_break=False, enable_mean_reversion_exit=False
)


@dataclass
class BacktestResult:
    trade_log: list[dict] = field(default_factory=list)
    equity_curve: list[dict] = field(default_factory=list)
    drawdown: list[dict] = field(default_factory=list)
    monthly_returns: list[dict] = field(default_factory=list)
    summary: dict = field(default_factory=dict)


def _build_trade_log(
    sized_weight: pd.Series,
    tqqq: pd.Series,
    sqqq: pd.Series,
    equity_curve: pd.Series,
    exit_reason: pd.Series,
) -> list[dict]:
    """sized_weight may be fractional (Job 2 sizing) rather than strictly
    ±1/0 -- sign(sized_weight) is always the Job1+Job3 direction, magnitude
    is how much capital is actually deployed. A pure magnitude change with
    the same sign (a resize, not a real exit) shows up as its own row with
    exit_reason="resize" rather than a signal-flip/stop-loss/etc reason,
    since exits.py's reasons only cover real direction changes."""
    dates = sized_weight.index
    group_id = (sized_weight != sized_weight.shift()).cumsum()
    trades: list[dict] = []

    for _, idx in sized_weight.groupby(group_id).groups.items():
        weight = sized_weight.loc[idx[0]]
        if weight == 0:
            continue  # cash periods aren't trades

        entry_date = idx[0]
        last_held_date = idx[-1]
        entry_pos = dates.get_loc(entry_date)
        last_held_pos = dates.get_loc(last_held_date)
        asset = tqqq if weight > 0 else sqqq
        symbol = config.LONG_TICKER if weight > 0 else config.SHORT_TICKER

        is_open = last_held_pos == len(dates) - 1
        if is_open:
            exit_date = last_held_date
            sell_price = float(asset.iloc[last_held_pos])
            reason = None
        else:
            exit_date = dates[last_held_pos + 1]
            sell_price = float(asset.loc[exit_date])
            reason = exit_reason.loc[exit_date] or "resize"

        buy_price = float(asset.loc[entry_date])
        capital_at_entry = float(equity_curve.loc[entry_date])
        capital_deployed = capital_at_entry * abs(weight)
        share_size = capital_deployed / buy_price if buy_price else 0.0
        profit = share_size * (sell_price - buy_price)
        profit_pct = (sell_price / buy_price - 1.0) if buy_price else 0.0

        trades.append(
            {
                "symbol": symbol,
                "start_date": entry_date.strftime("%Y-%m-%d"),
                "end_date": exit_date.strftime("%Y-%m-%d"),
                "duration_days": (exit_date - entry_date).days,
                "buy_price": round(buy_price, 4),
                "sell_price": round(sell_price, 4),
                "share_size": round(share_size, 4),
                "size_pct": round(abs(weight) * 100, 1),
                "profit": round(profit, 2),
                "profit_pct": round(profit_pct * 100, 3),
                "is_profitable": bool(profit > 0),
                "is_short": bool(weight < 0),
                "is_open": bool(is_open),
                "exit_reason": reason,
            }
        )

    return trades


def _drawdown_series(equity_curve: pd.Series) -> pd.Series:
    running_max = equity_curve.cummax()
    return equity_curve / running_max - 1.0


def _max_drawdown_and_duration(equity_curve: pd.Series) -> tuple[float, int]:
    dd = _drawdown_series(equity_curve)
    max_dd = float(dd.min()) if len(dd) else 0.0

    running_max = equity_curve.cummax()
    longest = 0
    peak_date = equity_curve.index[0] if len(equity_curve) else None
    for date, value in equity_curve.items():
        if value >= running_max.loc[date]:
            peak_date = date
        else:
            longest = max(longest, (date - peak_date).days)

    return max_dd, longest


def _monthly_returns(equity_curve: pd.Series) -> list[dict]:
    monthly = equity_curve.resample("ME").last()
    monthly_returns = monthly.pct_change()
    first_val = equity_curve.iloc[0]
    if len(monthly) and monthly.index[0].to_period("M") == equity_curve.index[0].to_period("M"):
        monthly_returns.iloc[0] = monthly.iloc[0] / first_val - 1.0

    rows = []
    for date, ret in monthly_returns.items():
        if pd.isna(ret):
            continue
        rows.append(
            {
                "year": date.year,
                "month": date.month,
                "return_pct": round(float(ret) * 100, 3),
            }
        )
    return rows


def _summary_stats(
    equity_curve: pd.Series,
    trades: list[dict],
    max_dd: float,
    max_dd_days: int,
) -> dict:
    start_val = float(equity_curve.iloc[0])
    end_val = float(equity_curve.iloc[-1])
    n_days = (equity_curve.index[-1] - equity_curve.index[0]).days
    years = max(n_days / 365.25, 1e-9)
    cagr = (end_val / start_val) ** (1 / years) - 1 if start_val > 0 else 0.0

    completed = [t for t in trades if not t["is_open"]]
    n_trades = len(completed)
    wins = [t for t in completed if t["is_profitable"]]
    losses = [t for t in completed if not t["is_profitable"]]
    win_rate = (len(wins) / n_trades) if n_trades else 0.0

    avg_win = float(np.mean([t["profit_pct"] for t in wins])) if wins else 0.0
    avg_loss = float(np.mean([t["profit_pct"] for t in losses])) if losses else 0.0
    profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss else float("inf") if avg_win else 0.0

    exit_reason_breakdown: dict[str, int] = {}
    for t in completed:
        reason = t["exit_reason"] or "unknown"
        exit_reason_breakdown[reason] = exit_reason_breakdown.get(reason, 0) + 1

    return {
        "start_date": equity_curve.index[0].strftime("%Y-%m-%d"),
        "end_date": equity_curve.index[-1].strftime("%Y-%m-%d"),
        "initial_capital": round(start_val, 2),
        "final_equity": round(end_val, 2),
        "cagr_pct": round(cagr * 100, 3),
        "total_return_pct": round((end_val / start_val - 1) * 100, 3),
        "num_trades": n_trades,
        "win_rate_pct": round(win_rate * 100, 2),
        "profit_loss_ratio": round(profit_loss_ratio, 3) if np.isfinite(profit_loss_ratio) else None,
        "max_drawdown_pct": round(max_dd * 100, 3),
        "max_drawdown_days": max_dd_days,
        "exit_reason_breakdown": exit_reason_breakdown,
    }


def run_backtest(
    dataset: pd.DataFrame,
    initial_capital: float = 10_000.0,
    exit_config: ExitConfig | None = None,
    sizing_config: SizingConfig | None = None,
) -> BacktestResult:
    """dataset must have columns: ndx, tqqq, sqqq, qqq (Close prices), indexed by Date.

    exit_config controls the Job 3 exit overlay (stop-loss, fast trend-break,
    mean-reversion extension) on top of the Job 1 entry signal. Defaults to
    no overlay -- exits purely by the Job 1 signal flipping.

    sizing_config controls the Job 2 position-sizing overlay (rate-of-change
    based). Defaults to disabled -- always 100% in or out."""
    signal_df = compute_signal(dataset["ndx"])
    overlay = apply_exit_overlay(dataset, signal_df, exit_config or _NO_EXIT_OVERLAY)
    sized_weight = apply_sizing(overlay.effective_weight, dataset["ndx"], sizing_config or SizingConfig(enabled=False))

    tqqq_ret = dataset["tqqq"].pct_change().fillna(0.0)
    sqqq_ret = dataset["sqqq"].pct_change().fillna(0.0)
    qqq_ret = dataset["qqq"].pct_change().fillna(0.0)

    # weight_shifted's sign picks the asset; its magnitude (Job 2 sizing) is
    # how much of yesterday's total equity that day's return is applied to,
    # i.e. the strategy rebalances daily to hold a constant target fraction
    # (matching the spec's "each day set ONE number: a target weight").
    weight_shifted = sized_weight.shift(1).fillna(0.0)
    asset_ret = np.where(weight_shifted > 0, tqqq_ret, np.where(weight_shifted < 0, sqqq_ret, 0.0))
    strategy_ret = pd.Series(weight_shifted.abs().to_numpy() * asset_ret, index=dataset.index)

    equity_curve = initial_capital * (1 + strategy_ret).cumprod()
    benchmark_curve = initial_capital * (1 + qqq_ret).cumprod()

    dd_series = _drawdown_series(equity_curve)
    max_dd, max_dd_days = _max_drawdown_and_duration(equity_curve)

    trades = _build_trade_log(
        sized_weight, dataset["tqqq"], dataset["sqqq"], equity_curve, overlay.exit_reason
    )
    monthly = _monthly_returns(equity_curve)
    summary = _summary_stats(equity_curve, trades, max_dd, max_dd_days)

    equity_curve_rows = [
        {
            "date": d.strftime("%Y-%m-%d"),
            "strategy_equity": round(float(s), 2),
            "benchmark_equity": round(float(b), 2),
            "target_weight": float(sized_weight.loc[d]),
        }
        for d, s, b in zip(dataset.index, equity_curve, benchmark_curve)
    ]
    drawdown_rows = [
        {"date": d.strftime("%Y-%m-%d"), "drawdown_pct": round(float(v) * 100, 3)}
        for d, v in dd_series.items()
    ]

    return BacktestResult(
        trade_log=trades,
        equity_curve=equity_curve_rows,
        drawdown=drawdown_rows,
        monthly_returns=monthly,
        summary=summary,
    )
