"""Job 3: exit / square-off overlay.

Layers independently-toggleable exit rules on top of the Job 1 entry signal.
Job 1 alone only exits a position when its own rule flips (price crosses
back below/above the 50d/250d MAs) -- these rules give it a faster, more
mechanical way to bail before that slow confirmation arrives.

Built-in rules (see EXIT_RULES below):

- **Stop-loss**: exit if the held ETF (TQQQ or SQQQ) has fallen more than
  `stop_loss_pct` from its entry price. The bluntest, most literal "cut your
  losses" rule.
- **Fast trend-break**: exit if ^NDX closes back across a much faster moving
  average (`fast_ma_period`, default 20d) than the slow 250d one Job 1 waits
  for -- an early warning that the trend may be breaking.
- **Mean-reversion extension**: exit if ^NDX has stretched more than
  `extension_pct` above (for a long) or below (for a short) its 50-day MA --
  "the market moved too far, too fast" per the original spec.

All rules are evaluated end-of-day only (never intraday), consistent with
the rest of this system's "decide once near the close" philosophy.

After ANY rule forces an exit, the overlay will not re-enter the same
direction until Job 1's own signal changes to something different from what
it read at the moment of the forced exit -- otherwise a stop-loss would just
immediately re-buy the same dip it was designed to avoid.

**Adding a new rule**: write a function `(ctx: ExitContext) -> bool` (True
means "exit now"), add a matching enable flag + any thresholds to
ExitConfig, and append an ExitRule entry to EXIT_RULES. Nothing else in this
module or in backtest.py needs to change -- the loop below just walks the
registry in order and uses whichever rule fires first.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from . import config


@dataclass
class ExitConfig:
    enable_stop_loss: bool = True
    stop_loss_pct: float = config.EXIT_STOP_LOSS_PCT
    enable_fast_trend_break: bool = True
    fast_ma_period: int = config.EXIT_FAST_MA_PERIOD
    enable_mean_reversion_exit: bool = True
    extension_pct: float = config.EXIT_EXTENSION_PCT


@dataclass
class ExitContext:
    """Everything a single rule needs to decide whether TODAY (index i) is
    an exit day for the position currently held in `direction`."""

    i: int
    direction: float  # +1 or -1 -- which side we're currently holding
    entry_price: float
    tqqq: pd.Series
    sqqq: pd.Series
    ndx_close: pd.Series
    ma_fast_ndx: pd.Series
    fast_ma_short: pd.Series
    cfg: ExitConfig

    @property
    def held_asset_price(self) -> float:
        asset = self.tqqq if self.direction > 0 else self.sqqq
        return asset.iloc[self.i]


def _stop_loss_rule(ctx: ExitContext) -> bool:
    return (ctx.held_asset_price / ctx.entry_price - 1.0) <= -ctx.cfg.stop_loss_pct


def _fast_trend_break_rule(ctx: ExitContext) -> bool:
    fast_val = ctx.fast_ma_short.iloc[ctx.i]
    if pd.isna(fast_val):
        return False
    close = ctx.ndx_close.iloc[ctx.i]
    return close < fast_val if ctx.direction > 0 else close > fast_val


def _mean_reversion_rule(ctx: ExitContext) -> bool:
    ma_val = ctx.ma_fast_ndx.iloc[ctx.i]
    if pd.isna(ma_val):
        return False
    close = ctx.ndx_close.iloc[ctx.i]
    if ctx.direction > 0:
        return close > ma_val * (1 + ctx.cfg.extension_pct)
    return close < ma_val * (1 - ctx.cfg.extension_pct)


@dataclass
class ExitRule:
    name: str
    enabled: Callable[[ExitConfig], bool]
    fires: Callable[[ExitContext], bool]


# Evaluated in this order; the first enabled rule that fires wins. To add a
# rule: write a `fires` function above, add its flag/thresholds to
# ExitConfig, and append it here.
EXIT_RULES: list[ExitRule] = [
    ExitRule("stop_loss", lambda cfg: cfg.enable_stop_loss, _stop_loss_rule),
    ExitRule("fast_trend_break", lambda cfg: cfg.enable_fast_trend_break, _fast_trend_break_rule),
    ExitRule(
        "mean_reversion_extension", lambda cfg: cfg.enable_mean_reversion_exit, _mean_reversion_rule
    ),
]


@dataclass
class ExitOverlayResult:
    effective_weight: pd.Series
    exit_reason: pd.Series  # object dtype, None except on a day a position closes


def apply_exit_overlay(
    dataset: pd.DataFrame,
    signal_df: pd.DataFrame,
    exit_config: ExitConfig,
) -> ExitOverlayResult:
    """dataset needs columns ndx/tqqq/sqqq (Close prices). signal_df is the
    output of signals.compute_signal(dataset['ndx']) -- needs close/ma_fast/
    target_weight columns, same index as dataset."""
    dates = dataset.index
    n = len(dates)

    base_weight = signal_df["target_weight"]
    ndx_close = dataset["ndx"]
    ma_fast_ndx = signal_df["ma_fast"]
    fast_ma_short = ndx_close.rolling(exit_config.fast_ma_period).mean()

    effective_weight = pd.Series(0.0, index=dates)
    exit_reason = pd.Series([None] * n, index=dates, dtype=object)

    current_direction = 0.0
    entry_price = None
    blocked_value: float | None = None

    for i in range(n):
        if current_direction != 0.0:
            reason = None

            if base_weight.iloc[i] != current_direction:
                reason = "signal_flip"
            else:
                ctx = ExitContext(
                    i=i,
                    direction=current_direction,
                    entry_price=entry_price,
                    tqqq=dataset["tqqq"],
                    sqqq=dataset["sqqq"],
                    ndx_close=ndx_close,
                    ma_fast_ndx=ma_fast_ndx,
                    fast_ma_short=fast_ma_short,
                    cfg=exit_config,
                )
                for rule in EXIT_RULES:
                    if rule.enabled(exit_config) and rule.fires(ctx):
                        reason = rule.name
                        break

            if reason is not None:
                exit_reason.iloc[i] = reason
                blocked_value = None if reason == "signal_flip" else base_weight.iloc[i]
                current_direction = 0.0
                entry_price = None

        if current_direction == 0.0:
            candidate = base_weight.iloc[i]
            if candidate == 0.0:
                blocked_value = None
            elif candidate != blocked_value:
                current_direction = candidate
                asset = dataset["tqqq"] if candidate > 0 else dataset["sqqq"]
                entry_price = asset.iloc[i]
                blocked_value = None

        effective_weight.iloc[i] = current_direction

    return ExitOverlayResult(effective_weight=effective_weight, exit_reason=exit_reason)
