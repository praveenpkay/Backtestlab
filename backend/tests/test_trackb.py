import pandas as pd

from app.trackb import compute_track_b_analysis


def test_track_b_is_always_labeled_signal_only(synthetic_dataset):
    result = compute_track_b_analysis(synthetic_dataset["ndx"], "^NDX")
    assert result["signal_only"] is True
    assert "not simulated dollar returns" in result["disclaimer"].lower() or "not" in result["disclaimer"].lower()
    assert result["ticker_used"] == "^NDX"


def test_track_b_series_has_no_dollar_fields(synthetic_dataset):
    result = compute_track_b_analysis(synthetic_dataset["ndx"], "^NDX")
    for row in result["series"]:
        assert set(row) == {"date", "close", "ma_fast", "ma_slow", "target_weight"}
        assert "equity" not in row
        assert "profit" not in row


def test_track_b_regime_percentages_sum_to_100(synthetic_dataset):
    result = compute_track_b_analysis(synthetic_dataset["ndx"], "^NDX")
    stats = result["regime_stats"]
    total = stats["pct_days_long"] + stats["pct_days_short"] + stats["pct_days_cash"]
    assert abs(total - 100.0) < 0.01


def test_track_b_streak_stats_hand_computed():
    idx = pd.bdate_range("2020-01-01", periods=10)
    close = pd.Series(range(10), index=idx).astype(float)
    weight = pd.Series([1, 1, 1, 0, 0, -1, -1, -1, -1, 1], index=idx).astype(float)

    from app.trackb import _streak_stats

    long_count, long_longest = _streak_stats(weight, 1.0)
    short_count, short_longest = _streak_stats(weight, -1.0)
    cash_count, cash_longest = _streak_stats(weight, 0.0)

    assert (long_count, long_longest) == (2, 3)  # [1,1,1] then a lone [1] at the end
    assert (short_count, short_longest) == (1, 4)
    assert (cash_count, cash_longest) == (1, 2)


def test_track_b_regime_changes_count_matches_manual(synthetic_dataset):
    from app.signals import compute_signal

    result = compute_track_b_analysis(synthetic_dataset["ndx"], "^NDX")
    weight = compute_signal(synthetic_dataset["ndx"])["target_weight"]
    expected = int((weight != weight.shift()).sum() - 1)
    assert result["regime_stats"]["num_regime_changes"] == expected
