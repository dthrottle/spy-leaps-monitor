"""
Database management module using SQLite
"""
import sqlite3
import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime
import json


class Database:
    """SQLite database manager for SPY LEAPS strategy"""
    
    def __init__(self, db_path: str = "data/spy_leaps.db"):
        self.db_path = db_path
        self.init_tables()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_tables(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Prices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                date TEXT PRIMARY KEY,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                adj_close REAL,
                volume REAL
            )
        """)
        
        # VIX table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vix (
                date TEXT PRIMARY KEY,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                adj_close REAL,
                volume REAL
            )
        """)
        
        # Trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date TEXT,
                exit_date TEXT,
                entry_price REAL,
                exit_price REAL,
                option_strike REAL,
                option_entry_premium REAL,
                option_exit_premium REAL,
                contracts INTEGER,
                pnl REAL,
                notes TEXT
            )
        """)
        
        # Config table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                run_id TEXT PRIMARY KEY,
                created_at TEXT,
                params TEXT
            )
        """)
        
        # Signals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                signal_type TEXT,
                details TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_prices(self, df: pd.DataFrame, table: str = 'prices'):
        """Save price data to database"""
        conn = self.get_connection()
        df.to_sql(table, conn, if_exists='replace', index=True, index_label='date')
        conn.close()
    
    def load_prices(self, table: str = 'prices', start_date: Optional[str] = None, 
                    end_date: Optional[str] = None) -> pd.DataFrame:
        """Load price data from database"""
        conn = self.get_connection()
        
        query = f"SELECT * FROM {table}"
        conditions = []
        
        if start_date:
            conditions.append(f"date >= '{start_date}'")
        if end_date:
            conditions.append(f"date <= '{end_date}'")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY date"
        
        df = pd.read_sql_query(query, conn, index_col='date', parse_dates=['date'])
        conn.close()
        return df
    
    def save_trade(self, trade: Dict):
        """Save a single trade"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO trades (entry_date, exit_date, entry_price, exit_price,
                              option_strike, option_entry_premium, option_exit_premium,
                              contracts, pnl, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade.get('entry_date'),
            trade.get('exit_date'),
            trade.get('entry_price'),
            trade.get('exit_price'),
            trade.get('option_strike'),
            trade.get('option_entry_premium'),
            trade.get('option_exit_premium'),
            trade.get('contracts'),
            trade.get('pnl'),
            trade.get('notes')
        ))
        
        conn.commit()
        conn.close()
    
    def load_trades(self, run_id: Optional[str] = None) -> pd.DataFrame:
        """Load all trades"""
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM trades ORDER BY entry_date", conn)
        conn.close()
        return df
    
    def save_config(self, run_id: str, params: Dict):
        """Save configuration for a backtest run"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO config (run_id, created_at, params)
            VALUES (?, ?, ?)
        """, (run_id, datetime.now().isoformat(), json.dumps(params)))
        
        conn.commit()
        conn.close()
    
    def save_signal(self, date: str, signal_type: str, details: str):
        """Save a signal"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO signals (date, signal_type, details)
            VALUES (?, ?, ?)
        """, (date, signal_type, details))
        
        conn.commit()
        conn.close()
    
    def load_signals(self) -> pd.DataFrame:
        """Load all signals"""
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM signals ORDER BY date", conn)
        conn.close()
        return df
    
    def clear_trades(self):
        """Clear all trades"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM trades")
        conn.commit()
        conn.close()
    
    def clear_signals(self):
        """Clear all signals"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM signals")
        conn.commit()
        conn.close()
    
    def reset_database(self):
        """Reset all tables except prices and vix"""
        self.clear_trades()
        self.clear_signals()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM config")
        conn.commit()
        conn.close()
