import pandas as pd

from src.data.load import load_prices_yfinance
from src.signals.basic import momentum_k, reversal_k

def main():
    tickers = ["SPY", "QQQ", "IWM", "TLT", "GLD"]
    prices, _ = load_prices_yfinance(tickers, start="2018-01-01")

    mom20 = momentum_k(prices, k=20)
    rev5  = reversal_k(prices, k=5)

    print("prices shape:", prices.shape)
    print("mom20 shape:", mom20.shape, "nan rate:", mom20.isna().mean().mean())
    print("rev5  shape:", rev5.shape,  "nan rate:", rev5.isna().mean().mean())

    # Save for later modules (do not commit data/ to GitHub)
    mom20.to_csv("data/signal_mom20.csv")
    rev5.to_csv("data/signal_rev5.csv")
    print("Saved signals to data/")

if __name__ == "__main__":
    main()