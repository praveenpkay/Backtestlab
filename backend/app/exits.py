"""Job 3: exit / square-off overlay.

Layers three basic, independently-toggleable exit rules on top of the Job 1
entry signal. Job 1 alone only exits a position when its own rule flips
(price crosses back below/above the 50d/250d MAs) -- these rules give it a
faster, more mechanical way to bail before that slow confirmation arrives:

- **Stop-loss**: exit if the held ETF (TQQQ or SQQQ) has fallen more than
  `stop_loss_pct` from its entry price. The bluntest, most literal "cut your
  losses" rule.
- **Fast trend-break**: exit if ^NDX closes back across a much faster moving
  average (`fast_ma_period`, default 20d) than the slow 250d one Job 1 waits
  for -- an early warning that the trend may be breaking.
- **Mean-reversion extension**: exit if ^NDX has stretched more than
  `extension_pct` above (for a long) or below (for a short) its 50-day MA --
  "the market moved too far, too fast" per the original spec.

All three are evaluated end-of-day only (never intraday), consistent with
the rest of this system's "decide once near the close" philosophy.

After ANY of these rules forces an exit, the overlay will not re-enter the
same direction until Job 1's own signal changes to something different from
what it read at the moment of the forced exit -- otherwise a stop-loss would
just immediately re-buy the same dip it was designed to avoid.
"""

from __future__ import annotations

from dataclasses import dataclass

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
            asset = dataset["tqqq"] if current_direction > 0 else dataset["sqqq"]
            current_price = asset.iloc[i]
            reason = None

            if base_weight.iloc[i] != current_direction:
                reason = "signal_flip"

            if reason is None and exit_config.enable_stop_loss:
                if (current_price / entry_price - 1.0) <= -exit_config.stop_loss_pct:
                    reason = "stop_loss"

            if reason is None and exit_config.enable_fast_trend_break:
                fast_val = fast_ma_short.iloc[i]
                if pd.notna(fast_val):
                    if current_direction > 0 and ndx_close.iloc[i] < fast_val:
                        reason = "fast_trend_break"
                    elif current_direction < 0 and ndx_close.iloc[i] > fast_val:
                        reason = "fast_trend_break"

            if reason is None and exit_config.enable_mean_reversion_exit:
                ma_val = ma_fast_ndx.iloc[i]
                if pd.notna(ma_val):
                    if current_direction > 0 and ndx_close.iloc[i] > ma_val * (1 + exit_config.extension_pct):
                        reason = "mean_reversion_extension"
                    elif current_direction < 0 and ndx_close.iloc[i] < ma_val * (1 - exit_config.extension_pct):
                        reason = "mean_reversion_extension"

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
