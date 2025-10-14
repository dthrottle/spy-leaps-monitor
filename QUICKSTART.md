# Quick Start Guide

This guide will help you get started with the SPY LEAPS Monitor application.

## Step 1: Installation

First, install the required dependencies:

```bash
pip install -r requirements.txt
```

## Step 2: Quick Start (Recommended)

Use the quick start script to automatically download data and launch the app:

```bash
python start.py
```

This will:
1. Create the database
2. Download SPY historical data from 2010
3. Download VIX historical data from 2010
4. Launch the Streamlit application

## Step 3: Manual Start

If you prefer to set things up manually:

### Download Data

```bash
# Download SPY data
python src/download_data.py --ticker SPY --table prices --start 2010-01-01

# Download VIX data
python src/download_data.py --ticker ^VIX --table vix --start 2010-01-01
```

### Launch Application

```bash
streamlit run src/main.py
```

## Step 4: Run Your First Backtest

1. Open the application in your browser (http://localhost:8501)
2. Go to the **Backtest** page
3. Configure your parameters:
   - Weekly Amount: $1,000
   - Initial Capital: $100,000
   - Start Date: 2015-01-01
   - Keep other defaults
4. Click **"Run Backtest"**
5. View your results!

## Step 5: Explore the Results

### Metrics to Review:
- **Total Return**: How much did the strategy return?
- **Max Drawdown**: What was the worst decline?
- **Sharpe Ratio**: Risk-adjusted performance
- **Win Rate**: Percentage of profitable trades

### Charts to Explore:
- **Equity Curve**: Strategy vs Buy & Hold comparison
- **Drawdown**: Visualize worst periods
- **Exposure**: Number of positions over time
- **Trade Returns**: Distribution of P&L

## Step 6: Experiment with Parameters

Try adjusting these parameters to see how they affect performance:

### More Conservative:
- Pause Drawdown: 5% (pause earlier)
- Liquidate from Peak: 12% (exit earlier)
- VIX Threshold: 20 (more sensitive to volatility)

### More Aggressive:
- Pause Drawdown: 15% (pause later)
- Liquidate from Peak: 25% (stay invested longer)
- VIX Threshold: 30 (less sensitive to volatility)

## Step 7: Run Sensitivity Analysis

1. Go to **Sensitivity** page
2. Select a parameter to sweep (e.g., `pause_drawdown_pct`)
3. Set range: Min=5, Max=20, Step=5
4. Click **"Run Sensitivity Analysis"**
5. Compare results to find optimal values

## Common Issues

### No Data Available
**Solution**: Go to **Data Management** and download SPY/VIX data

### Import Errors
**Solution**: Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Database Errors
**Solution**: Reset the database:
1. Go to **Data Management**
2. Click **"Reset Database"**
3. Re-download data

## Tips for Success

1. **Start Simple**: Use default parameters first
2. **Compare to Buy & Hold**: Always benchmark against passive investing
3. **Test Multiple Periods**: Try different date ranges (bull/bear markets)
4. **Consider Transaction Costs**: Real-world results will be lower
5. **Don't Overfit**: Avoid optimizing for past performance only

## Next Steps

- Review the [README.md](README.md) for detailed documentation
- Check out the [spec](spy-leaps-monitor-spec.md) for strategy details
- Run the test suite: `pytest tests/ -v`
- Explore notebooks for advanced analysis

## Support

Having issues? Check:
1. The error message in the terminal
2. Streamlit logs in the browser console
3. Database contents in `data/spy_leaps.db`

## Example Workflow

```bash
# 1. Install
pip install -r requirements.txt

# 2. Quick start (downloads data and launches app)
python start.py

# 3. In the browser:
#    - Go to Backtest page
#    - Set parameters
#    - Run backtest
#    - Review results

# 4. Export results
#    - Click "Export Results"
#    - Download trades CSV
#    - Analyze in Excel/Python

# 5. Optimize
#    - Go to Sensitivity page
#    - Test different parameters
#    - Find best configuration
```

Happy backtesting! 📈
