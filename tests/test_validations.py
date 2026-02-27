import numpy as np
import pandas as pd

from src.data.load import _validate_prices
from src.portfolio.weights import apply_weight_cap


def test_prices_validation_datetime_and_monotonic():
    # build a simple prices df with proper datetime index
    idx = pd.date_range("2020-01-01", periods=5, freq="D")
    prices = pd.DataFrame(
        {"A": [100, 101, 102, 103, 104], "B": [50, 50.5, 51, 51.5, 52]},
        index=idx,
    )

    checks = _validate_prices(prices)
    assert checks.is_monotonic_increasing is True
    assert checks.has_duplicate_dates is False
    # missing should be zero
    assert float(checks.missing_rate_by_asset.max()) == 0.0


def test_weight_cap_preserves_sum_long_only():
    idx = pd.date_range("2020-01-01", periods=1, freq="D")
    w = pd.DataFrame({"A": [0.8], "B": [0.1], "C": [0.1]}, index=idx)

    capped = apply_weight_cap(w, cap=0.5)

    # long-only still sums to 1
    assert np.isclose(capped.sum(axis=1).iloc[0], 1.0)

    # cap should reduce concentration relative to original
    assert capped.abs().max(axis=1).iloc[0] < w.abs().max(axis=1).iloc[0]