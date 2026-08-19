import pandas as pd

from app.signals import compute_signal


def test_target_weight_is_cash_during_warmup():
    # ma_slow needs 3 points; with ma_fast=2, ma_slow=3 the first 2 rows can't
    # have a slow MA yet and must be forced to cash regardless of price.
    close = pd.Series([100, 200, 300, 400, 500], index=pd.bdate_range("2020-01-01", periods=5))
    sig = compute_signal(close, ma_fast=2, ma_slow=3)
    assert sig["target_weight"].iloc[0] == 0.0
    assert sig["target_weight"].iloc[1] == 0.0


def test_target_weight_hand_computed():
    # ma_fast=2, ma_slow=3 on a tiny deterministic series so every rolling
    # mean can be checked by hand.
    close = pd.Series([10, 10, 10, 13, 16, 4, 4], index=pd.bdate_range("2020-01-01", periods=7))
    sig = compute_signal(close, ma_fast=2, ma_slow=3)

    # idx3: close=13, ma_fast=(10+13)/2=11.5, ma_slow=(10+10+13)/3=11. 13>11.5 and 13>11 -> up
    assert sig["target_weight"].iloc[3] == 1.0
    # idx4: close=16, ma_fast=(13+16)/2=14.5, ma_slow=(10+13+16)/3=13. 16>both -> up
    assert sig["target_weight"].iloc[4] == 1.0
    # idx5: close=4, ma_fast=(16+4)/2=10, ma_slow=(13+16+4)/3=11. 4<both -> down
    assert sig["target_weight"].iloc[5] == -1.0
    # idx6: close=4, ma_fast=(4+4)/2=4, ma_slow=(16+4+4)/3=8. 4==ma_fast (not strictly below) -> cash
    assert sig["target_weight"].iloc[6] == 0.0


def test_target_weight_only_takes_expected_values():
    close = pd.Series(range(1, 301), index=pd.bdate_range("2020-01-01", periods=300)).astype(float)
    sig = compute_signal(close)
    assert set(sig["target_weight"].unique()).issubset({-1.0, 0.0, 1.0})
    # a strictly increasing series should eventually flip to uptrend once both MAs are defined
    assert sig["target_weight"].iloc[-1] == 1.0
