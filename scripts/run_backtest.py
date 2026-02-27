import argparse
from datetime import datetime
from pathlib import Path

import yaml

from src.data.load import load_prices_yfinance
from src.signals.basic import momentum_k, reversal_k
from src.portfolio.weights import make_rank_weights, apply_weight_cap, apply_vol_targeting
from src.backtest.engine import run_backtest
from src.report.make_report import make_report


def build_signal(prices, cfg):
    name = cfg["name"]
    k = int(cfg.get("k", 20))
    if name == "momentum":
        return momentum_k(prices, k=k)
    if name == "reversal":
        return reversal_k(prices, k=k)
    raise ValueError(f"Unknown signal name: {name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to YAML config, e.g. configs/backtest.yaml")
    args = parser.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())

    # ---------- data ----------
    tickers = cfg["data"]["tickers"]
    start = cfg["data"].get("start", "2018-01-01")

    prices, _ = load_prices_yfinance(tickers, start=start)

    # ---------- signal (Day3) ----------
    signal = build_signal(prices, cfg["signal"])

    # ---------- portfolio weights (Day4) ----------
    top_k = int(cfg["portfolio"].get("top_k", 2))
    bottom_k = int(cfg["portfolio"].get("bottom_k", 0))
    cap = float(cfg["portfolio"].get("cap", 0.60))

    w = make_rank_weights(signal, top_k=top_k, bottom_k=bottom_k)
    w = apply_weight_cap(w, cap=cap)

    # vol targeting needs returns
    rets = prices.pct_change()
    vt = cfg["risk"]
    w = apply_vol_targeting(
        w,
        rets,
        target_vol_annual=float(vt.get("vol_target_annual", 0.10)),
        lookback=int(vt.get("vol_lookback", 20)),
        max_leverage=float(vt.get("max_leverage", 3.0)),
    )

    # ---------- costs + backtest engine (Day5) ----------
    fee_bps = float(cfg["costs"].get("fee_bps", 1.0))
    slippage_bps = float(cfg["costs"].get("slippage_bps", 5.0))

    results = run_backtest(prices, w, fee_bps=fee_bps, slippage_bps=slippage_bps)
    results["weights"] = w  # for report plots

    # ---------- output directory ----------
    run_tag = datetime.now().strftime("run_%Y%m%d")
    run_dir = Path("reports") / run_tag
    run_dir.mkdir(parents=True, exist_ok=True)

    # ---------- report ----------
    make_report(run_dir, results)

    print(f"Saved report to: {run_dir}")


if __name__ == "__main__":
    main()