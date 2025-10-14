# SPY LEAPS Liquidation & Backtest Specification

**Purpose:**
Create a reproducible Python application to backtest and monitor a weekly SPY LEAPS (1-year expiry) accumulation strategy with configurable liquidation rules (drawdown + trend + volatility confirmation). The app will use local SQLite for storage and Streamlit for an interactive dashboard. It will support backtesting, sensitivity analysis, and live signal generation (paper-trade mode).

---

## 1. High-level requirements

* **Language / stack:** Python 3.10+; Streamlit for UI; SQLite for local persistence; pandas, numpy, ta (technical analysis helpers), yfinance (or user-provided CSV) for historical data; optionally `py_vollib` or Black-Scholes functions for synthetic option pricing.
* **Primary goals:**

  * Implement weekly LEAPS buy schedule.
  * Implement configurable stop/liquidation rules (percent drawdown from recent high, moving average breaks, optional volatility gating with VIX).
  * Backtest historical performance and run scenario/sensitivity analyses.
  * Provide exportable reports (CSV, PNG charts) and simple paper-trade signal output.
* **Non-goals:** Live brokerage execution (not included). Production-grade scaling or cloud hosting (local app only).

---

## 2. Data Model & Storage (SQLite)

### Schema (suggested)

* `prices` (daily SPY price history)

  * `date` TEXT PRIMARY KEY (ISO date)
  * `open`, `high`, `low`, `close`, `adj_close`, `volume` REAL

* `vix` (optional) — same structure as prices for symbol ^VIX

* `trades` (backtest trades / simulated positions)

  * `id` INTEGER PRIMARY KEY AUTOINCREMENT
  * `entry_date` TEXT
  * `exit_date` TEXT
  * `entry_price` REAL (underlying SPY price at entry)
  * `exit_price` REAL
  * `option_strike` REAL
  * `option_entry_premium` REAL
  * `option_exit_premium` REAL
  * `contracts` INTEGER
  * `pnl` REAL
  * `notes` TEXT

* `config` (strategy run metadata)

  * `run_id` TEXT PRIMARY KEY
  * `created_at` TEXT
  * `params` JSON

* `signals` (generated signals: pause buys, liquidate, resume)

  * `date` TEXT
  * `signal_type` TEXT
  * `details` TEXT

### Storage rationale

* SQLite is lightweight, easy to backup, and supports queries for analysis. Use SQLAlchemy or `sqlite3` for access.

---

## 3. Strategy Rules & Parameters

### Weekly buy behaviour

* **Buy cadence:** every week on a configurable weekday (default: Friday close).
* **Position sizing:** fixed capital per week (e.g., $1000) or percent of portfolio; parameterize `weekly_amount`.
* **Option selection:** choose strikes relative to spot: ATM, 5% OTM, or custom. Default: **ATM** (closest strike) for 1-year expiry.
* **Option model:** use historic option premiums if available, or synthetic Black-Scholes pricing (inputs: underlying price, strike, time-to-expiry = 1 year from buy date, implied vol = historical 30/60/90-day realized or user-supplied IV surface). For backtesting, synthetic pricing is acceptable.

### Liquidation / pause rules (configurable)

* **Pause buys threshold (drawdown from recent high):** X% below rolling N-day high (e.g., 10% below 100-day high). Parameter: `pause_drawdown_pct` and `pause_lookback_days`.
* **Liquidate threshold:** Y% below 200-day moving average OR Z% from peak (example defaults: 15% from 200-day MA OR 18% from recent high). Parameterize `liquidate_pct_from_200ma` and `liquidate_pct_from_peak`.
* **Technical confirmation:** optional death-cross condition: 50-day MA < 200-day MA triggers liquidation.
* **Volatility gating:** if VIX > `vix_threshold` then pause buys (default 25).
* **Resume rules:** automatic resume when SPY recovers above 200-day MA for N consecutive days or when drawdown recovers to within `resume_pct` of peak. Parameter: `resume_consec_days`.

### Risk management

* **Max capital at risk cap:** e.g., total premium exposure cap (like 10% of portfolio) — stop buying when exposure + planned buy > cap.
* **Position-level stop:** optional — liquidate a specific LEAP if its premium drops more than `pos_loss_pct` from entry.

---

## 4. Backtest Engine

### Workflow

1. Load SPY historical daily prices and VIX (if used).
2. Iterate daily; on buy-day (weekly cadence) check `pause` conditions; if allowed, create a simulated trade using option premium (synthetic BS or historical), store trade record in `trades`.
3. Each day, mark-to-market open trades (recompute synthetic premium using current underlying price and time-to-expiry), update unrealized P&L.
4. On liquidation trigger (global or position-level), close trades at computed premium and record exit.
5. At the end of the run, compute metrics and export results.

### Performance / metrics to compute

