"""Fetches and locally caches daily price data for the tickers Backtest Lab
needs, via whichever data source is configured (config.DATA_SOURCE: stooq by
default, or polygon/alpaca with a free API key -- see .env.example).

Every ticker's daily OHLC history is cached to backend/data_cache/*.csv so
the app keeps working (on slightly stale data) if the data source is briefly
unreachable, and so repeated requests don't re-fetch the same history over
and over.
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from . import config
from .datasources import DataUnavailableError, get_data_source

__all__ = ["DataUnavailableError", "get_price_history", "get_index_history", "get_track_a_dataset", "get_track_b_series"]


def _cache_path(ticker: str, start: str) -> Path:
    safe = ticker.replace("^", "")
    suffix = "" if start == config.TRACK_A_START else f"__{start}"
    return config.DATA_CACHE_DIR / f"{safe}{suffix}.csv"


def _read_cache(ticker: str, start: str) -> pd.DataFrame | None:
    path = _cache_path(ticker, start)
    if not path.exists():
        return None
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.index.name = "Date"
    return df


def _write_cache(ticker: str, start: str, df: pd.DataFrame) -> None:
    df.to_csv(_cache_path(ticker, start))


def _cache_is_fresh(ticker: str, start: str) -> bool:
    path = _cache_path(ticker, start)
    if not path.exists():
        return False
    age_hours = (time.time() - path.stat().st_mtime) / 3600
    return age_hours < config.CACHE_TTL_HOURS


def _download(ticker: str, start: str) -> pd.DataFrame:
    source = get_data_source()
    df = source.fetch(ticker, start)
    if df is None or df.empty:
        raise DataUnavailableError(f"{source.name} returned no data for {ticker}")
    return df


def get_price_history(
    ticker: str, force_refresh: bool = False, start: str | None = None
) -> pd.DataFrame:
    """Returns a DataFrame of Open/High/Low/Close/Volume indexed by Date.

    Tries a fresh download first (unless the cache is already fresh and
    force_refresh is False); falls back to whatever cache exists if the
    download fails, so a network hiccup doesn't take the whole app down.
    """
    start = start or config.TRACK_A_START

    if not force_refresh and _cache_is_fresh(ticker, start):
        cached = _read_cache(ticker, start)
        if cached is not None:
            return cached

    try:
        fresh = _download(ticker, start)
        _write_cache(ticker, start, fresh)
        return fresh
    except Exception as exc:
        cached = _read_cache(ticker, start)
        if cached is not None:
            return cached
        raise DataUnavailableError(
            f"Could not fetch {ticker} from {config.DATA_SOURCE} and no cache exists: {exc}"
        ) from exc


def get_index_history(
    force_refresh: bool = False, start: str | None = None
) -> tuple[pd.Series, str]:
    """Close price history for the signal ticker. Tries the real index
    (config.INDEX_TICKER, e.g. ^NDX) first; falls back to the QQQ proxy if
    the configured data source doesn't carry it. Always reports which ticker
    was actually used so callers can label results honestly.
    """
    try:
        hist = get_price_history(config.INDEX_TICKER, force_refresh=force_refresh, start=start)
        return hist["Close"], config.INDEX_TICKER
    except DataUnavailableError:
        hist = get_price_history(config.BENCHMARK_TICKER, force_refresh=force_refresh, start=start)
        return hist["Close"], config.BENCHMARK_TICKER


def get_track_a_dataset(force_refresh: bool = False) -> tuple[pd.DataFrame, str]:
    """Joins Close prices for the index (or QQQ proxy) + both leveraged ETFs
    + benchmark into a single DataFrame aligned on trading day, from 2010
    onward. Returns (dataset, signal_ticker_used).
    """
    ndx_close, signal_ticker = get_index_history(force_refresh=force_refresh)
    tqqq = get_price_history(config.LONG_TICKER, force_refresh=force_refresh)["Close"]
    sqqq = get_price_history(config.SHORT_TICKER, force_refresh=force_refresh)["Close"]
    qqq = get_price_history(config.BENCHMARK_TICKER, force_refresh=force_refresh)["Close"]

    df = pd.DataFrame({"ndx": ndx_close, "tqqq": tqqq, "sqqq": sqqq, "qqq": qqq}).dropna(how="any")
    return df.sort_index(), signal_ticker


def get_track_b_series(force_refresh: bool = False) -> tuple[pd.Series, str]:
    """Long-history signal-only series (Track B): the index (or QQQ proxy)
    back to config.TRACK_B_START. NEVER turned into simulated leveraged
    dollar returns -- see backend/app/trackb.py, which only scores whether
    the entry signal would have gone risk-on/off at the right times.
    """
    return get_index_history(force_refresh=force_refresh, start=config.TRACK_B_START)
