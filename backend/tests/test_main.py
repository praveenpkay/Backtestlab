import pytest
from fastapi.testclient import TestClient

from app import main as main_module


@pytest.fixture
def client(synthetic_dataset, monkeypatch):
    monkeypatch.setattr(main_module, "get_track_a_dataset", lambda force_refresh=False: synthetic_dataset)
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
