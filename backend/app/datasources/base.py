"""Common interface every price data source implements, so backend/app/data.py
and everything above it (signals, backtest, exits) never needs to know or
care which one is actually configured."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class DataUnavailableError(RuntimeError):
    """Raised when a data source can't return usable price history -- missing
    API key, network failure, unknown ticker, empty response, etc."""


class DataSource(ABC):
    name: str

    @abstractmethod
    def fetch(self, ticker: str, start: str) -> pd.DataFrame:
        """Returns a DataFrame with columns Open, High, Low, Close, Volume,
        indexed by tz-naive Date (ascending), covering `ticker` from `start`
        (YYYY-MM-DD) through the latest available session. Raises
        DataUnavailableError if that can't be produced."""
