from src.data.load import load_prices_yfinance, _validate_prices as validate_prices

def main():
    tickers = ["SPY", "QQQ", "IWM", "TLT", "GLD"]

    # loader returns (prices, checks) in our setup
    prices, _ = load_prices_yfinance(tickers, start="2018-01-01")

    # --- sanity checks (confirm yfinance data looks real) ---
    print("=== Sanity checks ===")
    print("shape:", prices.shape)
    print("columns:", list(prices.columns))
    print("date range:", prices.index.min(), "->", prices.index.max())
    print("\nhead:\n", prices.head(3))
    print("\ntail:\n", prices.tail(3))

    # simple plausibility checks
    rets = prices.pct_change()
    print("\nmax abs daily return:", rets.abs().max().max())
    print("min price:", prices.min().min())
    print("non-positive prices:", int((prices <= 0).sum().sum()))

    # --- required data validations ---
    checks = validate_prices(prices)
    print("\n=== Data checks ===")
    print("Has duplicate dates:", checks.has_duplicate_dates)
    print("Is monotonic increasing:", checks.is_monotonic_increasing)
    print("\nMissing rate by asset:")
    print(checks.missing_rate_by_asset)

if __name__ == "__main__":
    main()