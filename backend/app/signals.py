"""Job 1: entry/direction signal.

Simple trend rule on the underlying index (^NDX): price above BOTH the fast
(50d) and slow (250d) moving average -> trend up -> target TQQQ. Price below
BOTH -> trend down -> target SQQQ. Anything mixed (price between the two MAs,
or not enough history yet to compute the slow MA) -> target cash.

This function is also the strategy's exit rule for the MVP: there is no
separate "close the position" logic yet -- you exit a position the same day
the trend flips against you. Job 2 (sizing) and Job 3 (a faster/smarter exit)
are meant to layer on top of `target_weight` later without changing this
function's contract: it always returns a weight in {-1, 0, +1} per day.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


def compute_signal(
    ndx_close: pd.Series,
    ma_fast: int = config.MA_FAST,
    ma_slow: int = config.MA_SLOW,
) -> pd.DataFrame:
    df = pd.DataFrame(index=ndx_close.index)
    df["close"] = ndx_close
    df["ma_fast"] = ndx_close.rolling(ma_fast).mean()
    df["ma_slow"] = ndx_close.rolling(ma_slow).mean()

    trend_up = (df["close"] > df["ma_fast"]) & (df["close"] > df["ma_slow"])
    trend_down = (df["close"] < df["ma_fast"]) & (df["close"] < df["ma_slow"])

    df["target_weight"] = np.select(
        [trend_up, trend_down],
        [1.0, -1.0],
        default=0.0,
    )
    # Not enough history for the slow MA yet -> no real signal, force cash.
    df.loc[df["ma_slow"].isna(), "target_weight"] = 0.0

    return df
