from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

import pandas as pd


@dataclass
class DataChecksResult:
    missing_rate_by_asset: pd.Series
    has_duplicate_dates: bool
    is_monotonic_increasing: bool
    has_extreme_returns: bool
    extreme_returns_top: pd.Series


def _validate_prices(prices: pd.DataFrame) -> DataChecksResult:
    """
    prices: index=DatetimeIndex (trading dates), columns=assets, values=adjusted close prices
    """
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise TypeError("prices.index must be a DatetimeIndex")

    has_duplicate_dates = prices.index.duplicated().any()
    is_monotonic_increasing = prices.index.is_monotonic_increasing

    missing_rate_by_asset = prices.isna().mean().sort_values(ascending=False)

    # --- extreme returns flag ---
    rets = prices.pct_change()

    # pick a threshold (50% is a common "something is wrong" flag for ETFs)
    threshold = 0.5

    # True/False mask where returns are extreme
    extreme_mask = rets.abs() > threshold
    has_extreme_returns = bool(extreme_mask.any().any())

    # Show top 10 extreme moves (flatten date x asset into a Series)
    extreme_top = (
        rets.stack()
        .loc[lambda s: s.abs() > threshold]
        .abs()
        .sort_values(ascending=False)
        .head(10)
    )
    return DataChecksResult(
        missing_rate_by_asset=missing_rate_by_asset,
        has_duplicate_dates=bool(has_duplicate_dates),
        is_monotonic_increasing=bool(is_monotonic_increasing),
        has_extreme_returns=has_extreme_returns,
        extreme_returns_top=extreme_top,
    )


def load_prices_yfinance(
    tickers: Iterable[str],
    start: str = "2018-01-01",
    end: Optional[str] = None,
    use_adjusted_close: bool = True,
) -> Tuple[pd.DataFrame, DataChecksResult]:
    """
    Returns:
      prices: DataFrame with shape (date x asset)
      checks: basic data validation results
    """
    tickers_list: List[str] = list(tickers)
    if len(tickers_list) == 0:
        raise ValueError("tickers is empty")

    import yfinance as yf  # local import so repo doesn't break if yfinance not installed

    df = yf.download(
        tickers_list,
        start=start,
        end=end,
        auto_adjust=False,
        progress=False,
        group_by="column",
    )

    # yfinance returns different shapes depending on number of tickers
    # MultiIndex columns for multiple tickers: (field, ticker)
    # SingleIndex for one ticker: fields only
    if isinstance(df.columns, pd.MultiIndex):
        field = "Adj Close" if use_adjusted_close else "Close"
        prices = df[field].copy()
    else:
        # single ticker case
        field = "Adj Close" if use_adjusted_close else "Close"
        prices = df[[field]].copy()
        prices.columns = tickers_list

    prices.index = pd.to_datetime(prices.index)
    prices = prices.sort_index()

    checks = _validate_prices(prices)

    return prices, checks


def save_prices_csv(prices: pd.DataFrame, path: str) -> None:
    """
    Save prices to csv with date index.
    """
    prices.to_csv(path, index=True)
