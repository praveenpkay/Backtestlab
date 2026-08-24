import pandas as pd
import pytest

from app import daily_log as daily_log_module
from app import config
from app.signals import compute_signal


@pytest.fixture
def fake_ndx_history(synthetic_dataset, monkeypatch):
    history = pd.DataFrame({"Close": synthetic_dataset["ndx"]})

    def _fake_get_price_history(ticker, force_refresh=False):
        assert ticker == config.INDEX_TICKER
        return history

    monkeypatch.setattr(daily_log_module, "get_price_history", _fake_get_price_history)
    return history


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.db")


def test_compute_latest_signal_matches_last_row(fake_ndx_history):
    result = daily_log_module.compute_latest_signal()
    expected_sig = compute_signal(fake_ndx_history["Close"]).iloc[-1]

    assert result["date"] == fake_ndx_history.index[-1].strftime("%Y-%m-%d")
    assert result["ndx_close"] == pytest.approx(float(expected_sig["close"]))
    assert result["target_weight"] == expected_sig["target_weight"]
    expected_symbol = {1.0: "TQQQ", -1.0: "SQQQ", 0.0: "CASH"}[expected_sig["target_weight"]]
    assert result["symbol"] == expected_symbol


def test_refresh_is_idempotent_for_same_day(fake_ndx_history, temp_db):
    row1 = daily_log_module.refresh_daily_log()
    row2 = daily_log_module.refresh_daily_log()

    rows = daily_log_module.get_daily_log()
    assert len(rows) == 1
    assert row1["date"] == row2["date"]
    assert rows[0]["date"] == row1["date"]
    assert rows[0]["target_weight"] == row1["target_weight"]


def test_get_daily_log_respects_limit(fake_ndx_history, temp_db):
    from app.db import get_connection

    with get_connection() as conn:
        for i, date in enumerate(pd.bdate_range("2024-01-01", periods=5)):
            conn.execute(
                """
                INSERT INTO daily_log (date, ndx_close, ma_fast, ma_slow, target_weight, symbol, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (date.strftime("%Y-%m-%d"), 100.0 + i, None, None, 1.0, "TQQQ", "2024-01-01T00:00:00"),
            )

    rows = daily_log_module.get_daily_log(limit=2)
    assert len(rows) == 2
    assert rows[0]["date"] < rows[1]["date"]
    assert rows[-1]["date"] == "2024-01-05"
