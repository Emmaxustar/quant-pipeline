import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def _drawdown(equity: pd.Series) -> pd.Series:
    peak = equity.cummax()
    return equity / peak - 1.0


def make_report(run_dir: str | Path, results: dict) -> None:
    """
    Save plots + tables into run_dir.
    results should contain:
      equity_gross, equity_net, gross_ret, net_ret, turnover, cost, stats, weights(optional)
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    eq_g = results["equity_gross"]
    eq_n = results["equity_net"]
    gross = results["gross_ret"]
    net = results["net_ret"]
    to = results["turnover"]
    cost = results["cost"]
    stats = results["stats"]
    weights = results.get("weights", None)

    # ---------- 1) Equity (gross vs net) ----------
    plt.figure()
    plt.plot(eq_g.index, eq_g.values, label="gross")
    plt.plot(eq_n.index, eq_n.values, label="net")
    plt.title("Equity curve (gross vs net)")
    plt.xlabel("Date")
    plt.ylabel("Equity (start=1)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(run_dir / "equity_gross_vs_net.png", dpi=150)

    # ---------- 2) Drawdown ----------
    dd_g = _drawdown(eq_g)
    dd_n = _drawdown(eq_n)

    plt.figure()
    plt.plot(dd_g.index, dd_g.values, label="gross")
    plt.plot(dd_n.index, dd_n.values, label="net")
    plt.title("Drawdown (gross vs net)")
    plt.xlabel("Date")
    plt.ylabel("Drawdown")
    plt.legend()
    plt.tight_layout()
    plt.savefig(run_dir / "drawdown_gross_vs_net.png", dpi=150)

    # ---------- 3) Turnover + Cost ----------
    plt.figure()
    plt.plot(to.index, to.values, label="turnover")
    plt.title("Daily turnover")
    plt.xlabel("Date")
    plt.ylabel("Turnover")
    plt.tight_layout()
    plt.savefig(run_dir / "turnover.png", dpi=150)

    plt.figure()
    plt.plot(cost.index, cost.values, label="cost")
    plt.title("Daily trading cost (return drag)")
    plt.xlabel("Date")
    plt.ylabel("Cost")
    plt.tight_layout()
    plt.savefig(run_dir / "cost.png", dpi=150)

    # ---------- 4) Exposure / weights distribution ----------
    if weights is not None:
        # Net and gross exposure over time
        net_exp = weights.sum(axis=1)
        gross_exp = weights.abs().sum(axis=1)

        plt.figure()
        plt.plot(net_exp.index, net_exp.values, label="net")
        plt.plot(gross_exp.index, gross_exp.values, label="gross")
        plt.title("Exposure over time")
        plt.xlabel("Date")
        plt.ylabel("Exposure")
        plt.legend()
        plt.tight_layout()
        plt.savefig(run_dir / "exposure.png", dpi=150)

        # Histogram of weights (sample across all dates/assets)
        w_flat = weights.stack().dropna()
        plt.figure()
        plt.hist(w_flat.values, bins=60)
        plt.title("Weights distribution")
        plt.xlabel("Weight")
        plt.ylabel("Count")
        plt.tight_layout()
        plt.savefig(run_dir / "weights_hist.png", dpi=150)

    # ---------- 5) Save tables ----------
    pd.DataFrame({"gross_ret": gross, "net_ret": net, "turnover": to, "cost": cost}).to_csv(
        run_dir / "timeseries.csv"
    )

    with open(run_dir / "stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    # small human-readable summary
    with open(run_dir / "summary.txt", "w") as f:
        for k, v in stats.items():
            try:
                f.write(f"{k}: {v:.6f}\n")
            except Exception:
                f.write(f"{k}: {v}\n")