import pytest

from app.exits import ExitConfig
from app.scenarios import Scenario, compute_buy_and_hold, default_scenarios, run_scenario, run_scenarios
from app.sizing import SizingConfig


def test_run_scenario_produces_kpis_and_readout(synthetic_dataset):
    scenario = Scenario("Test scenario")
    result = run_scenario(synthetic_dataset, scenario, 10_000.0)

    assert result["name"] == "Test scenario"
    assert result["kind"] == "strategy"
    assert "cagr_pct" in result["kpis"]
    assert "drawdown_episodes" in result["kpis"]
    assert "calmar_ratio" in result["kpis"]
    assert result["kpis"]["worst_day"] is not None
    assert isinstance(result["readout"], str) and len(result["readout"]) > 0


def test_compute_buy_and_hold_uses_full_capital_always(synthetic_dataset):
    result = compute_buy_and_hold(synthetic_dataset, "tqqq", "Buy & hold TQQQ", 10_000.0)

    assert result["kind"] == "benchmark"
    assert result["kpis"]["num_trades"] == 1
    first_price = synthetic_dataset["tqqq"].iloc[0]
    last_price = synthetic_dataset["tqqq"].iloc[-1]
    expected_total_return = (last_price / first_price - 1) * 100
    assert result["kpis"]["total_return_pct"] == pytest.approx(expected_total_return, abs=1e-3)


def test_run_scenarios_includes_benchmarks_and_custom_scenarios(synthetic_dataset):
    scenarios = [
        Scenario("Custom A", ma_fast=10, ma_slow=50),
        Scenario("Custom B", sizing_config=SizingConfig(enabled=True)),
    ]
    rows = run_scenarios(synthetic_dataset, scenarios, initial_capital=5_000.0)

    names = [r["name"] for r in rows]
    assert "Custom A" in names
    assert "Custom B" in names
    assert "Buy & hold TQQQ" in names
    assert "Buy & hold QQQ" in names
    assert sum(1 for r in rows if r["kind"] == "benchmark") == 2
    assert sum(1 for r in rows if r["kind"] == "strategy") == 2


def test_run_scenarios_uses_defaults_when_none_given(synthetic_dataset):
    rows = run_scenarios(synthetic_dataset, None, initial_capital=10_000.0)
    strategy_names = {r["name"] for r in rows if r["kind"] == "strategy"}
    assert strategy_names == {s.name for s in default_scenarios()}


def test_scenario_ma_override_actually_changes_results(synthetic_dataset):
    baseline = run_scenario(synthetic_dataset, Scenario("baseline", ma_fast=50, ma_slow=250), 10_000.0)
    fast = run_scenario(synthetic_dataset, Scenario("fast", ma_fast=10, ma_slow=40), 10_000.0)
    assert baseline["equity_curve"] != fast["equity_curve"]


def test_readout_mentions_benchmark_comparison(synthetic_dataset):
    rows = run_scenarios(synthetic_dataset, [Scenario("Only one")], initial_capital=10_000.0)
    strategy_row = next(r for r in rows if r["name"] == "Only one")
    assert "buy-and-hold" in strategy_row["readout"].lower()
