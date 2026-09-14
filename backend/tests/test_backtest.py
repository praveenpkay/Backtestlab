import math

import pytest

from app.backtest import run_backtest
from app.exits import ExitConfig
from app.signals import compute_signal
from app.sizing import SizingConfig


def test_equity_curve_matches_naive_day_by_day_reimplementation(synthetic_dataset):
    """Independent, non-vectorized reimplementation of 'apply yesterday's
    signal to today's return' -- catches lookahead bugs and asset-selection
    mistakes in the vectorized backtest engine."""
    result = run_backtest(synthetic_dataset, initial_capital=10_000.0)
    weights = compute_signal(synthetic_dataset["ndx"])["target_weight"]

    capital = 10_000.0
    expected = [capital]
    prev_weight = weights.iloc[0]
    for i in range(1, len(synthetic_dataset)):
        if prev_weight > 0:
            ret = synthetic_dataset["tqqq"].iloc[i] / synthetic_dataset["tqqq"].iloc[i - 1] - 1
        elif prev_weight < 0:
            ret = synthetic_dataset["sqqq"].iloc[i] / synthetic_dataset["sqqq"].iloc[i - 1] - 1
        else:
            ret = 0.0
        capital *= 1 + ret
        expected.append(capital)
        prev_weight = weights.iloc[i]

    actual = [row["strategy_equity"] for row in result.equity_curve]
    assert len(actual) == len(expected)
    for e, a in zip(expected, actual):
        assert math.isclose(e, a, rel_tol=1e-6, abs_tol=0.05)


def test_equity_curve_starts_at_initial_capital(synthetic_dataset):
    result = run_backtest(synthetic_dataset, initial_capital=12_345.0)
    assert result.equity_curve[0]["strategy_equity"] == 12345.0
    assert result.equity_curve[0]["benchmark_equity"] == 12345.0


def test_trade_log_prices_match_raw_series(synthetic_dataset):
    result = run_backtest(synthetic_dataset)
    price_lookup = {
        "TQQQ": synthetic_dataset["tqqq"],
        "SQQQ": synthetic_dataset["sqqq"],
    }
    for trade in result.trade_log:
        series = price_lookup[trade["symbol"]]
        buy = series.loc[trade["start_date"]]
        sell = series.loc[trade["end_date"]]
        assert math.isclose(buy, trade["buy_price"], rel_tol=1e-4, abs_tol=1e-4)
        assert math.isclose(sell, trade["sell_price"], rel_tol=1e-4, abs_tol=1e-4)

        expected_profit = trade["share_size"] * (sell - buy)
        assert math.isclose(expected_profit, trade["profit"], abs_tol=0.05)
        assert trade["is_profitable"] == (trade["profit"] > 0)
        assert trade["is_short"] == (trade["symbol"] == "SQQQ")


def test_trades_are_chronological_and_non_overlapping(synthetic_dataset):
    result = run_backtest(synthetic_dataset)
    trades = result.trade_log
    for a, b in zip(trades, trades[1:]):
        assert a["end_date"] <= b["start_date"]


def test_drawdown_is_never_positive(synthetic_dataset):
    result = run_backtest(synthetic_dataset)
    for row in result.drawdown:
        assert row["drawdown_pct"] <= 1e-9


def test_summary_max_drawdown_matches_series_min(synthetic_dataset):
    result = run_backtest(synthetic_dataset)
    series_min = min(row["drawdown_pct"] for row in result.drawdown)
    assert math.isclose(series_min, result.summary["max_drawdown_pct"], abs_tol=1e-6)


def test_summary_trade_count_matches_completed_trades(synthetic_dataset):
    result = run_backtest(synthetic_dataset)
    completed = [t for t in result.trade_log if not t["is_open"]]
    assert result.summary["num_trades"] == len(completed)


def test_monthly_returns_cover_dataset_span(synthetic_dataset):
    result = run_backtest(synthetic_dataset)
    periods = {(row["year"], row["month"]) for row in result.monthly_returns}
    expected_periods = {(d.year, d.month) for d in synthetic_dataset.index}
    assert periods == expected_periods


def test_exit_overlay_tags_every_completed_trade_with_a_reason(synthetic_dataset):
    result = run_backtest(synthetic_dataset, exit_config=ExitConfig())

    completed = [t for t in result.trade_log if not t["is_open"]]
    open_trades = [t for t in result.trade_log if t["is_open"]]

    assert all(t["exit_reason"] is not None for t in completed)
    assert all(t["exit_reason"] is None for t in open_trades)
    assert set(result.summary["exit_reason_breakdown"]).issubset(
        {"signal_flip", "stop_loss", "fast_trend_break", "mean_reversion_extension"}
    )
    assert sum(result.summary["exit_reason_breakdown"].values()) == result.summary["num_trades"]


