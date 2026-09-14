"""Extra KPIs for scenario comparison, beyond what backtest.py's summary
already covers: the full list of drawdown episodes (depth + length, not
just the single worst one), worst single day, worst month, and how bad
consecutive losing trades have been. These are what "is the edge real or
fragile" actually gets judged on.
"""

from __future__ import annotations

import pandas as pd


def compute_drawdown_episodes(equity: pd.Series) -> list[dict]:
    """Every underwater period: from the prior peak, to the trough, to
    recovery (a new equity high) -- or, if it never recovers within the
    tested window, marked is_ongoing with no recovery_date."""
    if equity.empty:
        return []

    running_max = equity.cummax()
    episodes: list[dict] = []
    in_episode = False
    peak_date = peak_value = None
    trough_date = trough_value = None

    for date, value in equity.items():
        at_new_high = value >= running_max.loc[date]
        if at_new_high:
            if in_episode:
                episodes.append(
                    {
                        "peak_date": peak_date.strftime("%Y-%m-%d"),
                        "trough_date": trough_date.strftime("%Y-%m-%d"),
                        "recovery_date": date.strftime("%Y-%m-%d"),
                        "depth_pct": round((trough_value / peak_value - 1) * 100, 3),
                        "length_days": (date - peak_date).days,
                        "is_ongoing": False,
                    }
                )
                in_episode = False
            peak_date, peak_value = date, value
        else:
            if not in_episode:
                in_episode = True
                trough_date, trough_value = date, value
            elif value < trough_value:
                trough_date, trough_value = date, value

    if in_episode:
        last_date = equity.index[-1]
        episodes.append(
            {
                "peak_date": peak_date.strftime("%Y-%m-%d"),
                "trough_date": trough_date.strftime("%Y-%m-%d"),
                "recovery_date": None,
                "depth_pct": round((trough_value / peak_value - 1) * 100, 3),
                "length_days": (last_date - peak_date).days,
                "is_ongoing": True,
            }
        )

    return episodes


def compute_worst_day(daily_returns: pd.Series) -> dict | None:
    if daily_returns.empty:
        return None
    idx = daily_returns.idxmin()
    return {"date": idx.strftime("%Y-%m-%d"), "return_pct": round(float(daily_returns.loc[idx]) * 100, 3)}


def compute_worst_month(monthly_returns: list[dict]) -> dict | None:
    if not monthly_returns:
        return None
    worst = min(monthly_returns, key=lambda r: r["return_pct"])
    return {"year": worst["year"], "month": worst["month"], "return_pct": worst["return_pct"]}


def compute_consecutive_loss_stats(trade_log: list[dict]) -> dict:
    """Longest run of back-to-back losing trades, and how much that streak
    cost compounded (not just summed) -- "how bad have consecutive losing
    stretches been," per the spec."""
    completed = [t for t in trade_log if not t["is_open"]]

    best_len = 0
    best_compounded = 0.0
    cur_len = 0
    cur_compounded = 1.0

    for t in completed:
        if not t["is_profitable"]:
            cur_len += 1
            cur_compounded *= 1 + t["profit_pct"] / 100
        else:
            if cur_len > best_len:
                best_len, best_compounded = cur_len, cur_compounded - 1
            cur_len, cur_compounded = 0, 1.0

    if cur_len > best_len:
        best_len, best_compounded = cur_len, cur_compounded - 1

    return {
        "max_consecutive_losses": best_len,
        "worst_losing_streak_pct": round(best_compounded * 100, 3) if best_len else 0.0,
    }


def compute_calmar_ratio(cagr_pct: float, max_drawdown_pct: float) -> float | None:
    """CAGR / |max drawdown| -- a simple return-per-unit-of-pain ratio, used
    for the "beats buy-and-hold on a risk-adjusted basis" comparison."""
    if max_drawdown_pct == 0:
        return None
    return round(cagr_pct / abs(max_drawdown_pct), 3)
