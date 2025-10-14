"""
Utility script to download and update market data
"""
import sys
import os
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.db import Database
from src.config import DB_PATH
import yfinance as yf
from datetime import datetime
import argparse


def download_data(ticker, start_date, end_date=None):
    """Download data from Yahoo Finance"""
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Downloading {ticker} from {start_date} to {end_date}...")
    
    data = yf.download(ticker, start=start_date, end=end_date, progress=True, auto_adjust=False)
    
    if len(data) == 0:
        print(f"No data retrieved for {ticker}")
        return None
    
    # Handle multi-index columns from yfinance
    if isinstance(data.columns, pd.MultiIndex):
        # Flatten multi-index columns
        data.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in data.columns.values]
        # Clean up the column names
        data.columns = [col.split('_')[0].lower() if '_' in col else col.lower() for col in data.columns]
    else:
        # Clean up column names for single-index
        data.columns = [col.lower().replace(' ', '_') for col in data.columns]
    
    # Ensure adj_close exists
    if 'adj' in data.columns:
        data.rename(columns={'adj': 'adj_close'}, inplace=True)
    if 'adj_close' not in data.columns and 'close' in data.columns:
        data['adj_close'] = data['close']
    
    return data


def main():
    parser = argparse.ArgumentParser(description='Download market data for SPY LEAPS Monitor')
    parser.add_argument('--ticker', type=str, default='SPY', help='Ticker symbol to download')
    parser.add_argument('--table', type=str, default='prices', help='Database table name')
    parser.add_argument('--start', type=str, default='2010-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, default=None, help='End date (YYYY-MM-DD), defaults to today')
    
    args = parser.parse_args()
    
    # Initialize database
    db = Database(DB_PATH)
    
    # Download data
    data = download_data(args.ticker, args.start, args.end)
    
    if data is not None:
        # Save to database
        db.save_prices(data, args.table)
        print(f"\n✅ Saved {len(data)} rows to '{args.table}' table")
        print(f"Date range: {data.index[0]} to {data.index[-1]}")
    else:
        print("\n❌ Failed to download data")


if __name__ == "__main__":
    main()
