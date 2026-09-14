"""Scenario engine: run several named parameter combinations against the
same real price history in one go, plus buy-and-hold TQQQ/QQQ benchmark
rows, so you can compare -- not just run one backtest and hope.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from . import config
from .backtest import _max_drawdown_and_duration, _monthly_returns, run_backtest
from .exits import ExitConfig
from .kpis import (
    compute_calmar_ratio,
    compute_consecutive_loss_stats,
    compute_drawdown_episodes,
    compute_worst_day,
    compute_worst_month,
)
from .readout import generate_readout
from .sizing import SizingConfig


@dataclass
class Scenario:
    name: str
    ma_fast: int = config.MA_FAST
    ma_slow: int = config.MA_SLOW
    exit_config: ExitConfig = field(default_factory=ExitConfig)
    sizing_config: SizingConfig = field(default_factory=lambda: SizingConfig(enabled=False))


def default_scenarios() -> list[Scenario]:
    """A handful of sensible presets covering the main on/off combinations
    -- not fitted to the data, just the natural comparison points."""
    return [
        Scenario(
            "Job 1 only (50/250)",
            exit_config=ExitConfig(
                enable_stop_loss=False, enable_fast_trend_break=False, enable_mean_reversion_exit=False
            ),
        ),
        Scenario("Job 1 + Job 3 (50/250)"),
        Scenario("Job 1 + Job 3 + Job 2 (50/250)", sizing_config=SizingConfig(enabled=True)),
        Scenario("Faster entry (20/100)", ma_fast=20, ma_slow=100),
    ]


def _augment_kpis(summary: dict, equity_curve_rows: list[dict], trade_log: list[dict]) -> dict:
    equity = pd.Series(
        {row["date"]: row["strategy_equity"] for row in equity_curve_rows},
    )
    equity.index = pd.to_datetime(equity.index)
    daily_returns = equity.pct_change().fillna(0.0)

    episodes = compute_drawdown_episodes(equity)
    loss_stats = compute_consecutive_loss_stats(trade_log)

    return {
        **summary,
        "calmar_ratio": compute_calmar_ratio(summary["cagr_pct"], summary["max_drawdown_pct"]),
        "drawdown_episodes": episodes,
        "num_drawdowns_over_20pct": sum(1 for e in episodes if e["depth_pct"] <= -20),
        "worst_day": compute_worst_day(daily_returns),
        "worst_month": compute_worst_month([]),  # filled in by caller with real monthly rows
        **loss_stats,
    }


def run_scenario(dataset: pd.DataFrame, scenario: Scenario, initial_capital: float) -> dict:
    result = run_backtest(
        dataset,
        initial_capital=initial_capital,
        exit_config=scenario.exit_config,
        sizing_config=scenario.sizing_config,
        ma_fast=scenario.ma_fast,
        ma_slow=scenario.ma_slow,
    )
    kpis = _augment_kpis(result.summary, result.equity_curve, result.trade_log)
    kpis["worst_month"] = compute_worst_month(result.monthly_returns)

    return {
        "name": scenario.name,
        "kind": "strategy",
        "kpis": kpis,
        "equity_curve": result.equity_curve,
        "readout": generate_readout(scenario.name, kpis),
    }


def compute_buy_and_hold(dataset: pd.DataFrame, price_col: str, name: str, initial_capital: float) -> dict:
    prices = dataset[price_col]
    daily_returns = prices.pct_change().fillna(0.0)
    equity = initial_capital * (1 + daily_returns).cumprod()

    start_val = float(equity.iloc[0])
    end_val = float(equity.iloc[-1])
    n_days = (equity.index[-1] - equity.index[0]).days
    years = max(n_days / 365.25, 1e-9)
    cagr = (end_val / start_val) ** (1 / years) - 1 if start_val > 0 else 0.0

    max_dd, max_dd_days = _max_drawdown_and_duration(equity)
    monthly = _monthly_returns(equity)
    episodes = compute_drawdown_episodes(equity)

    kpis = {
        "start_date": equity.index[0].strftime("%Y-%m-%d"),
        "end_date": equity.index[-1].strftime("%Y-%m-%d"),
        "initial_capital": round(start_val, 2),
        "final_equity": round(end_val, 2),
        "cagr_pct": round(cagr * 100, 3),
        "total_return_pct": round((end_val / start_val - 1) * 100, 3),
        "num_trades": 1,
        "win_rate_pct": 100.0 if end_val > start_val else 0.0,
        "profit_loss_ratio": None,
        "max_drawdown_pct": round(max_dd * 100, 3),
        "max_drawdown_days": max_dd_days,
        "exit_reason_breakdown": {},
        "calmar_ratio": compute_calmar_ratio(round(cagr * 100, 3), round(max_dd * 100, 3)),
        "drawdown_episodes": episodes,
        "num_drawdowns_over_20pct": sum(1 for e in episodes if e["depth_pct"] <= -20),
        "worst_day": compute_worst_day(daily_returns),
        "worst_month": compute_worst_month(monthly),
        "max_consecutive_losses": 0,
        "worst_losing_streak_pct": 0.0,
    }

    equity_curve_rows = [
        {"date": d.strftime("%Y-%m-%d"), "strategy_equity": round(float(v), 2), "benchmark_equity": round(float(v), 2), "target_weight": 1.0}
        for d, v in equity.items()
    ]

    return {
        "name": name,
        "kind": "benchmark",
        "kpis": kpis,
        "equity_curve": equity_curve_rows,
        "readout": generate_readout(name, kpis),
    }


def run_scenarios(
    dataset: pd.DataFrame, scenarios: list[Scenario] | None, initial_capital: float = 10_000.0
) -> list[dict]:
    scenarios = scenarios or default_scenarios()
    rows = [run_scenario(dataset, s, initial_capital) for s in scenarios]

    bh_tqqq = compute_buy_and_hold(dataset, "tqqq", "Buy & hold TQQQ", initial_capital)
    bh_qqq = compute_buy_and_hold(dataset, "qqq", "Buy & hold QQQ", initial_capital)
    benchmarks = {bh_tqqq["name"]: bh_tqqq["kpis"], bh_qqq["name"]: bh_qqq["kpis"]}

    # Re-generate strategy readouts now that benchmark KPIs are available for comparison.
    for row in rows:
        row["readout"] = generate_readout(row["name"], row["kpis"], benchmarks=benchmarks)

    return rows + [bh_tqqq, bh_qqq]
