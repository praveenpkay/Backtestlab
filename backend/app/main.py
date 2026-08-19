from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .backtest import run_backtest
from .data import DataUnavailableError, get_track_a_dataset

app = FastAPI(title="Backtest Lab API")

_default_origins = "http://localhost:3000,http://127.0.0.1:3000"
_cors_origins = os.environ.get("CORS_ORIGINS", _default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/backtest")
def backtest(
    initial_capital: float = Query(10_000.0, gt=0),
    refresh: bool = Query(False, description="Force a fresh pull from Yahoo Finance"),
):
    try:
        dataset = get_track_a_dataset(force_refresh=refresh)
    except DataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if dataset.empty:
        raise HTTPException(status_code=503, detail="No overlapping price history available yet")

    result = run_backtest(dataset, initial_capital=initial_capital)
    return {
        "trade_log": result.trade_log,
        "equity_curve": result.equity_curve,
        "drawdown": result.drawdown,
        "monthly_returns": result.monthly_returns,
        "summary": result.summary,
        "config": {
            "index_ticker": config.INDEX_TICKER,
            "long_ticker": config.LONG_TICKER,
            "short_ticker": config.SHORT_TICKER,
            "benchmark_ticker": config.BENCHMARK_TICKER,
            "ma_fast": config.MA_FAST,
            "ma_slow": config.MA_SLOW,
            "track_a_start": config.TRACK_A_START,
        },
    }
