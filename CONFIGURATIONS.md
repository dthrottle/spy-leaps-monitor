# Example Strategy Configurations

This file contains example strategy configurations for different market conditions and risk profiles.

## Conservative Strategy

**Use when:** High uncertainty, volatile markets, or risk-averse investors

```python
config = StrategyConfig(
    weekly_amount=500.0,
    buy_weekday=4,  # Friday
    strike_moneyness=0.0,  # ATM
    
    # Tight risk controls
    pause_drawdown_pct=5.0,        # Pause quickly on drawdowns
    liquidate_pct_from_200ma=12.0, # Exit when 12% below 200-MA
    liquidate_pct_from_peak=15.0,  # Exit on 15% drawdown from peak
    vix_threshold=20.0,             # Pause when VIX > 20
    
    # Lower exposure
    max_exposure_pct=5.0,
    
    # Quick resume
    resume_consec_days=10,
    resume_pct=3.0,
    
    initial_capital=100000.0
)
```

**Expected Characteristics:**
- Lower returns but less volatile
- More frequent pauses and liquidations
- Better downside protection
- Lower maximum drawdown

---

## Moderate Strategy (Default)

**Use when:** Normal market conditions, balanced approach

```python
config = StrategyConfig(
    weekly_amount=1000.0,
    buy_weekday=4,
    strike_moneyness=0.0,
    
    # Balanced risk controls
    pause_drawdown_pct=10.0,
    liquidate_pct_from_200ma=15.0,
    liquidate_pct_from_peak=18.0,
    vix_threshold=25.0,
    
    max_exposure_pct=10.0,
    
    resume_consec_days=15,
    resume_pct=5.0,
    
    initial_capital=100000.0
)
```

**Expected Characteristics:**
- Moderate returns with reasonable volatility
- Balanced pause/liquidation triggers
- Good risk-reward balance
- Suitable for most market conditions

---

## Aggressive Strategy

**Use when:** Bullish outlook, long-term horizon, higher risk tolerance

```python
config = StrategyConfig(
    weekly_amount=2000.0,
    buy_weekday=4,
    strike_moneyness=0.0,
    
    # Loose risk controls
    pause_drawdown_pct=15.0,        # Stay invested through drawdowns
    liquidate_pct_from_200ma=20.0,  # Only exit on severe declines
    liquidate_pct_from_peak=25.0,   # 25% drawdown tolerance
    vix_threshold=30.0,              # Less VIX sensitivity
    
    # Higher exposure
    max_exposure_pct=15.0,
    
    # Patient resume
    resume_consec_days=20,
    resume_pct=8.0,
    
    initial_capital=100000.0
)
```

**Expected Characteristics:**
- Higher potential returns
- Greater volatility and drawdowns
- Stays invested through corrections
- Better for bull markets

---

## Growth Focus (OTM Strikes)

**Use when:** Seeking leveraged upside exposure

```python
config = StrategyConfig(
    weekly_amount=1500.0,
    buy_weekday=4,
    strike_moneyness=5.0,  # 5% OTM calls
    
    # Moderate risk controls
    pause_drawdown_pct=10.0,
    liquidate_pct_from_200ma=15.0,
    liquidate_pct_from_peak=18.0,
    vix_threshold=25.0,
    
    max_exposure_pct=12.0,
    
    resume_consec_days=15,
    resume_pct=5.0,
    
    initial_capital=100000.0
)
```

**Expected Characteristics:**
- Lower premium costs (more contracts)
- Higher delta exposure
- More sensitive to moves
- Better leverage in bull markets

---

## Income Focus (ITM Strikes)

**Use when:** Seeking lower volatility, dividend-like returns

```python
config = StrategyConfig(
    weekly_amount=1000.0,
    buy_weekday=4,
    strike_moneyness=-5.0,  # 5% ITM calls
    
    # Tight risk controls
    pause_drawdown_pct=8.0,
    liquidate_pct_from_200ma=12.0,
    liquidate_pct_from_peak=15.0,
    vix_threshold=22.0,
    
    max_exposure_pct=10.0,
    
    resume_consec_days=12,
    resume_pct=4.0,
    
    initial_capital=100000.0
)
```

**Expected Characteristics:**
- Higher premium costs (fewer contracts)
- Lower delta exposure per contract
- More stable returns
- Better intrinsic value protection

---

## Bear Market Defense

**Use when:** Expecting volatility, defensive positioning

```python
config = StrategyConfig(
    weekly_amount=500.0,
    buy_weekday=4,
    strike_moneyness=0.0,
    
    # Very tight risk controls
    pause_drawdown_pct=5.0,
    liquidate_pct_from_200ma=10.0,
    liquidate_pct_from_peak=12.0,
    vix_threshold=18.0,
    use_death_cross=True,  # Enable death cross trigger
    
    max_exposure_pct=5.0,
    
    resume_consec_days=20,  # Patient on resume
    resume_pct=2.0,
    
    initial_capital=100000.0
)
```

**Expected Characteristics:**
- Very defensive positioning
- Quick to exit on weakness
- Lower exposure
- Capital preservation focus

---

## How to Use These Configs

### In Code:

```python
from src.config import StrategyConfig
from src.db import Database
from src.backtest import BacktestEngine

# Choose a configuration
config = StrategyConfig(
    # Copy parameters from above
    weekly_amount=1000.0,
    # ... etc
)

# Run backtest
db = Database()
engine = BacktestEngine(config, db)
results = engine.run()
```

### In Streamlit:

1. Go to the **Backtest** page
2. Adjust sliders to match the desired configuration
3. Click **Run Backtest**

---

## Testing Configurations

Always test configurations across multiple market conditions:

1. **Bull Market**: 2013-2019, 2020-2021
2. **Bear Market**: 2008-2009, 2022
3. **Volatility**: 2020 COVID crash
4. **Full Cycle**: 2010-2024

---

## Optimization Tips

1. **Start Conservative**: Begin with tighter risk controls
2. **Test Sensitivity**: Use sensitivity analysis to find optimal parameters
3. **Consider Correlation**: Different parameters interact (drawdown + VIX)
4. **Market Regime**: Adjust for current market conditions
5. **Don't Overfit**: Avoid optimizing solely for past performance

---

## Parameter Ranges

Typical ranges for key parameters:

| Parameter | Conservative | Moderate | Aggressive |
|-----------|-------------|----------|------------|
| Pause Drawdown % | 5-8 | 10-12 | 15-20 |
| Liquidate from Peak % | 12-15 | 18-20 | 25-30 |
| VIX Threshold | 18-22 | 25-28 | 30-35 |
| Max Exposure % | 5-7 | 10-12 | 15-20 |
| Weekly Amount | Low | Medium | High |

---

## Notes

- These are **example configurations** only
- Always backtest before using
- Past performance doesn't guarantee future results
- Adjust based on your risk tolerance
- Monitor and rebalance regularly
