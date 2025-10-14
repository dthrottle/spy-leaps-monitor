#!/usr/bin/env python3
"""
Quick start script to download initial data and launch the app
"""
import os
import sys
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.db import Database
from src.config import DB_PATH
import yfinance as yf
from datetime import datetime

def download_and_save_data(ticker, table_name, db):
    """Download data from Yahoo Finance and save to database"""
    print(f"Downloading {ticker} data...")
    try:
        data = yf.download(ticker, start='2010-01-01', end=datetime.now().strftime('%Y-%m-%d'), 
                          progress=False, auto_adjust=False)
        
        if len(data) > 0:
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
            
            # Ensure all required columns exist
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                print(f"❌ Missing required columns: {missing_cols}")
                return False
            
            db.save_prices(data, table_name)
            print(f"✅ Saved {len(data)} rows of {ticker} data to '{table_name}' table")
            return True
        else:
            print(f"❌ No data retrieved for {ticker}")
            return False
    except Exception as e:
        print(f"❌ Error downloading {ticker}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("SPY LEAPS Monitor - Quick Start Setup")
    print("=" * 60)
    print()
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Initialize database
    print("Initializing database...")
    db = Database(DB_PATH)
    print("✅ Database initialized")
    print()
    
    # Check if data already exists
    try:
        prices = db.load_prices('prices')
        if len(prices) > 0:
            print(f"📊 SPY data already exists ({len(prices)} rows)")
            print(f"   Date range: {prices.index[0]} to {prices.index[-1]}")
            
            response = input("\nDownload fresh data? (y/n): ")
            if response.lower() != 'y':
                print("\nSkipping data download...")
                print("\n✅ Setup complete! Starting application...\n")
                os.system("streamlit run src/main.py")
                return
    except:
        pass
    
    # Download SPY data
    print("\n" + "-" * 60)
    download_and_save_data('SPY', 'prices', db)
    
    # Download VIX data
    print("-" * 60)
    download_and_save_data('^VIX', 'vix', db)
    
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\nStarting Streamlit application...")
    print("The app will open in your browser at http://localhost:8501")
    print("\nPress Ctrl+C to stop the application")
    print()
    
    # Launch Streamlit app using the venv python
    import subprocess
    venv_streamlit = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'streamlit')
    if os.path.exists(venv_streamlit):
        subprocess.run([venv_streamlit, 'run', 'src/main.py'])
    else:
        # Fallback to system streamlit
        os.system("streamlit run src/main.py")

if __name__ == "__main__":
    main()
