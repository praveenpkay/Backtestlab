from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import config
from .backtest import run_backtest
from .daily_log import get_daily_log, refresh_daily_log
from .data import DataUnavailableError, get_track_a_dataset, get_track_b_series
from .exits import ExitConfig
from .scenarios import Scenario, default_scenarios, run_scenarios
from .sizing import SizingConfig
from .trackb import compute_track_b_analysis
from .walkforward import run_walk_forward

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
    refresh: bool = Query(False, description="Force a fresh pull from the configured data source"),
    enable_stop_loss: bool = Query(True),
    stop_loss_pct: float = Query(config.EXIT_STOP_LOSS_PCT, gt=0, lt=1),
    enable_fast_trend_break: bool = Query(True),
    fast_ma_period: int = Query(config.EXIT_FAST_MA_PERIOD, gt=1),
    enable_mean_reversion_exit: bool = Query(True),
    extension_pct: float = Query(config.EXIT_EXTENSION_PCT, gt=0),
    enable_sizing: bool = Query(False),
    sizing_roc_period: int = Query(config.SIZING_ROC_PERIOD, gt=0),
    sizing_full_threshold: float = Query(config.SIZING_ROC_FULL_THRESHOLD, gt=0),
    sizing_partial_threshold: float = Query(config.SIZING_ROC_PARTIAL_THRESHOLD, gt=0),
    sizing_partial_weight: float = Query(config.SIZING_PARTIAL_WEIGHT, gt=0, le=1),
    sizing_min_weight: float = Query(config.SIZING_MIN_WEIGHT, gt=0, le=1),
    fee_bps: float = Query(config.DEFAULT_FEE_BPS, ge=0),
):
    try:
        dataset, signal_ticker = get_track_a_dataset(force_refresh=refresh)
    except DataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if dataset.empty:
        raise HTTPException(status_code=503, detail="No overlapping price history available yet")

    exit_config = ExitConfig(
        enable_stop_loss=enable_stop_loss,
        stop_loss_pct=stop_loss_pct,
        enable_fast_trend_break=enable_fast_trend_break,
        fast_ma_period=fast_ma_period,
        enable_mean_reversion_exit=enable_mean_reversion_exit,
        extension_pct=extension_pct,
    )
    sizing_config = SizingConfig(
        enabled=enable_sizing,
        roc_period=sizing_roc_period,
        full_threshold=sizing_full_threshold,
        partial_threshold=sizing_partial_threshold,
        partial_weight=sizing_partial_weight,
        min_weight=sizing_min_weight,
    )
    result = run_backtest(
        dataset,
        initial_capital=initial_capital,
        exit_config=exit_config,
        sizing_config=sizing_config,
        fee_bps=fee_bps,
    )
    return {
        "trade_log": result.trade_log,
        "equity_curve": result.equity_curve,
        "drawdown": result.drawdown,
        "monthly_returns": result.monthly_returns,
        "summary": result.summary,
        "config": {
            "index_ticker": config.INDEX_TICKER,
            "signal_ticker_used": signal_ticker,
            "data_source": config.DATA_SOURCE,
            "long_ticker": config.LONG_TICKER,
            "short_ticker": config.SHORT_TICKER,
            "benchmark_ticker": config.BENCHMARK_TICKER,
            "ma_fast": config.MA_FAST,
            "ma_slow": config.MA_SLOW,
            "track_a_start": config.TRACK_A_START,
            "exit_rules": {
                "enable_stop_loss": exit_config.enable_stop_loss,
                "stop_loss_pct": exit_config.stop_loss_pct,
                "enable_fast_trend_break": exit_config.enable_fast_trend_break,
                "fast_ma_period": exit_config.fast_ma_period,
                "enable_mean_reversion_exit": exit_config.enable_mean_reversion_exit,
                "extension_pct": exit_config.extension_pct,
            },
            "sizing": {
                "enabled": sizing_config.enabled,
                "roc_period": sizing_config.roc_period,
                "full_threshold": sizing_config.full_threshold,
                "partial_threshold": sizing_config.partial_threshold,
                "partial_weight": sizing_config.partial_weight,
                "min_weight": sizing_config.min_weight,
            },
            "fee_bps": fee_bps,
        },
    }


