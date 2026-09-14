"""Computes and persists the strategy's daily dial -- the "how am I doing"
tracker. Independent of the Track A backtest: this just records, once per
day, what the live signal said, so a real history accumulates over time
regardless of how backtest parameters get tweaked later.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from . import config
from .data import get_index_history
from .db import get_connection
from .signals import compute_signal


def _symbol_for_weight(weight: float) -> str:
    if weight > 0:
        return config.LONG_TICKER
    if weight < 0:
        return config.SHORT_TICKER
    return "CASH"


def compute_latest_signal() -> dict:
    """Computes today's (or the most recent trading day's) target weight
    from the live signal history. Does not persist anything."""
    ndx, signal_ticker = get_index_history()
    sig = compute_signal(ndx)
    last = sig.iloc[-1]
    date = sig.index[-1]
    weight = float(last["target_weight"])
    ma_fast = None if pd.isna(last["ma_fast"]) else float(last["ma_fast"])
    ma_slow = None if pd.isna(last["ma_slow"]) else float(last["ma_slow"])

    return {
        "date": date.strftime("%Y-%m-%d"),
        "ndx_close": float(last["close"]),
        "ma_fast": ma_fast,
        "ma_slow": ma_slow,
        "target_weight": weight,
        "symbol": _symbol_for_weight(weight),
        "signal_ticker": signal_ticker,
        "rationale": None,
        "next_exit_trigger": None,
    }


def refresh_daily_log() -> dict:
    """Computes the latest signal and upserts it into the daily log,
    keyed by trading date (safe to call more than once on the same day)."""
    row = compute_latest_signal()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO daily_log (
                date, ndx_close, ma_fast, ma_slow, target_weight, symbol,
                signal_ticker, rationale, next_exit_trigger, recorded_at
            )
            VALUES (
                :date, :ndx_close, :ma_fast, :ma_slow, :target_weight, :symbol,
                :signal_ticker, :rationale, :next_exit_trigger, :recorded_at
            )
            ON CONFLICT(date) DO UPDATE SET
                ndx_close = excluded.ndx_close,
                ma_fast = excluded.ma_fast,
                ma_slow = excluded.ma_slow,
                target_weight = excluded.target_weight,
                symbol = excluded.symbol,
                signal_ticker = excluded.signal_ticker,
                rationale = excluded.rationale,
                next_exit_trigger = excluded.next_exit_trigger,
                recorded_at = excluded.recorded_at
            """,
            {**row, "recorded_at": datetime.now(timezone.utc).isoformat()},
        )
    return row


def get_daily_log(limit: int | None = None) -> list[dict]:
    query = (
        "SELECT date, ndx_close, ma_fast, ma_slow, target_weight, symbol, "
        "signal_ticker, rationale, next_exit_trigger FROM daily_log ORDER BY date ASC"
    )
    with get_connection() as conn:
        rows = conn.execute(query).fetchall()
    rows = [dict(r) for r in rows]
    if limit:
        rows = rows[-limit:]
    return rows
