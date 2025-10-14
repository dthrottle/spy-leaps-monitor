# Example Jupyter Notebook for SPY LEAPS Analysis

This is a template for analyzing backtest results.

## Getting Started

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.getcwd(), '..', 'src'))

from config import StrategyConfig, DB_PATH
from db import Database
from backtest import BacktestEngine

# Load database
db = Database(DB_PATH)
```

## Load and Analyze Trades

```python
# Load trades
trades = db.load_trades()
print(f"Total trades: {len(trades)}")
print(f"Total P&L: ${trades['pnl'].sum():,.2f}")

# View trades
trades.head()
```

## Load Signals

```python
# Load signals
signals = db.load_signals()
print(f"Total signals: {len(signals)}")

# Count by type
signals['signal_type'].value_counts()
```

## Run Custom Backtest

```python
# Create custom configuration
config = StrategyConfig(
    weekly_amount=2000.0,
    initial_capital=200000.0,
    start_date='2015-01-01',
    pause_drawdown_pct=8.0,
    liquidate_pct_from_peak=15.0
)

# Run backtest
engine = BacktestEngine(config, db)
results = engine.run()

# View results
print(f"Total Return: {results['total_return']:.2f}%")
print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
```

## Visualize Results

```python
# Plot equity curve
equity_df = results['equity_curve']

plt.figure(figsize=(12, 6))
plt.plot(equity_df.index, equity_df['value'], label='Strategy')
plt.title('Portfolio Value Over Time')
plt.xlabel('Date')
plt.ylabel('Value ($)')
plt.legend()
plt.grid(True)
plt.show()
```

## Compare Multiple Strategies

```python
# Test multiple configurations
configs = [
    {'pause_drawdown_pct': 5.0, 'name': 'Conservative'},
    {'pause_drawdown_pct': 10.0, 'name': 'Moderate'},
    {'pause_drawdown_pct': 15.0, 'name': 'Aggressive'}
]

results_list = []

for cfg in configs:
    config = StrategyConfig(**cfg)
    engine = BacktestEngine(config, db)
    result = engine.run()
    results_list.append({
        'name': cfg['name'],
        'return': result['total_return'],
        'drawdown': result['max_drawdown'],
        'sharpe': result['sharpe_ratio']
    })

# Compare
pd.DataFrame(results_list)
```
