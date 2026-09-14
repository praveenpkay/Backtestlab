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

# Columns added after the initial release. SQLite has no "ADD COLUMN IF NOT
# EXISTS", so we just try each and ignore "duplicate column" -- cheap and
# safe for a single-table personal-tool database.
_MIGRATIONS = [
    "ALTER TABLE daily_log ADD COLUMN signal_ticker TEXT",
    "ALTER TABLE daily_log ADD COLUMN rationale TEXT",
    "ALTER TABLE daily_log ADD COLUMN next_exit_trigger TEXT",
]


@contextmanager
def get_connection():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(_SCHEMA)
        for migration in _MIGRATIONS:
            try:
                conn.execute(migration)
            except sqlite3.OperationalError:
                pass  # column already exists
        yield conn
        conn.commit()
    finally:
        conn.close()
