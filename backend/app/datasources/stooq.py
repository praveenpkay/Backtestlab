"""Stooq: the default data source. No API key, a stable documented CSV
endpoint -- unlike scraping Yahoo Finance's undocumented API (which is also
what got blocked outright in the sandbox this was built in)."""

from __future__ import annotations

from io import StringIO

import pandas as pd
import requests

from .base import DataSource, DataUnavailableError

STOOQ_CSV_URL = "https://stooq.com/q/d/l/?s={symbol}&i=d"

REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def _to_stooq_symbol(ticker: str) -> str:
    if ticker.startswith("^"):
        return ticker.lower()  # e.g. ^NDX -> ^ndx
    return f"{ticker.lower()}.us"  # e.g. TQQQ -> tqqq.us


class StooqDataSource(DataSource):
    name = "stooq"

    def fetch(self, ticker: str, start: str) -> pd.DataFrame:
        symbol = _to_stooq_symbol(ticker)
        url = STOOQ_CSV_URL.format(symbol=symbol)
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise DataUnavailableError(f"Stooq request failed for {ticker} ({symbol}): {exc}") from exc

        text = resp.text.strip()
        first_line = text.splitlines()[0] if text else ""
        if not text or "Date" not in first_line:
            raise DataUnavailableError(
                f"Stooq returned no data for {ticker} (tried symbol '{symbol}')"
            )

        df = pd.read_csv(StringIO(text))
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if df.empty or missing:
            raise DataUnavailableError(
                f"Stooq response for {ticker} ({symbol}) was empty or missing columns {missing}"
            )

        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date").sort_index()
        df = df.loc[df.index >= pd.Timestamp(start)]
        return df[REQUIRED_COLUMNS]
