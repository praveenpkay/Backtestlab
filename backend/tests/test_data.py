import pandas as pd
import pytest

from app import config
from app.data import DataUnavailableError, get_index_history, get_track_a_dataset, get_track_b_series


def _ohlc(close_values, start="2010-01-04"):
    idx = pd.bdate_range(start, periods=len(close_values))
    return pd.DataFrame(
        {"Open": close_values, "High": close_values, "Low": close_values, "Close": close_values, "Volume": 1},
        index=idx,
    )


@pytest.fixture
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_CACHE_DIR", tmp_path)


def test_get_index_history_uses_real_index_when_available(monkeypatch, isolated_cache):
    from app import data as data_module

    def _fake_download(ticker, start):
        assert ticker == config.INDEX_TICKER
        return _ohlc([100, 101, 102])

    monkeypatch.setattr(data_module, "_download", _fake_download)

    close, ticker_used = get_index_history()

    assert ticker_used == config.INDEX_TICKER
    assert list(close) == [100, 101, 102]


def test_get_index_history_falls_back_to_qqq_when_index_unavailable(monkeypatch, isolated_cache):
    from app import data as data_module

    def _fake_download(ticker, start):
        if ticker == config.INDEX_TICKER:
            raise DataUnavailableError("no ^NDX on this source")
        assert ticker == config.BENCHMARK_TICKER
        return _ohlc([50, 51, 52])

    monkeypatch.setattr(data_module, "_download", _fake_download)

    close, ticker_used = get_index_history()

    assert ticker_used == config.BENCHMARK_TICKER
    assert list(close) == [50, 51, 52]


def test_get_track_a_dataset_reports_signal_ticker_used(monkeypatch, isolated_cache):
    from app import data as data_module

    def _fake_download(ticker, start):
        if ticker == config.INDEX_TICKER:
            raise DataUnavailableError("unavailable")
        return _ohlc([10, 11, 12])

    monkeypatch.setattr(data_module, "_download", _fake_download)

    dataset, ticker_used = get_track_a_dataset()

    assert ticker_used == config.BENCHMARK_TICKER
    assert list(dataset.columns) == ["ndx", "tqqq", "sqqq", "qqq"]
    assert len(dataset) == 3


def test_get_track_b_series_uses_long_history_start(monkeypatch, isolated_cache):
    from app import data as data_module

    seen_starts = []

    def _fake_download(ticker, start):
        seen_starts.append(start)
        return _ohlc([1, 2, 3], start="1985-01-02")

    monkeypatch.setattr(data_module, "_download", _fake_download)

    close, ticker_used = get_track_b_series()

    assert config.TRACK_B_START in seen_starts
    assert ticker_used == config.INDEX_TICKER
    assert len(close) == 3


def test_track_a_and_track_b_caches_are_kept_separate(monkeypatch, isolated_cache):
    from app import data as data_module

    call_count = {"n": 0}

    def _fake_download(ticker, start):
        call_count["n"] += 1
        length = 3 if start == config.TRACK_A_START else 5
        return _ohlc(list(range(length)), start=start)

    monkeypatch.setattr(data_module, "_download", _fake_download)

    track_a = data_module.get_price_history(config.INDEX_TICKER)
    track_b = data_module.get_price_history(config.INDEX_TICKER, start=config.TRACK_B_START)

    assert len(track_a) == 3
    assert len(track_b) == 5
    assert call_count["n"] == 2  # separate cache files -> both had to download once
