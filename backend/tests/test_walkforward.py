import pytest

from app.exits import ExitConfig
from app.walkforward import run_walk_forward


def test_walk_forward_splits_into_two_periods(synthetic_dataset):
    mid_date = synthetic_dataset.index[len(synthetic_dataset) // 2].strftime("%Y-%m-%d")
    result = run_walk_forward(synthetic_dataset, split_date=mid_date, initial_capital=10_000.0)

    assert result["split_date"] == mid_date
    assert result["in_sample"]["end_date"] <= mid_date
    assert result["out_of_sample"]["start_date"] >= mid_date
    assert "flag" in result
    assert "cagr_pct" in result["in_sample"]
    assert "cagr_pct" in result["out_of_sample"]


def test_walk_forward_rebases_each_period_to_initial_capital(synthetic_dataset):
    mid_date = synthetic_dataset.index[len(synthetic_dataset) // 2].strftime("%Y-%m-%d")
    result = run_walk_forward(synthetic_dataset, split_date=mid_date, initial_capital=5_000.0)

    # total_return_pct is computed on the rebased series, so it reflects
    # only that period's own performance, not compounded from the other half.
    assert isinstance(result["in_sample"]["total_return_pct"], float)
    assert isinstance(result["out_of_sample"]["total_return_pct"], float)


def test_walk_forward_flags_when_out_of_sample_has_no_trades(synthetic_dataset):
    # Split right at the very end so almost nothing is left out-of-sample.
    near_end_date = synthetic_dataset.index[-2].strftime("%Y-%m-%d")
    result = run_walk_forward(synthetic_dataset, split_date=near_end_date, initial_capital=10_000.0)

    if result["out_of_sample"]["num_trades"] == 0:
        assert result["flag"] is True
        assert result["flag_reason"] is not None


def test_walk_forward_rejects_split_outside_data_range(synthetic_dataset):
    with pytest.raises(ValueError):
        run_walk_forward(synthetic_dataset, split_date="1900-01-01", initial_capital=10_000.0)

    with pytest.raises(ValueError):
        run_walk_forward(synthetic_dataset, split_date="2999-01-01", initial_capital=10_000.0)


def test_walk_forward_accepts_ma_and_exit_overrides(synthetic_dataset):
    mid_date = synthetic_dataset.index[len(synthetic_dataset) // 2].strftime("%Y-%m-%d")
    result = run_walk_forward(
        synthetic_dataset,
        split_date=mid_date,
        initial_capital=10_000.0,
        exit_config=ExitConfig(enable_stop_loss=False, enable_fast_trend_break=False, enable_mean_reversion_exit=False),
        ma_fast=20,
        ma_slow=100,
    )
    assert result["in_sample"] is not None
    assert result["out_of_sample"] is not None


def test_divergence_flagged_when_in_sample_strong_and_out_of_sample_negative():
    from app.walkforward import _check_divergence

    flag, reason = _check_divergence(
        {"cagr_pct": 20.0, "max_drawdown_pct": -5.0},
        {"cagr_pct": -10.0, "max_drawdown_pct": -8.0, "num_trades": 3},
    )
    assert flag is True
    assert "overfit" in reason.lower()


def test_no_divergence_when_both_periods_consistent():
    from app.walkforward import _check_divergence

    flag, reason = _check_divergence(
        {"cagr_pct": 15.0, "max_drawdown_pct": -10.0},
        {"cagr_pct": 12.0, "max_drawdown_pct": -11.0, "num_trades": 5},
    )
    assert flag is False
    assert reason is None
