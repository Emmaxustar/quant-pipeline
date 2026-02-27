import numpy as np
import pandas as pd

def turnover(weights: pd.DataFrame) -> pd.Series:
    """
    Turnover_t = 0.5 * sum_i |w_t,i - w_{t-1,i}|
    - weights: date x asset
    - returns: Series indexed by date
    """
    w = weights.fillna(0.0)
    dw = w.diff()  # w_t - w_{t-1}
    to = 0.5 * dw.abs().sum(axis=1)
    return to

def trading_cost(
    weights: pd.DataFrame,
    fee_bps: float = 1.0,
    slippage_bps: float = 5.0,
) -> pd.Series:
    """
    Simple cost model:
      cost_t = fee + slippage * turnover_t
    where fee_bps/slippage_bps are in basis points.
    Returns cost as a daily return drag (decimal).
    """
    to = turnover(weights)
    fee = fee_bps / 1e4
    slip = slippage_bps / 1e4
    cost = fee + slip * to
    return cost