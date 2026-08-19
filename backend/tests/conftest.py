"""Synthetic price fixtures.

Yahoo Finance is not reachable from this sandbox (org egress policy), so all
backtest/signal tests run against a deterministic, seeded synthetic dataset
instead of live data. This validates the math, not real-world returns --
Track A conviction still requires running against real TQQQ/SQQQ/^NDX data
somewhere with network access.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


def _make_synthetic_dataset(n_days: int = 600, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2010-01-04", periods=n_days)

    # A slow sinusoidal trend (so the 250d MA crosses more than once) plus
    # small daily noise, so the index isn't perfectly monotonic.
    t = np.arange(n_days)
    trend = 100 * np.sin(2 * np.pi * t / 300)
    noise = rng.normal(0, 0.3, n_days).cumsum() * 0.2
    ndx = 1000 + trend * 5 + noise
    ndx = np.maximum(ndx, 50)  # keep strictly positive

    ndx_ret = pd.Series(ndx).pct_change().fillna(0.0).to_numpy()

    daily_fee = 0.0003  # crude expense-drag stand-in, just to avoid a toy 3x-with-no-cost fixture
    tqqq_ret = 3 * ndx_ret - daily_fee
    sqqq_ret = -3 * ndx_ret - daily_fee

    tqqq = 50 * np.cumprod(1 + tqqq_ret)
    sqqq = 50 * np.cumprod(1 + sqqq_ret)
    qqq = 100 * np.cumprod(1 + ndx_ret)

    df = pd.DataFrame(
        {"ndx": ndx, "tqqq": tqqq, "sqqq": sqqq, "qqq": qqq},
        index=dates,
    )
    df.index.name = "Date"
    return df


@pytest.fixture
def synthetic_dataset() -> pd.DataFrame:
    return _make_synthetic_dataset()
