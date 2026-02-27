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

## Signal timing and look-ahead prevention -- future leaking
- Signals are computed using information available up to the close of day *t*.
- Signals are shifted by 1 day (`signal.shift(1)`) so positions decided at *t* are executed on *t+1*.
- PnL is evaluated using returns from *t+1* onward (no using the same-bar price to both compute the signal and execute the trade).
- Baseline assumption: end-of-day signals with next-day execution (close-to-next-close for now).
- Any alternative execution price (next open/VWAP, etc.) must be stated explicitly and used consistently.

## Signal and portfolio design notes
- Signals: momentum_k uses k-day cumulative return; reversal_k uses the negative of recent k-day return.
- Timing: signals are shifted by 1 day to avoid look-ahead; positions decided at t are executed on t+1.
- Portfolio: convert signals to weights via cross-sectional ranking (top-k long; optional bottom-k short), then normalize exposure.
- Risk controls: apply single-name weight cap to limit concentration risk; apply volatility targeting to keep risk more stable across regimes (with leverage cap).

## What this repo does

### Pipeline Outline
```text
DATA (Day2)
┌──────────────────────────────────────────────────────────────┐
│ Input: prices (date × asset)                                 │
│ Checks: missing rate, duplicate dates, monotonic dates, etc. │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
SIGNALS (Day3)
┌──────────────────────────────────────────────────────────────┐
│ raw_signal[t,i] = f(prices up to day t)                      │
│   - momentum_k:  P[t]/P[t-k] - 1                             │
│   - reversal_k: -(P[t]/P[t-k] - 1)                           │
│                                                              │
│ signal = raw_signal.shift(1)                                 │
│ (avoid look-ahead: decide at t, execute at t+1)              │
│ Output: signal (date × asset)                                │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
PORTFOLIO / RISK (Day4)
┌──────────────────────────────────────────────────────────────┐
│ 1) Rank signals → select top-k (optional bottom-k)           │
│ 2) Normalize weights                                         │
│    - long-only: sum(w_t)=1                                   │
│    - long-short: sum(long)=+1, sum(short)=-1                 │
│ 3) Single-name cap (e.g., 10%)                               │
│    - clip |w_t,i| <= cap and renormalize                     │
│ 4) Vol targeting                                             │
│    - r_p,t = Σ_i w_t,i r[t,i]                                │
│    - σ_t = rolling_std(r_p, lookback)                        │
│    - scale_t = σ* / σ_t (with leverage cap)                  │
│    - w'_t = scale_t · w_t                                    │
│ Output: weights (date × asset)                               │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
BACKTEST OUTPUT
┌──────────────────────────────────────────────────────────────┐
│ portfolio_return[t] = Σ_i w'[t,i] r[t,i]                     │
│ equity[t] = Π_{τ≤t} (1 + portfolio_return[τ])                │
│ Outputs: equity curve + basic metrics                        │
└──────────────────────────────────────────────────────────────┘