"""Alpaca: optional data source, needs a free paper/live API key pair.

Sign up at https://app.alpaca.markets/signup (the free paper-trading account
includes market data), then put the keys in backend/.env as
ALPACA_API_KEY_ID and ALPACA_SECRET_KEY (copy backend/.env.example) and set
DATA_SOURCE=alpaca.

Note: Alpaca's market data API serves stocks/ETFs, not raw index tickers --
use QQQ as the ^NDX signal proxy with this source (the app does this
automatically and labels it).
"""

from __future__ import annotations

import os
from datetime import date

import pandas as pd
import requests

from .base import DataSource, DataUnavailableError

ALPACA_BARS_URL = "https://data.alpaca.markets/v2/stocks/{ticker}/bars"


class AlpacaDataSource(DataSource):
    name = "alpaca"

    def __init__(self, api_key_id: str | None = None, secret_key: str | None = None):
        self.api_key_id = api_key_id or os.environ.get("ALPACA_API_KEY_ID")
        self.secret_key = secret_key or os.environ.get("ALPACA_SECRET_KEY")
        if not self.api_key_id or not self.secret_key:
            raise DataUnavailableError(
                "ALPACA_API_KEY_ID / ALPACA_SECRET_KEY are not set. Get a free key pair at "
                "https://app.alpaca.markets/signup, add them to backend/.env "
                "(see backend/.env.example), and set DATA_SOURCE=alpaca."
            )

    def fetch(self, ticker: str, start: str) -> pd.DataFrame:
        if ticker.startswith("^"):
            raise DataUnavailableError(
                f"Alpaca's market data API doesn't serve index tickers like {ticker}; "
                "configure the app to use QQQ as the signal proxy with this source."
            )

        headers = {"APCA-API-KEY-ID": self.api_key_id, "APCA-API-SECRET-KEY": self.secret_key}
        params: dict[str, str | int] = {
            "timeframe": "1Day",
            "start": f"{start}T00:00:00Z",
            "end": f"{date.today().isoformat()}T00:00:00Z",
            "limit": 10000,
            "adjustment": "all",
        }

        bars: list[dict] = []
        page_token: str | None = None
        try:
            while True:
                if page_token:
                    params["page_token"] = page_token
                resp = requests.get(
                    ALPACA_BARS_URL.format(ticker=ticker), headers=headers, params=params, timeout=20
                )
                resp.raise_for_status()
                payload = resp.json()
                bars.extend(payload.get("bars") or [])
                page_token = payload.get("next_page_token")
                if not page_token:
                    break
        except requests.RequestException as exc:
            raise DataUnavailableError(f"Alpaca request failed for {ticker}: {exc}") from exc

        if not bars:
            raise DataUnavailableError(f"Alpaca returned no bars for {ticker}")

        df = pd.DataFrame(bars)
        df["Date"] = pd.to_datetime(df["t"]).dt.tz_localize(None)
        df = df.set_index("Date").sort_index()
        df = df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"})
        return df[["Open", "High", "Low", "Close", "Volume"]]