class ScenarioRequest(BaseModel):
    name: str
    ma_fast: int = config.MA_FAST
    ma_slow: int = config.MA_SLOW
    enable_stop_loss: bool = True
    stop_loss_pct: float = config.EXIT_STOP_LOSS_PCT
    enable_fast_trend_break: bool = True
    fast_ma_period: int = config.EXIT_FAST_MA_PERIOD
    enable_mean_reversion_exit: bool = True
    extension_pct: float = config.EXIT_EXTENSION_PCT
    enable_sizing: bool = False
    sizing_roc_period: int = config.SIZING_ROC_PERIOD
    sizing_full_threshold: float = config.SIZING_ROC_FULL_THRESHOLD
    sizing_partial_threshold: float = config.SIZING_ROC_PARTIAL_THRESHOLD
    sizing_partial_weight: float = config.SIZING_PARTIAL_WEIGHT
    sizing_min_weight: float = config.SIZING_MIN_WEIGHT
    fee_bps: float = config.DEFAULT_FEE_BPS

    def to_scenario(self) -> Scenario:
        return Scenario(
            name=self.name,
            ma_fast=self.ma_fast,
            ma_slow=self.ma_slow,
            exit_config=ExitConfig(
                enable_stop_loss=self.enable_stop_loss,
                stop_loss_pct=self.stop_loss_pct,
                enable_fast_trend_break=self.enable_fast_trend_break,
                fast_ma_period=self.fast_ma_period,
                enable_mean_reversion_exit=self.enable_mean_reversion_exit,
                extension_pct=self.extension_pct,
            ),
            sizing_config=SizingConfig(
                enabled=self.enable_sizing,
                roc_period=self.sizing_roc_period,
                full_threshold=self.sizing_full_threshold,
                partial_threshold=self.sizing_partial_threshold,
                partial_weight=self.sizing_partial_weight,
                min_weight=self.sizing_min_weight,
            ),
            fee_bps=self.fee_bps,
        )


class CompareRequest(BaseModel):
    initial_capital: float = 10_000.0
    refresh: bool = False
    scenarios: list[ScenarioRequest] = []
    walk_forward_split_date: str | None = None


@app.post("/api/scenarios/compare")
def scenarios_compare(body: CompareRequest):
    try:
        dataset, signal_ticker = get_track_a_dataset(force_refresh=body.refresh)
    except DataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if dataset.empty:
        raise HTTPException(status_code=503, detail="No overlapping price history available yet")

    scenarios = [s.to_scenario() for s in body.scenarios] if body.scenarios else default_scenarios()
    rows = run_scenarios(dataset, scenarios, initial_capital=body.initial_capital)

    if body.walk_forward_split_date:
        scenarios_by_name = {s.name: s for s in scenarios}
        for row in rows:
            if row["kind"] != "strategy":
                row["walk_forward"] = None
                continue
            scenario = scenarios_by_name[row["name"]]
            try:
                row["walk_forward"] = run_walk_forward(
                    dataset,
                    split_date=body.walk_forward_split_date,
                    initial_capital=body.initial_capital,
                    exit_config=scenario.exit_config,
                    sizing_config=scenario.sizing_config,
                    ma_fast=scenario.ma_fast,
                    ma_slow=scenario.ma_slow,
                    fee_bps=scenario.fee_bps,
                )
            except ValueError as exc:
                row["walk_forward"] = {"error": str(exc)}

    return {"signal_ticker_used": signal_ticker, "data_source": config.DATA_SOURCE, "scenarios": rows}


@app.get("/api/signal-history")
def signal_history(refresh: bool = Query(False)):
    """Track B: signal-only stress test on long-history index data (back to
    config.TRACK_B_START). Never returns simulated dollar returns."""
    try:
        close, ticker_used = get_track_b_series(force_refresh=refresh)
    except DataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if close.empty:
        raise HTTPException(status_code=503, detail="No long-history signal data available yet")

    return compute_track_b_analysis(close, ticker_used)


@app.get("/api/daily-log")
def daily_log(limit: int | None = Query(None, gt=0)):
    return {"rows": get_daily_log(limit=limit)}


@app.post("/api/daily-log/refresh")
def daily_log_refresh():
    try:
        row = refresh_daily_log()
    except DataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return row
