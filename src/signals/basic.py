import pandas as pd

def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Simple daily returns.
    prices: date x asset
    returns: date x asset
    """
    return prices.pct_change()

def momentum_k(prices: pd.DataFrame, k: int = 20) -> pd.DataFrame:
    """
    Rolling return over past k days (momentum).
    raw_mom[t] uses prices up to t, so we shift by 1 for tradable signal.
    """
    raw = prices.pct_change(k)          # (P_t / P_{t-k} - 1)
    signal = raw.shift(1)               # avoid future leak: trade on t+1
    return signal

def reversal_k(prices: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """
    Short-term reversal: negative of recent k-day return.
    raw_rev[t] = -return over last k days at t, then shift by 1.
    """
    raw = -prices.pct_change(k)
    signal = raw.shift(1)
    return signal