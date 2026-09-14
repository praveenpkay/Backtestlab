"""Job 2: position sizing overlay.

Rate-of-change (momentum strength) scales how much of the account is
actually deployed once Job 1 + Job 3 have already decided a direction:
trend accelerating (|ROC| large) -> bigger position; decelerating -> trim.
This never changes *whether* you're long/short/cash -- only how much.

Off by default: Job 1 + Job 3 alone are always 100% in or out. Turning this
on scales that down to a partial size (config.SIZING_PARTIAL_WEIGHT or
config.SIZING_MIN_WEIGHT) when momentum is weak.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import config


@dataclass
class SizingConfig:
    enabled: bool = False
    roc_period: int = config.SIZING_ROC_PERIOD
    full_threshold: float = config.SIZING_ROC_FULL_THRESHOLD
    partial_threshold: float = config.SIZING_ROC_PARTIAL_THRESHOLD
    partial_weight: float = config.SIZING_PARTIAL_WEIGHT
    min_weight: float = config.SIZING_MIN_WEIGHT


def apply_sizing(
    direction: pd.Series,
    ndx_close: pd.Series,
    sizing_config: SizingConfig,
) -> pd.Series:
    """direction is the ±1/0 series from Job 1 + Job 3 (exits.apply_exit_overlay's
    effective_weight). Returns a fractional weight in [-1, 1]: same sign as
    direction, scaled by momentum strength when sizing is enabled.

    Note: sign(result) == direction always -- sizing never flips or clears a
    direction Job 1/Job 3 already decided, it only scales its magnitude.
    """
    if not sizing_config.enabled:
        return direction.copy()

    roc = ndx_close.pct_change(periods=sizing_config.roc_period).abs()
    size = np.select(
        [roc >= sizing_config.full_threshold, roc >= sizing_config.partial_threshold],
        [1.0, sizing_config.partial_weight],
        default=sizing_config.min_weight,
    )
    return direction * pd.Series(size, index=direction.index)
