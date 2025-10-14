# Troubleshooting Guide

## Common Issues and Solutions

### 1. YFinance "tuple object has no attribute lower" Error

**Problem:** Getting error `'tuple' object has no attribute 'lower'` when downloading data.

**Cause:** yfinance API changed and now returns multi-index columns in a different format.

**Solution:** ✅ **FIXED** - Updated all download functions to properly handle multi-index columns.

The fix has been applied to:
- `start.py`
- `src/download_data.py`
- `src/main.py`

### 2. SSL Timeout Errors

**Problem:** `SSLError: Failed to perform, curl: (35) Recv failure: Operation timed out`

**Cause:** Network timeout when downloading large date ranges from Yahoo Finance.

**Solutions:**
- Use shorter date ranges (e.g., start from 2015 instead of 2010)
- Retry the download
- Check your internet connection

**Example:**
```bash
# Download data from 2015 instead of 2010
venv/bin/python src/download_data.py --ticker SPY --table prices --start 2015-01-01
```

### 3. Streamlit Command Not Found

**Problem:** `sh: streamlit: command not found` when running `start.py`

**Cause:** Streamlit is installed in the virtual environment but not in system PATH.

**Solution:** ✅ **FIXED** - Updated `start.py` to use the venv streamlit directly.

**Alternative:** Use the run script:
```bash
./run.sh start
```

### 4. Missing Dependencies

**Problem:** Import errors like `ModuleNotFoundError`

**Solution:**
```bash
# Activate venv and install requirements
source venv/bin/activate
pip install -r requirements.txt
```

Or use the venv directly:
```bash
venv/bin/pip install -r requirements.txt
```

### 5. Database Locked

**Problem:** `database is locked` error

**Solutions:**
1. Close any other connections to the database
2. Restart the Streamlit app
3. Reset the database:
   ```bash
   rm data/spy_leaps.db
   ./run.sh start
   ```

### 6. No Data Available in App

**Problem:** App says "No data available"

**Solution:** Download data using one of these methods:

**Method 1: In the App**
1. Go to "Data Management" page
2. Click "Download SPY Data"
3. Click "Download VIX Data"

**Method 2: Command Line**
```bash
venv/bin/python src/download_data.py --ticker SPY --table prices --start 2015-01-01
venv/bin/python src/download_data.py --ticker ^VIX --table vix --start 2015-01-01
```

**Method 3: Run Script**
```bash
./run.sh download
```

### 7. Port Already in Use

**Problem:** `Port 8501 is already in use`

**Solutions:**
1. Find and kill the existing process:
   ```bash
   lsof -ti:8501 | xargs kill -9
   ```
2. Use a different port:
   ```bash
   venv/bin/streamlit run src/main.py --server.port 8502
   ```

### 8. Python Version Issues

**Problem:** Compatibility issues with Python version

**Requirements:** Python 3.9 or higher

**Check your version:**
```bash
python3 --version
```

**Solution:** Install Python 3.9+ if needed.

### 9. Charts Not Displaying

**Problem:** Blank charts or visualization errors

**Solutions:**
1. Clear Streamlit cache:
   ```bash
   rm -rf ~/.streamlit/cache
   ```
2. Refresh the browser (Cmd+Shift+R or Ctrl+Shift+R)
3. Reinstall plotly:
   ```bash
   venv/bin/pip install --upgrade plotly
   ```

### 10. Test Failures

**Problem:** Tests failing when running `pytest`

**Solutions:**
1. Make sure you're using the venv:
   ```bash
   venv/bin/pytest tests/ -v
   ```
2. Install test dependencies:
   ```bash
   venv/bin/pip install pytest pytest-cov
   ```

## Quick Fixes Summary

### Data Download Working ✅
```bash
# Download recent data (2015-present)
venv/bin/python src/download_data.py --ticker SPY --table prices --start 2015-01-01
venv/bin/python src/download_data.py --ticker ^VIX --table vix --start 2015-01-01
```

### Launch App ✅
```bash
# Use run script (recommended)
./run.sh start

# Or direct command
venv/bin/streamlit run src/main.py
```

### Run Tests ✅
```bash
venv/bin/pytest tests/ -v
```

## Getting Help

If you continue to experience issues:

1. Check the terminal output for specific error messages
2. Review the logs in the Streamlit interface
3. Try resetting the database: `rm data/spy_leaps.db`
4. Reinstall dependencies: `venv/bin/pip install -r requirements.txt --force-reinstall`

## System Status Check

Run this to verify your setup:

```bash
# Check Python version
venv/bin/python --version

# Check installed packages
venv/bin/pip list

# Check data
ls -lh data/

# Test imports
venv/bin/python -c "import streamlit, pandas, yfinance; print('All imports OK')"
```

## Recent Fixes Applied

- ✅ Fixed yfinance multi-index column handling
- ✅ Fixed start.py to use venv streamlit
- ✅ Added auto_adjust=False to prevent warnings
- ✅ Improved error handling in data downloads
- ✅ Updated all download functions consistently

---

Last Updated: October 14, 2025
