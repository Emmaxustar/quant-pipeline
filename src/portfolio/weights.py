import numpy as np
import pandas as pd

def make_rank_weights(
    signal: pd.DataFrame,
    top_k: int = 2,
    bottom_k: int = 0,
) -> pd.DataFrame:
    """
    Convert signal(date x asset) to weights(date x asset) by cross-sectional ranking.
    - If bottom_k == 0: long-only top_k, equal weight, sum(weights)=1 on each date.
    - If bottom_k > 0: long top_k, short bottom_k, equal weight within each side,
      long sums to +1 and short sums to -1 (net 0).
    """
    weights = pd.DataFrame(0.0, index=signal.index, columns=signal.columns)

    for dt, row in signal.iterrows():
        s = row.dropna()
        if s.empty:
            continue

        ranked = s.sort_values(ascending=False)
        longs = ranked.head(top_k).index

        if bottom_k > 0:
            shorts = ranked.tail(bottom_k).index
            weights.loc[dt, longs] = 1.0 / len(longs)
            weights.loc[dt, shorts] = -1.0 / len(shorts)
        else:
            weights.loc[dt, longs] = 1.0 / len(longs)

    return weights


def apply_weight_cap(weights: pd.DataFrame, cap: float = 0.10) -> pd.DataFrame:
    """
    Cap absolute position weight by `cap` and renormalize to preserve gross exposure:
    - long-only: keep sum(weights)=1
    - long-short: keep sum(long)=+1 and sum(short)=-1 (preserve each side)
    """
    w = weights.copy()

    def _cap_and_renorm(vec: pd.Series) -> pd.Series:
        if vec.abs().sum() == 0:
            return vec

        # long-only vs long-short detection by sign
        pos = vec[vec > 0]
        neg = vec[vec < 0]

        # cap long side
        if len(pos) > 0:
            pos_capped = pos.clip(upper=cap)
            if pos_capped.sum() > 0:
                pos_capped = pos_capped / pos_capped.sum()  # renorm to sum=1
            vec.loc[pos.index] = pos_capped

        # cap short side (negative)
        if len(neg) > 0:
            neg_capped = neg.clip(lower=-cap)  # closer to 0 is higher, so lower=-cap
            if neg_capped.abs().sum() > 0:
                neg_capped = neg_capped / neg_capped.abs().sum()  # renorm abs sum=1
                neg_capped = -neg_capped.abs()  # ensure negative
            vec.loc[neg.index] = neg_capped

        return vec

    w = w.apply(_cap_and_renorm, axis=1)
    return w


def portfolio_returns(weights: pd.DataFrame, returns: pd.DataFrame) -> pd.Series:
    """
    Compute portfolio daily returns using weights decided at date t applied to returns at t.
    Assumes weights are already shifted appropriately in the signal layer.
    """
    aligned_w, aligned_r = weights.align(returns, join="inner", axis=0)
    aligned_w, aligned_r = aligned_w.align(aligned_r, join="inner", axis=1)
    return (aligned_w * aligned_r).sum(axis=1)


def apply_vol_targeting(
    weights: pd.DataFrame,
    returns: pd.DataFrame,
    target_vol_annual: float = 0.10,
    lookback: int = 20,
    max_leverage: float = 3.0,
) -> pd.DataFrame:
    """
    Scale weights by inverse of rolling realized vol to target a stable risk level.
    - target_vol_annual: e.g. 10% annualized
    - lookback: rolling window for realized vol
    - max_leverage: cap scaling to avoid extreme leverage in low-vol periods
    """
    # convert annual target to daily
    target_vol_daily = target_vol_annual / np.sqrt(252)

    port_ret = portfolio_returns(weights, returns)
    realized_vol = port_ret.rolling(lookback).std()

    scale = target_vol_daily / realized_vol
    scale = scale.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    scale = scale.clip(upper=max_leverage)

    scaled_weights = weights.mul(scale, axis=0)
    return scaled_weights