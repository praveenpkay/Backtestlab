"""Walk-forward validation: split the tested history into an earlier chunk
and a later chunk that's treated as never-looked-at, and report performance
on each separately. The point isn't fitting new parameters per chunk (this
strategy's rules are fixed heuristics, not optimized ones) -- it's checking
whether a scenario that looks good over the WHOLE period still looks good
on the back half alone, or whether it's front-loaded on a lucky stretch.
Flags loudly when in-sample and out-of-sample diverge.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .backtest import _max_drawdown_and_duration, run_backtest
from .exits import ExitConfig
from .kpis import compute_calmar_ratio, compute_consecutive_loss_stats, compute_worst_day
from .sizing import SizingConfig


def _rebase_equity(equity: pd.Series, initial_capital: float) -> pd.Series:
    """Treats this slice as if it started fresh with initial_capital, so its
    own drawdowns/CAGR aren't contaminated by what happened before the split."""
    return equity / equity.iloc[0] * initial_capital


def _build_period_kpis(equity: pd.Series, trades: list[dict]) -> dict:
    start_val = float(equity.iloc[0])
    end_val = float(equity.iloc[-1])
    n_days = (equity.index[-1] - equity.index[0]).days
    years = max(n_days / 365.25, 1e-9)
    cagr = (end_val / start_val) ** (1 / years) - 1 if start_val > 0 else 0.0
    max_dd, max_dd_days = _max_drawdown_and_duration(equity)
    daily_returns = equity.pct_change().fillna(0.0)

    completed = [t for t in trades if not t["is_open"]]
    wins = [t for t in completed if t["is_profitable"]]
    losses = [t for t in completed if not t["is_profitable"]]
    win_rate = (len(wins) / len(completed) * 100) if completed else 0.0
    avg_win = float(np.mean([t["profit_pct"] for t in wins])) if wins else 0.0
    avg_loss = float(np.mean([t["profit_pct"] for t in losses])) if losses else 0.0
    pl_ratio = abs(avg_win / avg_loss) if avg_loss else None

    cagr_pct = round(cagr * 100, 3)
    max_dd_pct = round(max_dd * 100, 3)

    return {
        "start_date": equity.index[0].strftime("%Y-%m-%d"),
        "end_date": equity.index[-1].strftime("%Y-%m-%d"),
        "cagr_pct": cagr_pct,
        "total_return_pct": round((end_val / start_val - 1) * 100, 3),
        "num_trades": len(completed),
        "win_rate_pct": round(win_rate, 2),
        "profit_loss_ratio": round(pl_ratio, 3) if pl_ratio is not None and np.isfinite(pl_ratio) else None,
        "max_drawdown_pct": max_dd_pct,
        "max_drawdown_days": max_dd_days,
        "calmar_ratio": compute_calmar_ratio(cagr_pct, max_dd_pct),
        "worst_day": compute_worst_day(daily_returns),
        **compute_consecutive_loss_stats(trades),
    }


def _check_divergence(in_kpis: dict, out_kpis: dict) -> tuple[bool, str | None]:
    if out_kpis["num_trades"] == 0:
        return True, "No completed trades in the out-of-sample period -- there's nothing yet to judge whether the edge holds up."

    if in_kpis["cagr_pct"] > 5 and out_kpis["cagr_pct"] < 0:
        return True, (
            f"In-sample looked strong ({in_kpis['cagr_pct']:.1f}% CAGR) but out-of-sample was negative "
            f"({out_kpis['cagr_pct']:.1f}% CAGR) -- treat the in-sample result as possibly overfit until "
            "this holds up on more untouched data."
        )

    if in_kpis["max_drawdown_pct"] < -1 and out_kpis["max_drawdown_pct"] < in_kpis["max_drawdown_pct"] * 1.5:
        return True, (
            f"Out-of-sample max drawdown ({out_kpis['max_drawdown_pct']:.1f}%) is notably worse than "
            f"in-sample ({in_kpis['max_drawdown_pct']:.1f}%) -- the pain you'd actually feel going forward "
            "may be understated by the in-sample number alone."
        )

    return False, None


def run_walk_forward(
    dataset: pd.DataFrame,
    split_date: str,
    initial_capital: float = 10_000.0,
    exit_config: ExitConfig | None = None,
    sizing_config: SizingConfig | None = None,
    ma_fast: int | None = None,
    ma_slow: int | None = None,
    fee_bps: float = 0.0,
) -> dict:
    kwargs = {}
    if ma_fast is not None:
        kwargs["ma_fast"] = ma_fast
    if ma_slow is not None:
        kwargs["ma_slow"] = ma_slow

    result = run_backtest(
        dataset,
        initial_capital=initial_capital,
        exit_config=exit_config,
        sizing_config=sizing_config,
        fee_bps=fee_bps,
        **kwargs,
    )

    equity = pd.Series({row["date"]: row["strategy_equity"] for row in result.equity_curve})
    equity.index = pd.to_datetime(equity.index)
    split_ts = pd.Timestamp(split_date)

    if split_ts <= equity.index[0] or split_ts >= equity.index[-1]:
        raise ValueError(
            f"split_date must fall strictly within the dataset's date range "
            f"({equity.index[0].strftime('%Y-%m-%d')} to {equity.index[-1].strftime('%Y-%m-%d')})"
        )

    in_sample_equity = equity.loc[:split_ts]
    out_sample_equity = equity.loc[split_ts:]

    if in_sample_equity.empty or out_sample_equity.empty:
        raise ValueError("split_date must fall strictly within the dataset's date range")

    in_trades = [t for t in result.trade_log if t["start_date"] <= split_date]
    out_trades = [t for t in result.trade_log if t["start_date"] > split_date]

    in_kpis = _build_period_kpis(_rebase_equity(in_sample_equity, initial_capital), in_trades)
    out_kpis = _build_period_kpis(_rebase_equity(out_sample_equity, initial_capital), out_trades)
    flag, flag_reason = _check_divergence(in_kpis, out_kpis)

    return {
        "split_date": split_date,
        "in_sample": in_kpis,
        "out_of_sample": out_kpis,
        "flag": flag,
        "flag_reason": flag_reason,
    }
