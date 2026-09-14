import pandas as pd

from app.sizing import SizingConfig, apply_sizing


def test_sizing_disabled_returns_direction_unchanged():
    idx = pd.bdate_range("2020-01-01", periods=5)
    direction = pd.Series([1.0, 1.0, -1.0, 0.0, 1.0], index=idx)
    close = pd.Series([100, 110, 90, 90, 95], index=idx)

    result = apply_sizing(direction, close, SizingConfig(enabled=False))

    pd.testing.assert_series_equal(result, direction)


def test_sizing_full_weight_when_roc_strong():
    idx = pd.bdate_range("2020-01-01", periods=3)
    direction = pd.Series([1.0, 1.0, 1.0], index=idx)
    # roc period=1: close[1]/close[0]-1 = 0.20 (strong) -> full weight
    close = pd.Series([100, 120, 121], index=idx)
    cfg = SizingConfig(enabled=True, roc_period=1, full_threshold=0.10, partial_threshold=0.03)

    result = apply_sizing(direction, close, cfg)

    assert result.iloc[1] == 1.0  # direction 1 * full size 1.0


def test_sizing_partial_weight_when_roc_moderate():
    idx = pd.bdate_range("2020-01-01", periods=3)
    direction = pd.Series([1.0, 1.0, 1.0], index=idx)
    # roc[1] = 105/100 - 1 = 0.05 -> between partial (0.03) and full (0.10) thresholds
    close = pd.Series([100, 105, 105], index=idx)
    cfg = SizingConfig(
        enabled=True, roc_period=1, full_threshold=0.10, partial_threshold=0.03, partial_weight=0.65
    )

    result = apply_sizing(direction, close, cfg)

    assert result.iloc[1] == 0.65


def test_sizing_min_weight_when_roc_weak():
    idx = pd.bdate_range("2020-01-01", periods=3)
    direction = pd.Series([1.0, 1.0, 1.0], index=idx)
    close = pd.Series([100, 100.5, 100.5], index=idx)  # roc[1] = 0.005, weak
    cfg = SizingConfig(enabled=True, roc_period=1, min_weight=0.30)

    result = apply_sizing(direction, close, cfg)

    assert result.iloc[1] == 0.30


def test_sizing_never_flips_sign_or_leaves_cash():
    idx = pd.bdate_range("2020-01-01", periods=4)
    direction = pd.Series([1.0, -1.0, 0.0, -1.0], index=idx)
    close = pd.Series([100, 200, 50, 10], index=idx)  # huge ROC swings
    cfg = SizingConfig(enabled=True, roc_period=1)

    result = apply_sizing(direction, close, cfg)

    assert (result.apply(lambda x: 0 if x == 0 else (1 if x > 0 else -1)) == direction).all()
    assert result.iloc[2] == 0.0  # cash stays cash regardless of ROC
