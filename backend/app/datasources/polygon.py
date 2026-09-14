"""Polygon.io: optional data source, needs a free API key.

Sign up at https://polygon.io/dashboard/signup (free tier covers this app's
needs -- end-of-day bars only, no real-time), then put the key in
backend/.env as POLYGON_API_KEY (copy backend/.env.example) and set
DATA_SOURCE=polygon.
"""

from __future__ import annotations

import os
from datetime import date

import pandas as pd
import requests

from .base import DataSource, DataUnavailableError

POLYGON_AGGS_URL = (
    "https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
    "?adjusted=true&sort=asc&limit=50000&apiKey={api_key}"
)


def _to_polygon_ticker(ticker: str) -> str:
    # Polygon's index convention is "I:NDX", not "^NDX".
    if ticker.startswith("^"):
        return f"I:{ticker[1:]}"
    return ticker


class PolygonDataSource(DataSource):
    name = "polygon"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("POLYGON_API_KEY")
        if not self.api_key:
            raise DataUnavailableError(
                "POLYGON_API_KEY is not set. Get a free key at "
                "https://polygon.io/dashboard/signup, add it to backend/.env "
                "(see backend/.env.example), and set DATA_SOURCE=polygon."
            )

    def fetch(self, ticker: str, start: str) -> pd.DataFrame:
        symbol = _to_polygon_ticker(ticker)
        url = POLYGON_AGGS_URL.format(
            ticker=symbol, start=start, end=date.today().isoformat(), api_key=self.api_key
        )
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            payload = resp.json()
        except requests.RequestException as exc:
            raise DataUnavailableError(f"Polygon request failed for {ticker} ({symbol}): {exc}") from exc

        results = payload.get("results")
        if not results:
            raise DataUnavailableError(
                f"Polygon returned no results for {ticker} ({symbol}): status={payload.get('status')}"
            )

        df = pd.DataFrame(results)
        df["Date"] = pd.to_datetime(df["t"], unit="ms")
        df = df.set_index("Date").sort_index()
        df = df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"})
        return df[["Open", "High", "Low", "Close", "Volume"]]
