from __future__ import annotations

from .. import config
from .alpaca import AlpacaDataSource
from .base import DataSource, DataUnavailableError
from .polygon import PolygonDataSource
from .stooq import StooqDataSource

_SOURCES: dict[str, type[DataSource]] = {
    "stooq": StooqDataSource,
    "polygon": PolygonDataSource,
    "alpaca": AlpacaDataSource,
}


def get_data_source(name: str | None = None) -> DataSource:
    key = (name or config.DATA_SOURCE).lower()
    cls = _SOURCES.get(key)
    if cls is None:
        raise DataUnavailableError(
            f"Unknown DATA_SOURCE '{key}'. Choose one of: {', '.join(_SOURCES)}"
        )
    return cls()


__all__ = ["DataSource", "DataUnavailableError", "get_data_source"]
