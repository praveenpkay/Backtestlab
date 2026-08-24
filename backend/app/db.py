"""Tiny SQLite wrapper for the daily signal log -- the persisted record of
what the strategy's dial said on each day, independent of any single
backtest run."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_log (
    date TEXT PRIMARY KEY,
    ndx_close REAL NOT NULL,
    ma_fast REAL,
    ma_slow REAL,
    target_weight REAL NOT NULL,
    symbol TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);
"""


@contextmanager
def get_connection():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()