def test_exit_overlay_defaults_to_job1_only_when_omitted(synthetic_dataset):
    with_default = run_backtest(synthetic_dataset)
    explicit_no_overlay = run_backtest(
        synthetic_dataset,
        exit_config=ExitConfig(
            enable_stop_loss=False, enable_fast_trend_break=False, enable_mean_reversion_exit=False
        ),
    )
    assert with_default.equity_curve == explicit_no_overlay.equity_curve
    assert with_default.trade_log == explicit_no_overlay.trade_log


def test_sizing_disabled_by_default_matches_full_size(synthetic_dataset):
    no_sizing = run_backtest(synthetic_dataset)
    explicit_disabled = run_backtest(synthetic_dataset, sizing_config=SizingConfig(enabled=False))
    assert no_sizing.equity_curve == explicit_disabled.equity_curve
    assert all(t["size_pct"] == 100.0 for t in no_sizing.trade_log)


def test_sizing_enabled_never_exceeds_full_capital_and_tags_resizes(synthetic_dataset):
    result = run_backtest(
        synthetic_dataset,
        exit_config=ExitConfig(),
        sizing_config=SizingConfig(enabled=True, roc_period=10),
    )

    for t in result.trade_log:
        assert 0 < t["size_pct"] <= 100.0

    reasons = {t["exit_reason"] for t in result.trade_log if not t["is_open"]}
    assert reasons.issubset(
        {"signal_flip", "stop_loss", "fast_trend_break", "mean_reversion_extension", "resize"}
    )


def test_fee_bps_zero_matches_no_fee_default(synthetic_dataset):
    no_fee_arg = run_backtest(synthetic_dataset)
    explicit_zero = run_backtest(synthetic_dataset, fee_bps=0.0)
    assert no_fee_arg.equity_curve == explicit_zero.equity_curve
    assert no_fee_arg.summary["total_fees_paid"] == 0.0
    assert no_fee_arg.summary["fee_bps"] == 0.0


def test_fee_bps_reduces_final_equity(synthetic_dataset):
    no_fee = run_backtest(synthetic_dataset, exit_config=ExitConfig())
    with_fee = run_backtest(synthetic_dataset, exit_config=ExitConfig(), fee_bps=50.0)

    assert with_fee.summary["final_equity"] < no_fee.summary["final_equity"]
    assert with_fee.summary["total_fees_paid"] > 0.0


def test_fee_bps_charges_exact_turnover_hand_computed(monkeypatch):
    import pandas as pd

    import app.backtest as backtest_module

    idx = pd.bdate_range("2020-01-01", periods=4)
    dataset = pd.DataFrame(
        {"ndx": [100.0] * 4, "tqqq": [100.0, 110.0, 121.0, 121.0], "sqqq": [50.0] * 4, "qqq": [10.0] * 4},
        index=idx,
    )
    # Force a known, simple weight path: full long, full long, flat, flat --
    # one entry (turnover 1.0) and one exit (turnover 1.0), no other rebalances.
    fixed_signal = pd.DataFrame(
        {"close": [100.0] * 4, "ma_fast": [90.0] * 4, "ma_slow": [90.0] * 4, "target_weight": [1.0, 1.0, 0.0, 0.0]},
        index=idx,
    )
    monkeypatch.setattr(backtest_module, "compute_signal", lambda close, ma_fast=None, ma_slow=None: fixed_signal)

    result = run_backtest(
        dataset,
        initial_capital=10_000.0,
        exit_config=ExitConfig(enable_stop_loss=False, enable_fast_trend_break=False, enable_mean_reversion_exit=False),
        fee_bps=100.0,  # 1%
    )

    # Day0: enter full long from cash -> turnover 1.0, fee = 1% * $10,000 = $100.
    # Day1: still full long, no change -> turnover 0, no fee.
    # Day2: exit to cash -> turnover 1.0, fee = 1% of day1's ending equity.
    day0_equity = 10_000.0 * (1 - 0.01)  # day0 return is 0 (weight_shifted starts at 0) minus the entry fee
    day1_ret = 110.0 / 100.0 - 1.0  # holding day0's weight (1.0) into day1's TQQQ move
    day1_equity = day0_equity * (1 + day1_ret)
    day2_fee = 0.01 * day1_equity
    expected_total_fees = 100.0 + day2_fee

    assert result.summary["total_fees_paid"] == pytest.approx(expected_total_fees, abs=0.05)


def test_sizing_reduces_exposure_and_therefore_volatility(synthetic_dataset):
    full_size = run_backtest(synthetic_dataset, sizing_config=SizingConfig(enabled=False))
    scaled_down = run_backtest(
        synthetic_dataset,
        sizing_config=SizingConfig(enabled=True, full_threshold=999, partial_threshold=999, min_weight=0.3),
    )
    # Forcing min_weight (0.3x) for the entire history should shrink the
    # total return magnitude relative to full-size (both directions).
    assert abs(scaled_down.summary["total_return_pct"]) < abs(full_size.summary["total_return_pct"])
