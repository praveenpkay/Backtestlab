"""Fetches and locally caches daily price data for the tickers Backtest Lab needs.

Yahoo Finance (via yfinance) is the data source. Every ticker's daily OHLC
history is cached to backend/data_cache/<TICKER>.csv so the app keeps working
(on slightly stale data) if Yahoo is unreachable, and so repeated requests
don't re-download the same history over and over.
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import yfinance as yf

from . import config


class DataUnavailableError(RuntimeError):
    """Raised when a ticker has neither a fresh download nor a usable cache."""


def _cache_path(ticker: str) -> Path:
    safe = ticker.replace("^", "")
    return config.DATA_CACHE_DIR / f"{safe}.csv"


def _read_cache(ticker: str) -> pd.DataFrame | None:
    path = _cache_path(ticker)
    if not path.exists():
        return None
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.index.name = "Date"
    return df


def _write_cache(ticker: str, df: pd.DataFrame) -> None:
    df.to_csv(_cache_path(ticker))


def _cache_is_fresh(ticker: str) -> bool:
    path = _cache_path(ticker)
    if not path.exists():
        return False
    age_hours = (time.time() - path.stat().st_mtime) / 3600
    return age_hours < config.CACHE_TTL_HOURS


def _download(ticker: str) -> pd.DataFrame:
    raw = yf.download(
        ticker,
        start=config.TRACK_A_START,
        progress=False,
        auto_adjust=True,
    )
    if raw is None or raw.empty:
        raise DataUnavailableError(f"yfinance returned no data for {ticker}")
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    raw.index.name = "Date"
    return raw[["Open", "High", "Low", "Close", "Volume"]]


def get_price_history(ticker: str, force_refresh: bool = False) -> pd.DataFrame:
    """Returns a DataFrame of Open/High/Low/Close/Volume indexed by Date.

    Tries a fresh download first (unless the cache is already fresh and
    force_refresh is False); falls back to whatever cache exists if the
    download fails, so a network hiccup doesn't take the whole app down.
    """
    if not force_refresh and _cache_is_fresh(ticker):
        cached = _read_cache(ticker)
        if cached is not None:
            return cached

    try:
        fresh = _download(ticker)
        _write_cache(ticker, fresh)
        return fresh
    except Exception as exc:
        cached = _read_cache(ticker)
        if cached is not None:
            return cached
        raise DataUnavailableError(
            f"Could not fetch {ticker} from Yahoo Finance and no cache exists: {exc}"
        ) from exc


def get_track_a_dataset(force_refresh: bool = False) -> pd.DataFrame:
    """Joins Close prices for the index + both leveraged ETFs + benchmark
    into a single DataFrame aligned on trading day.
    """
    tickers = {
        "ndx": config.INDEX_TICKER,
        "tqqq": config.LONG_TICKER,
        "sqqq": config.SHORT_TICKER,
        "qqq": config.BENCHMARK_TICKER,
    }
    closes = {}
    for col, ticker in tickers.items():
        hist = get_price_history(ticker, force_refresh=force_refresh)
        closes[col] = hist["Close"]

    df = pd.DataFrame(closes).dropna(how="any")
    df = df.sort_index()
    return df
