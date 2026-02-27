import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.data.load import load_prices_yfinance
from src.signals.basic import momentum_k
from src.portfolio.weights import (
    make_rank_weights,
    apply_weight_cap,
    portfolio_returns,
    apply_vol_targeting,
)

def main():
    tickers = ["SPY", "QQQ", "IWM", "TLT", "GLD"]
    prices, _ = load_prices_yfinance(tickers, start="2018-01-01")
    rets = prices.pct_change()

    # signal already shifted inside momentum_k (Day3 rule)
    sig = momentum_k(prices, k=20)

    # 1) raw rank weights (long-only top 2 for ETF universe)
    w = make_rank_weights(sig, top_k=2, bottom_k=0)

    # 2) cap single-name weight at 60% (with only 2 names, 10% cap would force too many names)
    w_cap = apply_weight_cap(w, cap=0.60)

    # 3) vol targeting to 10% annual vol
    w_vt = apply_vol_targeting(w_cap, rets, target_vol_annual=0.10, lookback=20, max_leverage=3.0)

    # portfolio returns
    pr = portfolio_returns(w_vt, rets).dropna()
    equity = (1 + pr).cumprod()

    print("Final equity:", float(equity.iloc[-1]))
    print("Ann. vol (approx):", float(pr.std() * np.sqrt(252)))
    print("Max drawdown (approx):", float((equity / equity.cummax() - 1).min()))

    plt.figure()
    plt.plot(equity.index, equity.values)
    plt.title("Equity curve (mom20 → top2 long, cap + vol targeting)")
    plt.xlabel("Date")
    plt.ylabel("Equity (start=1)")
    plt.tight_layout()
    plt.savefig("reports/equity_curve_day4.png", dpi=150)
    print("Saved: reports/equity_curve_day4.png")

if __name__ == "__main__":
    main()