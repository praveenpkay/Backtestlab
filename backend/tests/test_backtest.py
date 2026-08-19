import math

from app.backtest import run_backtest
from app.signals import compute_signal


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
