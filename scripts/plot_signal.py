import matplotlib.pyplot as plt

from src.data.load import load_prices_yfinance
from src.signals.basic import momentum_k

def main():
    tickers = ["SPY", "QQQ", "IWM", "TLT", "GLD"]
    prices, _ = load_prices_yfinance(tickers, start="2018-01-01")

    sig = momentum_k(prices, k=20)
    s = sig["SPY"].dropna()

    plt.figure()
    plt.plot(s.index, s.values)
    plt.title("SPY momentum_20 (shifted by 1 day)")
    plt.xlabel("Date")
    plt.ylabel("Signal (20-day return)")
    plt.tight_layout()
    plt.savefig("reports/signal_spy_mom20.png", dpi=150)
    print("Saved plot to reports/signal_spy_mom20.png")

if __name__ == "__main__":
    main()