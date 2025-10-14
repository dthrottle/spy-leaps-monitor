# SPY LEAPS Monitor 📈

A comprehensive Python application for backtesting and monitoring SPY LEAPS (1-year expiry) accumulation strategies with configurable liquidation rules.

## Features

- **Weekly LEAPS Accumulation**: Automated weekly purchase schedule with configurable parameters
- **Smart Liquidation Rules**: Configurable stop/liquidation triggers based on:
  - Drawdown from recent highs
  - Moving average breaks (50/200-day MA)
  - VIX volatility gating
  - Death cross detection (optional)
- **Comprehensive Backtesting**: Test strategies on historical data with detailed metrics
- **Sensitivity Analysis**: Sweep through parameter ranges to optimize strategy
- **Interactive Dashboard**: Streamlit-based UI with rich visualizations
- **Local SQLite Storage**: All data stored locally for easy backup and analysis

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/spy-leaps-monitor.git
cd spy-leaps-monitor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create the data directory (if it doesn't exist):
```bash
mkdir -p data
```

## Usage

### Running the Application

Start the Streamlit dashboard:

```bash
streamlit run src/main.py
```

The application will open in your default web browser at `http://localhost:8501`

### First Time Setup

1. Navigate to the **Data Management** page
2. Download SPY historical data (ticker: SPY)
3. Download VIX data (ticker: ^VIX)
4. Configure your strategy parameters in the **Backtest** page
5. Run your first backtest!

## Application Pages

### 📊 Overview
- Quick portfolio summary
- Latest SPY price and technical indicators
- Recent trading signals
- Current portfolio status

### 🔬 Backtest
- Configure strategy parameters
- Set date ranges for historical testing
- Run backtests with detailed metrics
- Visualize equity curves, drawdowns, and performance
- Export results to CSV

### 💼 Trades
- View all executed trades
- Filter and sort trade history
- Analyze win/loss statistics
- Export trade data

### 🔍 Sensitivity
- Parameter sweep analysis
- Test different configurations
- Compare strategy variations
- Optimize parameters

### 🚦 Signals
- View all generated signals (BUY, PAUSE, LIQUIDATE, RESUME)
- Filter by signal type
- Visualize signals on price chart
- Export signal history

### 💾 Data Management
- Download/update historical data
- View database statistics
- Manage stored data
- Clear or reset database

## Strategy Parameters

### Core Parameters

- **Weekly Amount**: Capital allocated per week ($)
- **Buy Weekday**: Day of week for purchases (Monday-Friday)
- **Strike Moneyness**: Strike selection relative to spot (0% = ATM)
- **Initial Capital**: Starting portfolio value ($)

### Risk Management

- **Pause Drawdown Threshold**: Drawdown % to pause buying
- **Liquidate % from 200-day MA**: Distance from MA to trigger liquidation
- **Liquidate % from Peak**: Drawdown to trigger full liquidation
- **VIX Threshold**: VIX level to pause buying
- **Max Exposure**: Maximum portfolio exposure (%)

### Advanced Options

- **Death Cross**: Enable 50/200-day MA cross trigger
- **Resume Rules**: Conditions to resume buying after pause
- **Position Loss %**: Per-position stop loss (optional)

## Example Configuration

Default parameters provide a starting point:

```python
weekly_amount = $1,000
strike_moneyness = 0% (ATM)
pause_drawdown_pct = 10%
liquidate_pct_from_200ma = 15%
liquidate_pct_from_peak = 18%
vix_threshold = 25
max_exposure_pct = 10%
```

## Project Structure

```
spy-leaps-monitor/
├── data/                       # SQLite database and data files
│   └── spy_leaps.db           # Main database
├── src/
│   ├── main.py                # Streamlit application entry point
│   ├── config.py              # Configuration and parameters
│   ├── db.py                  # Database management
│   ├── backtest.py            # Core backtesting engine
│   ├── pricing.py             # Black-Scholes option pricing
│   ├── signals.py             # Signal generation logic
│   └── analysis.py            # Metrics and visualization
├── tests/
│   ├── test_pricing.py        # Pricing tests
│   ├── test_signals.py        # Signal generation tests
│   └── test_end_to_end.py     # Integration tests
├── notebooks/                  # Jupyter notebooks for analysis
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Performance Metrics

The application calculates comprehensive performance metrics:

- **Total Return**: Overall portfolio return (%)
- **CAGR**: Compound Annual Growth Rate
- **Max Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return
- **Sortino Ratio**: Downside risk-adjusted return
- **Win Rate**: Percentage of profitable trades
- **Average Win/Loss**: Mean P&L for winning/losing trades

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_pricing.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Option Pricing

The application uses **Black-Scholes pricing** with historical volatility:

- **Volatility Estimation**: Rolling 30-day realized volatility
- **Strike Selection**: Automatic selection based on moneyness
- **Time to Expiry**: 1 year from purchase date
- **Risk-free Rate**: Configurable (default 4.5%)

## Data Sources

- **SPY Prices**: Yahoo Finance via `yfinance`
- **VIX Data**: Yahoo Finance (^VIX ticker)
- **Storage**: Local SQLite database

## Limitations & Disclaimers

⚠️ **Important Notes:**

1. **Paper Trading Only**: This is a backtesting and analysis tool. It does NOT execute real trades.
2. **Synthetic Pricing**: Option premiums are calculated using Black-Scholes, not actual market prices.
3. **No Slippage/Fees**: Backtests do not account for bid-ask spreads, commissions, or slippage.
4. **Historical Performance**: Past results do not guarantee future performance.
5. **Not Financial Advice**: This tool is for educational and research purposes only.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Roadmap

### Future Enhancements

- [ ] Actual option prices from market data
- [ ] Implied volatility surface integration
- [ ] Multi-asset support (QQQ, IWM, etc.)
- [ ] Monte Carlo simulation
- [ ] Risk parity position sizing
- [ ] Greeks-based analysis
- [ ] Broker API integration for paper trading
- [ ] Email/webhook alerts for signals

## License

See [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Review the specification: [spy-leaps-monitor-spec.md](spy-leaps-monitor-spec.md)

## Acknowledgments

Built with:
- [Streamlit](https://streamlit.io/) - Interactive web UI
- [yfinance](https://github.com/ranaroussi/yfinance) - Market data
- [pandas](https://pandas.pydata.org/) - Data analysis
- [plotly](https://plotly.com/) - Interactive charts
- [scipy](https://scipy.org/) - Black-Scholes calculations

---

**Disclaimer**: This software is provided "as is" without warranty. Use at your own risk. Not financial advice.