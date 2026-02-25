# quant-pipeline

This repo is for building a reproducible quant research pipeline. The plan is to get a minimal end-to-end workflow working first, then add realism and rigor step by step.

## Goal
**signal → portfolio → cost → report**

- **Signal**: compute a signal (factor/indicator) from data  
- **Portfolio**: turn the signal into positions (selection, weights, rebalance rules)  
- **Cost**: include transaction costs and slippage assumptions  
- **Report**: output plots and core metrics for review and comparison

## Repo structure
- `src/` core logic (signals / portfolio / costs / reporting)
- `configs/` YAML configs (experiment parameters in one place)
- `scripts/` runnable entry points (CLI scripts)
- `tests/` unit tests (pytest)
- `data/` local data (not tracked by default)
- `reports/` outputs (plots / tables / reports)

## Quickstart

### 1) Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Run (placeholders for now)
```bash
# python scripts/run_backtest.py --config configs/backtest.yaml
# python scripts/make_report.py  --config configs/report.yaml
```

## Pitfalls to Avoid
- Future leak: using information that was not available at the decision time
- Survivorship bias: restricting the universe to only assets that “survived” to today
- Timing / alignment errors: misaligning signal timestamps and return windows
- Overfitting / data snooping: repeatedly tuning on the same sample and expecting it to generalize

## How I avoid future leak (timing assumption)
- I compute signals using data available up to the close of day *t*.
- I shift signals by 1 day (`signal.shift(1)`) so the position decided at *t* is traded on *t+1*.
- I evaluate PnL using returns from *t+1* (no using same-bar prices to both decide and trade).
- This repo assumes end-of-day signals and next-day execution (close-to-next-close baseline for now).
- Any other assumption (next-open, VWAP, etc.) will be stated explicitly in configs and kept consistent.

## Milestones
- Day2: minimal backtest (load data → signal → positions → equity curve)
- Day3: add a cost model + basic metrics (Sharpe / max drawdown / turnover) + a simple report
- Later: experiment management via configs and more rigorous validation (e.g., quantile backtests, IC, cross-sectional regressions)