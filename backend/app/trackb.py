"""Track B: long-history SIGNAL-ONLY stress test.

Real ^NDX (or QQQ proxy) index data goes back much further than TQQQ/SQQQ
have existed. This runs the Job 1 signal on that long history to see how it
would have behaved through crash regimes the 2010+ data doesn't contain
(2000 dot-com, 2008) -- but reports it strictly as signal direction/regime
behavior, NEVER as simulated dollar returns. Turning pre-2010 index moves
into fake leveraged-ETF dollar returns (naive daily x3 compounding) is
exactly the trap the original spec calls out: real leveraged ETFs have
costs and daily-reset decay that a naive multiply-by-3 ignores, worst
precisely in the volatile crashes this is meant to test.
"""

from __future__ import annotations

import pandas as pd

from .signals import compute_signal


def _streak_stats(weight: pd.Series, value: float) -> tuple[int, int]:
    """Returns (count of streaks, longest streak length) for a given weight value."""
    is_value = weight == value
    if not is_value.any():
        return 0, 0
    group_id = (weight != weight.shift()).cumsum()
    streak_lengths = weight[is_value].groupby(group_id[is_value]).size()
    return int(len(streak_lengths)), int(streak_lengths.max())


def compute_track_b_analysis(close: pd.Series, ticker_used: str) -> dict:
    sig = compute_signal(close)
    weight = sig["target_weight"]
    total_days = len(weight)

    num_regime_changes = int((weight != weight.shift()).sum() - 1) if total_days else 0
    long_count, long_longest = _streak_stats(weight, 1.0)
    short_count, short_longest = _streak_stats(weight, -1.0)
    cash_count, cash_longest = _streak_stats(weight, 0.0)

    series_rows = [
        {
            "date": d.strftime("%Y-%m-%d"),
            "close": float(c),
            "ma_fast": None if pd.isna(mf) else float(mf),
            "ma_slow": None if pd.isna(ms) else float(ms),
            "target_weight": float(w),
        }
        for d, c, mf, ms, w in zip(
            sig.index, sig["close"], sig["ma_fast"], sig["ma_slow"], weight
        )
    ]

    return {
        "signal_only": True,
        "disclaimer": (
            "Signal accuracy / direction only -- NOT simulated dollar returns. "
            "Real leveraged-ETF costs and daily-reset decay are not modeled here."
        ),
        "ticker_used": ticker_used,
        "start_date": sig.index[0].strftime("%Y-%m-%d") if total_days else None,
        "end_date": sig.index[-1].strftime("%Y-%m-%d") if total_days else None,
        "series": series_rows,
        "regime_stats": {
            "pct_days_long": round(float((weight == 1.0).mean()) * 100, 2) if total_days else 0.0,
            "pct_days_short": round(float((weight == -1.0).mean()) * 100, 2) if total_days else 0.0,
            "pct_days_cash": round(float((weight == 0.0).mean()) * 100, 2) if total_days else 0.0,
            "num_regime_changes": num_regime_changes,
            "long_streaks": {"count": long_count, "longest_days": long_longest},
            "short_streaks": {"count": short_count, "longest_days": short_longest},
            "cash_streaks": {"count": cash_count, "longest_days": cash_longest},
        },
    }
