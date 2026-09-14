import pandas as pd
import pytest

from app.kpis import (
    compute_calmar_ratio,
    compute_consecutive_loss_stats,
    compute_drawdown_episodes,
    compute_worst_day,
    compute_worst_month,
)


def test_drawdown_episodes_hand_computed():
    idx = pd.bdate_range("2020-01-01", periods=8)
    # peak 100 -> trough 80 (day3) -> recovers to 105 (day5) -> dips to 95 (day6, ongoing)
    equity = pd.Series([100, 90, 80, 90, 105, 95, 96, 97], index=idx)

    episodes = compute_drawdown_episodes(equity)

    assert len(episodes) == 2
    first = episodes[0]
    assert first["peak_date"] == idx[0].strftime("%Y-%m-%d")
    assert first["trough_date"] == idx[2].strftime("%Y-%m-%d")
    assert first["recovery_date"] == idx[4].strftime("%Y-%m-%d")
    assert first["depth_pct"] == pytest.approx(-20.0)
    assert first["is_ongoing"] is False

    second = episodes[1]
    assert second["peak_date"] == idx[4].strftime("%Y-%m-%d")
    assert second["is_ongoing"] is True
    assert second["recovery_date"] is None


def test_drawdown_episodes_empty_series():
    assert compute_drawdown_episodes(pd.Series(dtype=float)) == []


def test_drawdown_episodes_no_drawdown_at_all():
    idx = pd.bdate_range("2020-01-01", periods=3)
    equity = pd.Series([100, 110, 120], index=idx)
    assert compute_drawdown_episodes(equity) == []


def test_worst_day_picks_minimum_return():
    idx = pd.bdate_range("2020-01-01", periods=4)
    returns = pd.Series([0.01, -0.05, 0.02, -0.10], index=idx)
    result = compute_worst_day(returns)
    assert result["date"] == idx[3].strftime("%Y-%m-%d")
    assert result["return_pct"] == pytest.approx(-10.0)


def test_worst_day_empty_returns_none():
    assert compute_worst_day(pd.Series(dtype=float)) is None


def test_worst_month_picks_minimum():
    monthly = [
        {"year": 2020, "month": 1, "return_pct": 5.0},
        {"year": 2020, "month": 2, "return_pct": -12.0},
        {"year": 2020, "month": 3, "return_pct": 3.0},
    ]
    assert compute_worst_month(monthly) == {"year": 2020, "month": 2, "return_pct": -12.0}


def test_worst_month_empty_returns_none():
    assert compute_worst_month([]) is None


def test_consecutive_loss_stats_hand_computed():
    trades = [
        {"is_open": False, "is_profitable": True, "profit_pct": 5.0},
        {"is_open": False, "is_profitable": False, "profit_pct": -10.0},
        {"is_open": False, "is_profitable": False, "profit_pct": -5.0},
        {"is_open": False, "is_profitable": False, "profit_pct": -8.0},
        {"is_open": False, "is_profitable": True, "profit_pct": 2.0},
        {"is_open": True, "is_profitable": False, "profit_pct": -50.0},  # open, excluded
    ]
    result = compute_consecutive_loss_stats(trades)
    assert result["max_consecutive_losses"] == 3
    expected = ((1 - 0.10) * (1 - 0.05) * (1 - 0.08) - 1) * 100
    assert result["worst_losing_streak_pct"] == pytest.approx(expected, abs=0.01)


def test_consecutive_loss_stats_no_losses():
    trades = [{"is_open": False, "is_profitable": True, "profit_pct": 5.0}]
    result = compute_consecutive_loss_stats(trades)
    assert result == {"max_consecutive_losses": 0, "worst_losing_streak_pct": 0.0}


def test_calmar_ratio_basic():
    assert compute_calmar_ratio(20.0, -10.0) == pytest.approx(2.0)


def test_calmar_ratio_zero_drawdown_is_none():
    assert compute_calmar_ratio(20.0, 0.0) is None