* Total return, CAGR
* Max drawdown (underlying and strategy equity curve)
* Win rate, average win/loss
* Sharpe ratio (annualized), Sortino ratio
* Exposure over time (capital deployed)
* Cost basis vs realized delta exposure

---

## 5. Option Pricing for Backtest

* **Simplest approach:** Black-Scholes with implied vol estimated from historical realized vol (rolling 30-day or 60-day vol annualized). Use `scipy` or `py_vollib` for pricing.
* **More advanced:** Build an IV surface by expiry using historical option quotes if available.
* **Strike selection logic:** choose the strike that is nearest to target moneyness (ATM, 5% OTM, etc). For integer strike spacing approximate.

---

## 6. Streamlit UI Requirements

### Pages / Tabs

* `Overview` — quick summary of current portfolio, latest SPY price, VIX, and buy-pause/liquidation status.
* `Backtest` — inputs for parameters, run backtest, show plots, and export results.
* `Trades` — table of simulated trades from DB (sortable); allow CSV export.
* `Sensitivity` — sweep through parameter ranges (pause pct, liquidate pct, weekly_amount) and display aggregated metrics.
* `Signals` — chronological list of generated signals: pause, liquidate, resume.

### Visualizations

* Equity curve (strategy vs buy-and-hold SPY).
* Drawdown plot.
* Exposure timeline (capital deployed over time).
* Rolling metrics: rolling Sharpe, rolling volatility.
* Underlying price with annotated signals (pause/liquidate/resume events).
* Histogram of trade returns.

### Controls

* Parameter inputs (sliders / numeric): weekly_amount, strike_moneyness, pause_pct, liquidate_pct, vix_threshold, lookback windows, resume rules.
* Buttons: `Run Backtest`, `Reset DB`, `Export CSV`, `Run Sensitivity Sweep`.

---

## 7. Example Default Parameters (starting point)

* `weekly_amount`: $1000
* `strike_moneyness`: 0% (ATM)
* `pause_drawdown_pct`: 10
* `pause_lookback_days`: 100
* `liquidate_pct_from_200ma`: 15
* `liquidate_pct_from_peak`: 18
* `vix_threshold`: 25
* `resume_consec_days`: 15
* `max_exposure_pct`: 10 (of portfolio)

---

## 8. Files & Project Structure

```
spy-leaps-backtester/
├─ data/                    # downloaded csv jsons
├─ src/
│  ├─ main.py               # streamlit entry
│  ├─ backtest.py           # core backtest engine
│  ├─ pricing.py            # option pricing helpers
│  ├─ db.py                 # sqlite helpers
│  ├─ analysis.py           # metrics and plotting utilities
│  ├─ signals.py            # pause/liquidation logic
│  └─ config.py
├─ notebooks/               # for EDA
├─ requirements.txt
├─ README.md
└─ tests/
   ├─ test_pricing.py
   ├─ test_signals.py
   └─ test_end_to_end.py
```

---

## 9. Testing & Validation

* Unit tests for pricing (compare known BS values).
* Unit tests for signal generation (synthetic price paths to ensure pause/liquidate triggers).
* End-to-end tests with small sample dataset.
* Backtest validation: compare strategy equity to naive baseline (buy-and-hold SPY) and check behavior during historical corrections (2008, 2020, 2022 drawdowns if data included).

---

## 10. Sensitivity & Scenario Analysis

* Sweep `pause_drawdown_pct` across [5, 12, 20].
* Sweep `liquidate_pct` across [12, 25].
* Sweep `weekly_amount` across [500, 2000].
* Scenario tests: apply forced crash days (-10% single day), long drawdown (20% over 3 months), VIX spikes.

---

## 11. Deliverables & Roadmap

**MVP (week 1–2):**

* Local Streamlit app that loads CSV price data, implements weekly buys with synthetic BS pricing, stores trades in SQLite, and shows equity curve + trades table.

**Phase 2:**

* Add configurable liquidation rules (drawdown & MA), VIX gating, sensitivity sweeps.
* Add exports and paper-trade signal feed (CSV / webhook stub).

**Phase 3:**

* Improve option pricing (IV surface), add intraday handling (if needed), and integrate with a broker API for live paper-trade.

---

## 12. Example pseudocode (buy / check logic)

```
for date in trading_days:
    update_mark_to_market()
    if is_buy_day(date):
        if not global_pause:
            buy_leap(date)
    if check_liquidate_condition(date):
        liquidate_all(date)
    record_metrics(date)
```

---

## 13. Next steps I can do for you now

* Provide a ready-to-run GitHub-style `README.md` and `requirements.txt`.
* Scaffold the Streamlit `main.py` and core `backtest.py` files with starter code and functions.
* Create unit tests for pricing and signals.

Tell me which of the above you'd like me to produce first and I will scaffold it.
