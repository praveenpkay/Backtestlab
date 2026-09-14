import pytest
from fastapi.testclient import TestClient

from app import main as main_module


@pytest.fixture
def client(synthetic_dataset, monkeypatch):
    monkeypatch.setattr(
        main_module, "get_track_a_dataset", lambda force_refresh=False: (synthetic_dataset, "^NDX")
    )
    return TestClient(main_module.app)


def test_backtest_endpoint_defaults_have_exits_enabled(client):
    res = client.get("/api/backtest")
    assert res.status_code == 200
    body = res.json()
    assert body["config"]["exit_rules"]["enable_stop_loss"] is True
    assert body["config"]["exit_rules"]["enable_fast_trend_break"] is True
    assert body["config"]["exit_rules"]["enable_mean_reversion_exit"] is True
    assert "exit_reason_breakdown" in body["summary"]
    assert all("exit_reason" in t for t in body["trade_log"])


def test_backtest_endpoint_can_disable_all_exit_rules(client):
    res = client.get(
        "/api/backtest",
        params={
            "enable_stop_loss": "false",
            "enable_fast_trend_break": "false",
            "enable_mean_reversion_exit": "false",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["config"]["exit_rules"]["enable_stop_loss"] is False
    reasons = set(body["summary"]["exit_reason_breakdown"])
    assert reasons.issubset({"signal_flip"})


def test_backtest_endpoint_respects_custom_thresholds(client):
    res = client.get("/api/backtest", params={"stop_loss_pct": "0.05", "fast_ma_period": "10"})
    assert res.status_code == 200
    body = res.json()
    assert body["config"]["exit_rules"]["stop_loss_pct"] == 0.05
    assert body["config"]["exit_rules"]["fast_ma_period"] == 10


def test_backtest_endpoint_sizing_disabled_by_default(client):
    res = client.get("/api/backtest")
    assert res.status_code == 200
    body = res.json()
    assert body["config"]["sizing"]["enabled"] is False
    assert all(t["size_pct"] == 100.0 for t in body["trade_log"])


def test_backtest_endpoint_can_enable_sizing(client):
    res = client.get("/api/backtest", params={"enable_sizing": "true", "sizing_roc_period": "10"})
    assert res.status_code == 200
    body = res.json()
    assert body["config"]["sizing"]["enabled"] is True
    assert body["config"]["sizing"]["roc_period"] == 10
    assert all(0 < t["size_pct"] <= 100.0 for t in body["trade_log"])


def test_scenarios_compare_endpoint_defaults(client):
    res = client.post("/api/scenarios/compare", json={})
    assert res.status_code == 200
    body = res.json()
    names = [s["name"] for s in body["scenarios"]]
    assert "Buy & hold TQQQ" in names
    assert "Buy & hold QQQ" in names
    assert len(names) >= 4  # default scenarios + 2 benchmarks


def test_scenarios_compare_endpoint_custom_scenarios(client):
    res = client.post(
        "/api/scenarios/compare",
        json={
            "initial_capital": 5000,
            "scenarios": [
                {"name": "My Scenario", "ma_fast": 10, "ma_slow": 40, "enable_sizing": True}
            ],
        },
    )
    assert res.status_code == 200
    body = res.json()
    names = [s["name"] for s in body["scenarios"]]
    assert names == ["My Scenario", "Buy & hold TQQQ", "Buy & hold QQQ"]
    my_scenario = body["scenarios"][0]
    assert my_scenario["kpis"]["initial_capital"] == 5000.0
    assert "readout" in my_scenario


def test_signal_history_endpoint_is_labeled_signal_only(synthetic_dataset, monkeypatch):
    from app import main as main_module

    monkeypatch.setattr(
        main_module, "get_track_b_series", lambda force_refresh=False: (synthetic_dataset["ndx"], "^NDX")
    )
    client = TestClient(main_module.app)

    res = client.get("/api/signal-history")

    assert res.status_code == 200
    body = res.json()
    assert body["signal_only"] is True
    assert len(body["series"]) == len(synthetic_dataset)
