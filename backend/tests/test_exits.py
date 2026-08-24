import pandas as pd
import pytest

from app.exits import ExitConfig, apply_exit_overlay
from app.signals import compute_signal


def _frame(index, ndx, tqqq, sqqq):
    return pd.DataFrame({"ndx": ndx, "tqqq": tqqq, "sqqq": sqqq}, index=index)


def _signal_frame(index, target_weight, ndx_close, ma_fast):
    return pd.DataFrame({"close": ndx_close, "ma_fast": ma_fast, "target_weight": target_weight}, index=index)


def test_stop_loss_exits_and_blocks_reentry_until_signal_changes():
    idx = pd.bdate_range("2020-01-01", periods=10)
    dataset = _frame(
        idx,
        ndx=[100] * 10,
        tqqq=[100, 100, 85, 80, 80, 80, 80, 80, 80, 80],
        sqqq=[50] * 10,
    )
    target_weight = [1, 1, 1, 1, -1, -1, -1, -1, -1, -1]
    signal_df = _signal_frame(idx, target_weight, dataset["ndx"], ma_fast=[100] * 10)
    cfg = ExitConfig(
        enable_stop_loss=True,
        stop_loss_pct=0.12,
        enable_fast_trend_break=False,
        enable_mean_reversion_exit=False,
    )

    result = apply_exit_overlay(dataset, signal_df, cfg)

    assert list(result.effective_weight) == [1, 1, 0, 0, -1, -1, -1, -1, -1, -1]
    assert result.exit_reason.iloc[2] == "stop_loss"
    assert result.exit_reason.drop(result.exit_reason.index[2]).isna().all()


def test_fast_trend_break_exits_before_job1_signal_flips():
    idx = pd.bdate_range("2020-01-01", periods=6)
    ndx_close = [100, 101, 102, 90, 91, 92]
    dataset = _frame(idx, ndx=ndx_close, tqqq=[100] * 6, sqqq=[50] * 6)
    # Job 1 signal (target_weight) never flips in this window -- only the
    # faster overlay should be able to get us out.
    signal_df = _signal_frame(idx, target_weight=[1] * 6, ndx_close=ndx_close, ma_fast=[None] * 6)
    cfg = ExitConfig(
        enable_stop_loss=False,
        enable_fast_trend_break=True,
        fast_ma_period=3,
        enable_mean_reversion_exit=False,
    )

    result = apply_exit_overlay(dataset, signal_df, cfg)

    assert list(result.effective_weight) == [1, 1, 1, 0, 0, 0]
    assert result.exit_reason.iloc[3] == "fast_trend_break"


def test_mean_reversion_extension_exits_when_overstretched():
    idx = pd.bdate_range("2020-01-01", periods=6)
    ndx_close = [100, 110, 115, 125, 130, 130]
    dataset = _frame(idx, ndx=ndx_close, tqqq=[100] * 6, sqqq=[50] * 6)
    signal_df = _signal_frame(idx, target_weight=[1] * 6, ndx_close=ndx_close, ma_fast=[100] * 6)
    cfg = ExitConfig(
        enable_stop_loss=False,
        enable_fast_trend_break=False,
        enable_mean_reversion_exit=True,
        extension_pct=0.20,
    )

    result = apply_exit_overlay(dataset, signal_df, cfg)

    assert list(result.effective_weight) == [1, 1, 1, 0, 0, 0]
    assert result.exit_reason.iloc[3] == "mean_reversion_extension"


def test_block_clears_once_base_signal_passes_through_cash():
    idx = pd.bdate_range("2020-01-01", periods=6)
    dataset = _frame(idx, ndx=[100] * 6, tqqq=[100, 80, 80, 80, 80, 80], sqqq=[50] * 6)
    # day1: stop out of TQQQ. day2-3: Job1 still says +1 -> stays blocked.
    # day4: Job1 goes to cash -> clears the block. day5: Job1 says +1 again -> re-enters.
    target_weight = [1, 1, 1, 1, 0, 1]
    signal_df = _signal_frame(idx, target_weight, dataset["ndx"], ma_fast=[100] * 6)
    cfg = ExitConfig(enable_stop_loss=True, stop_loss_pct=0.12, enable_fast_trend_break=False, enable_mean_reversion_exit=False)

    result = apply_exit_overlay(dataset, signal_df, cfg)

    assert list(result.effective_weight) == [1, 0, 0, 0, 0, 1]
    assert result.exit_reason.iloc[1] == "stop_loss"


def test_all_rules_disabled_reproduces_job1_signal_exactly(synthetic_dataset):
    signal_df = compute_signal(synthetic_dataset["ndx"])
    cfg = ExitConfig(enable_stop_loss=False, enable_fast_trend_break=False, enable_mean_reversion_exit=False)

    result = apply_exit_overlay(synthetic_dataset, signal_df, cfg)

    pd.testing.assert_series_equal(
        result.effective_weight, signal_df["target_weight"], check_names=False
    )

    # Every "signal_flip" exit reason should correspond exactly to a day where
    # target_weight changed away from a nonzero value -- nothing more, nothing less.
    weight = signal_df["target_weight"]
    prev_weight = weight.shift(1)
    expected_exit_days = (prev_weight.fillna(0) != 0) & (weight != prev_weight)
    pd.testing.assert_series_equal(
        result.exit_reason.notna(), expected_exit_days, check_names=False
    )
    assert set(result.exit_reason.dropna().unique()) == {"signal_flip"}
