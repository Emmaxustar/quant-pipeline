import numpy as np
import matplotlib.pyplot as plt

from src.data.load import load_prices_yfinance
from src.signals.basic import momentum_k
from src.portfolio.weights import make_rank_weights, apply_weight_cap, apply_vol_targeting
from src.backtest.engine import run_backtest

def main():
    tickers = ["SPY", "QQQ", "IWM", "TLT", "GLD"]
    prices, _ = load_prices_yfinance(tickers, start="2018-01-01")

    # Day3 signal (shift inside)
    sig = momentum_k(prices, k=20)

    # Day4 weights (top2 long-only for ETF demo)
    w = make_rank_weights(sig, top_k=2, bottom_k=0)
    w = apply_weight_cap(w, cap=0.60)

    # returns needed for vol targeting
    rets = prices.pct_change()
    w = apply_vol_targeting(w, rets, target_vol_annual=0.10, lookback=20, max_leverage=3.0)

    # Day5 backtest with costs
    res = run_backtest(prices, w, fee_bps=1.0, slippage_bps=5.0)

    print("=== Stats ===")
    for k, v in res["stats"].items():
        print(f"{k}: {v:.4f}")

    # plot both curves
    eq_g = res["equity_gross"]
    eq_n = res["equity_net"]

    plt.figure()
    plt.plot(eq_g.index, eq_g.values, label="gross")
    plt.plot(eq_n.index, eq_n.values, label="net")
    plt.title("Equity curve: gross vs net (with costs)")
    plt.xlabel("Date")
    plt.ylabel("Equity (start=1)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("reports/equity_gross_vs_net.png", dpi=150)
    print("Saved: reports/equity_gross_vs_net.png")

if __name__ == "__main__":
    main()