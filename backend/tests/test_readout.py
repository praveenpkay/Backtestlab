from app.readout import generate_readout

_BASE_KPIS = {
    "cagr_pct": 15.0,
    "total_return_pct": 200.0,
    "start_date": "2010-01-01",
    "end_date": "2020-01-01",
    "max_drawdown_pct": -25.0,
    "max_drawdown_days": 100,
    "num_drawdowns_over_20pct": 2,
    "worst_day": {"date": "2015-06-01", "return_pct": -12.0},
    "worst_month": {"year": 2015, "month": 6, "return_pct": -20.0},
    "max_consecutive_losses": 3,
    "worst_losing_streak_pct": -18.0,
    "num_trades": 7,
    "win_rate_pct": 42.0,
    "calmar_ratio": 0.6,
}


def test_readout_includes_core_numbers():
    text = generate_readout("My scenario", _BASE_KPIS)
    assert "My scenario" in text
    assert "15.0%" in text
    assert "-25.0%" in text
    assert "100 days" in text


def test_readout_flags_small_sample_size():
    text = generate_readout("My scenario", _BASE_KPIS)
    assert "fragile" in text.lower()


def test_readout_omits_small_sample_flag_with_enough_trades():
    kpis = {**_BASE_KPIS, "num_trades": 50}
    text = generate_readout("My scenario", kpis)
    assert "fragile" not in text.lower()


def test_readout_compares_against_benchmarks():
    benchmarks = {"TQQQ": {"cagr_pct": 10.0, "calmar_ratio": 0.3}}
    text = generate_readout("My scenario", _BASE_KPIS, benchmarks=benchmarks)
    assert "beat" in text.lower()
    assert "TQQQ" in text


def test_readout_handles_missing_optional_fields_gracefully():
    minimal = {"cagr_pct": 5.0, "total_return_pct": 20.0, "max_drawdown_pct": -5.0, "max_drawdown_days": 10}
    text = generate_readout("Minimal", minimal)
    assert "Minimal" in text
    assert len(text) > 0
