import pandas as pd
import pytest
import requests

from app.datasources import DataUnavailableError, get_data_source
from app.datasources.alpaca import AlpacaDataSource
from app.datasources.polygon import PolygonDataSource
from app.datasources.stooq import StooqDataSource, _to_stooq_symbol


class _FakeResponse:
    def __init__(self, text="", json_data=None, status=200):
        self.text = text
        self._json = json_data
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return self._json


def test_to_stooq_symbol_maps_index_and_etf_tickers():
    assert _to_stooq_symbol("^NDX") == "^ndx"
    assert _to_stooq_symbol("TQQQ") == "tqqq.us"


def test_stooq_fetch_parses_csv(monkeypatch):
    csv_text = "Date,Open,High,Low,Close,Volume\n2020-01-02,10,11,9,10.5,1000\n2020-01-03,10.5,11,10,10.8,1200\n"
    monkeypatch.setattr(requests, "get", lambda url, timeout=15: _FakeResponse(text=csv_text))

    df = StooqDataSource().fetch("TQQQ", "2020-01-01")

    assert list(df.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert len(df) == 2
    assert df["Close"].iloc[-1] == 10.8


def test_stooq_fetch_respects_start_date(monkeypatch):
    csv_text = "Date,Open,High,Low,Close,Volume\n2019-12-31,1,1,1,1,1\n2020-01-02,10,11,9,10.5,1000\n"
    monkeypatch.setattr(requests, "get", lambda url, timeout=15: _FakeResponse(text=csv_text))

    df = StooqDataSource().fetch("TQQQ", "2020-01-01")

    assert len(df) == 1
    assert df.index[0] == pd.Timestamp("2020-01-02")


def test_stooq_fetch_raises_on_empty_response(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda url, timeout=15: _FakeResponse(text=""))
    with pytest.raises(DataUnavailableError):
        StooqDataSource().fetch("TQQQ", "2020-01-01")


def test_stooq_fetch_raises_on_network_error(monkeypatch):
    def _raise(*args, **kwargs):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(requests, "get", _raise)
    with pytest.raises(DataUnavailableError):
        StooqDataSource().fetch("TQQQ", "2020-01-01")


def test_polygon_requires_api_key(monkeypatch):
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)
    with pytest.raises(DataUnavailableError):
        PolygonDataSource()


def test_polygon_fetch_parses_aggs(monkeypatch):
    payload = {
        "results": [
            {"t": 1577923200000, "o": 10, "h": 11, "l": 9, "c": 10.5, "v": 1000},
            {"t": 1578009600000, "o": 10.5, "h": 11, "l": 10, "c": 10.8, "v": 1200},
        ]
    }
    monkeypatch.setattr(requests, "get", lambda url, timeout=20: _FakeResponse(json_data=payload))

    df = PolygonDataSource(api_key="fake-key").fetch("TQQQ", "2020-01-01")

    assert len(df) == 2
    assert list(df.columns) == ["Open", "High", "Low", "Close", "Volume"]


def test_polygon_maps_index_ticker():
    from app.datasources.polygon import _to_polygon_ticker

    assert _to_polygon_ticker("^NDX") == "I:NDX"
    assert _to_polygon_ticker("TQQQ") == "TQQQ"


def test_alpaca_requires_api_keys(monkeypatch):
    monkeypatch.delenv("ALPACA_API_KEY_ID", raising=False)
    monkeypatch.delenv("ALPACA_SECRET_KEY", raising=False)
    with pytest.raises(DataUnavailableError):
        AlpacaDataSource()


def test_alpaca_rejects_index_tickers():
    source = AlpacaDataSource(api_key_id="id", secret_key="secret")
    with pytest.raises(DataUnavailableError):
        source.fetch("^NDX", "2020-01-01")


def test_alpaca_fetch_paginates(monkeypatch):
    calls = []

    def _fake_get(url, headers=None, params=None, timeout=20):
        calls.append(dict(params))
        if "page_token" not in params:
            return _FakeResponse(
                json_data={
                    "bars": [{"t": "2020-01-02T00:00:00Z", "o": 1, "h": 2, "l": 0.5, "c": 1.5, "v": 10}],
                    "next_page_token": "abc",
                }
            )
        return _FakeResponse(
            json_data={
                "bars": [{"t": "2020-01-03T00:00:00Z", "o": 1.5, "h": 2, "l": 1, "c": 1.8, "v": 20}],
                "next_page_token": None,
            }
        )

    monkeypatch.setattr(requests, "get", _fake_get)
    df = AlpacaDataSource(api_key_id="id", secret_key="secret").fetch("TQQQ", "2020-01-01")

    assert len(df) == 2
    assert len(calls) == 2


def test_get_data_source_factory_selects_by_config(monkeypatch):
    from app import config as config_module

    monkeypatch.setattr(config_module, "DATA_SOURCE", "stooq")
    assert isinstance(get_data_source(), StooqDataSource)

    monkeypatch.setenv("POLYGON_API_KEY", "fake-key")
    assert isinstance(get_data_source("polygon"), PolygonDataSource)


def test_get_data_source_rejects_unknown_name():
    with pytest.raises(DataUnavailableError):
        get_data_source("not-a-real-source")
