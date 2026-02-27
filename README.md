# Quant-pipeline

A reproducible quant research pipeline: **data → signals → portfolio/risk → costs → report**.

The goal is to get a minimal end-to-end workflow working first, then add realism and rigor step by step.

---

## Goal
**signal → portfolio → cost → report**

- **Signal**: compute a signal (factor/indicator) from data  
- **Portfolio**: convert signals into positions (selection, weights, rebalance rules)  
- **Cost**: model turnover-based transaction costs and slippage  
- **Report**: save plots + core metrics for review and comparison  

---

## Repo structure
- `src/` core library code
  - `src/data/` loaders + data validation checks
  - `src/signals/` signal definitions
  - `src/portfolio/` portfolio construction + risk controls
  - `src/costs/` cost model (turnover + fees/slippage)
  - `src/backtest/` backtest engine (gross vs net)
  - `src/report/` report generator (plots + tables)
- `configs/` YAML configs (experiment parameters)
- `scripts/` runnable entry points (CLI scripts)
- `tests/` unit tests (pytest)
- `data/` local data cache (not tracked)
- `reports/` output artifacts (plots / tables / runs)

---

## Quickstart

### 1) Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Config-driven Run
```bash
export PYTHONPATH=$(pwd)
python scripts/run_backtest.py --config configs/backtest.yaml
```

### 3) Test
```bash
pytest -q
```

## What this repo does

### Pipeline Outline
```text
DATA
┌──────────────────────────────────────────────────────────────┐
│ Input: prices (date × asset)                                 │
│ Checks: missing rate, duplicate dates, monotonic dates, etc. │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
SIGNALS
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
PORTFOLIO / RISK
┌──────────────────────────────────────────────────────────────┐
│ 1) Rank signals → select top-k (optional bottom-k)           │
│ 2) Normalize weights                                         │
│    - long-only: sum(w_t)=1                                   │
│    - long-short: sum(long)=+1, sum(short)=-1                 │
│ 3) Single-name cap                                           │
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
COSTS + BACKTEST
┌──────────────────────────────────────────────────────────────┐
│ gross: r_p,t = Σ_i w_t,i r[t,i]                              │
│ turnover: 0.5 * Σ_i |w_t,i - w_{t-1,i}|                      │
│ cost: fee_bps/1e4 + (slippage_bps/1e4) * turnover            │
│ net: r_net,t = r_gross,t - cost_t                            │
│ Output: gross vs net equity + metrics                        │
└──────────────────────────────────────────────────────────────┘
                │
                ▼
REPORT
┌──────────────────────────────────────────────────────────────┐
│ Auto-generated plots + stats saved under reports/run_*/      │
└──────────────────────────────────────────────────────────────┘
```

## Backtest validity (avoid future leak)
- Signals are computed using information available up to the close of day *t*.
- Signals are shifted by 1 day (`signal.shift(1)`) so positions decided at *t* are executed on *t+1*.
- PnL is evaluated using returns from *t+1* onward (no using the same-bar price to both compute the signal and execute the trade).
- Baseline assumption: end-of-day signals with next-day execution (close-to-next-close for now).
- Any alternative execution price (next open/VWAP, etc.) must be stated explicitly and used consistently.

## Cost model
- Turnover: `0.5 * sum(|w_t - w_{t-1}|)` per day.
- Daily cost (bps): `fee_bps/1e4 + (slippage_bps/1e4) * turnover`.
- Net returns are computed as `gross - cost`.

## Risk control
- **Single-name cap** limits concentration risk so one name cannot dominate portfolio PnL.
- **Vol targeting** scales exposure using rolling realized volatility to keep risk more stable across regimes (with a leverage cap).

## Notes
- Data source: yfinance (prototype). A production setup would use a vendor feed with explicit corporate-action handling.
- Current signals are intentionally simple: momentum/reversal so the pipeline and assumptions are easy to audit.