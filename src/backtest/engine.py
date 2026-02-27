import numpy as np
import pandas as pd

from src.costs.model import trading_cost

def align_inputs(prices: pd.DataFrame, weights: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Align prices and weights on the same dates/assets.
    Returns: (prices_aligned, returns_aligned, weights_aligned)
    """
    prices = prices.sort_index()
    rets = prices.pct_change()

    w, r = weights.align(rets, join="inner", axis=0)
    w, r = w.align(r, join="inner", axis=1)

    return prices.loc[w.index, w.columns], r, w

def portfolio_returns(weights: pd.DataFrame, returns: pd.DataFrame) -> pd.Series:
    """
    Gross portfolio returns:
      r_p,t = sum_i w_t,i * r_t,i
    Assumes weights already represent the position held during day t.
    """
    w, r = weights.align(returns, join="inner", axis=0)
    w, r = w.align(r, join="inner", axis=1)
    return (w * r).sum(axis=1)

def equity_curve(port_ret: pd.Series) -> pd.Series:
    """Equity curve starting at 1.0"""
    port_ret = port_ret.fillna(0.0)
    return (1.0 + port_ret).cumprod()

def max_drawdown(equity: pd.Series) -> float:
    """Max drawdown in decimals (negative number)"""
    peak = equity.cummax()
    dd = equity / peak - 1.0
    return float(dd.min())

def summary_stats(
    gross_ret: pd.Series,
    net_ret: pd.Series,
    turnover: pd.Series,
    trading_cost: pd.Series,
) -> dict:
    """
    Basic metrics. Returns a dict of scalars.
    """
    def ann_return(r: pd.Series) -> float:
        eq = equity_curve(r)
        n = len(eq)
        if n == 0:
            return np.nan
        return float(eq.iloc[-1] ** (252 / n) - 1)

    def ann_vol(r: pd.Series) -> float:
        return float(r.std() * np.sqrt(252))

    out = {
        "ann_return_gross": ann_return(gross_ret),
        "ann_return_net": ann_return(net_ret),
        "ann_vol_gross": ann_vol(gross_ret),
        "ann_vol_net": ann_vol(net_ret),
        "max_dd_gross": max_drawdown(equity_curve(gross_ret)),
        "max_dd_net": max_drawdown(equity_curve(net_ret)),
        "avg_turnover": float(turnover.mean()),
        "avg_cost_daily": float(trading_cost.mean()),
        "cost_share": float(trading_cost.sum() / (gross_ret.abs().sum() + 1e-12)),
    }
    return out

def run_backtest(
    prices: pd.DataFrame,
    weights: pd.DataFrame,
    fee_bps: float = 1.0,
    slippage_bps: float = 5.0,
) -> dict:
    """
    Run a simple backtest producing gross/net returns and equity curves.
    """
    _, rets, w = align_inputs(prices, weights)

    gross = portfolio_returns(w, rets)
    cost = trading_cost(w, fee_bps=fee_bps, slippage_bps=slippage_bps)

    # align cost to gross return index
    cost = cost.reindex(gross.index).fillna(0.0)

    net = gross - cost

    eq_gross = equity_curve(gross)
    eq_net = equity_curve(net)

    # turnover for reporting
    from src.costs.model import turnover as turnover_fn
    to = turnover_fn(w).reindex(gross.index).fillna(0.0)

    stats = summary_stats(gross, net, to, cost)

    return {
        "gross_ret": gross,
        "net_ret": net,
        "cost": cost,
        "turnover": to,
        "equity_gross": eq_gross,
        "equity_net": eq_net,
        "stats": stats,
    }