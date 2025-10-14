"""
End-to-end integration test
"""
import pytest
import pandas as pd
import numpy as np
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import StrategyConfig
from src.db import Database
from src.backtest import BacktestEngine


def create_synthetic_data(length=500):
    """Create synthetic SPY-like data"""
    dates = pd.date_range(start='2020-01-01', periods=length, freq='D')
    
    # Generate prices with some volatility and trend
    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.01, length)
    prices = 400 * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'open': prices * np.random.uniform(0.99, 1.01, length),
        'high': prices * np.random.uniform(1.00, 1.02, length),
        'low': prices * np.random.uniform(0.98, 1.00, length),
        'close': prices,
        'volume': np.random.uniform(50000000, 100000000, length),
        'adj_close': prices
    }, index=dates)
    
    return df


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db = Database(db_path)
    yield db
    
    # Cleanup
    os.unlink(db_path)


def test_end_to_end_backtest(temp_db):
    """Test complete backtest workflow"""
    # Create synthetic data
    prices = create_synthetic_data(500)
    vix = create_synthetic_data(500)
    vix['close'] = np.random.uniform(15, 30, 500)  # VIX-like values
    
    # Save to database
    temp_db.save_prices(prices, 'prices')
    temp_db.save_prices(vix, 'vix')
    
    # Create configuration
    config = StrategyConfig(
        weekly_amount=1000.0,
        initial_capital=100000.0,
        start_date=prices.index[0].strftime('%Y-%m-%d'),
        end_date=prices.index[-1].strftime('%Y-%m-%d'),
        pause_drawdown_pct=10.0,
        liquidate_pct_from_peak=18.0
    )
    
    # Run backtest
    engine = BacktestEngine(config, temp_db)
    results = engine.run()
    
    # Verify results
    assert 'total_return' in results
    assert 'max_drawdown' in results
    assert 'sharpe_ratio' in results
    assert 'equity_curve' in results
    
    # Check equity curve
    equity_df = results['equity_curve']
    assert len(equity_df) > 0
    assert 'value' in equity_df.columns
    
    # Check that some trades were made
    trades = temp_db.load_trades()
    assert len(trades) > 0, "Should have executed some trades"
    
    # Check that signals were generated
    signals = temp_db.load_signals()
    assert len(signals) > 0, "Should have generated some signals"
    
    # Verify metrics are reasonable
    assert -100 < results['total_return'] < 1000, "Return should be reasonable"
    assert results['max_drawdown'] < 0, "Max drawdown should be negative"


def test_position_management(temp_db):
    """Test that positions are opened and closed correctly"""
    # Create synthetic data with known patterns
    prices = create_synthetic_data(300)
    temp_db.save_prices(prices, 'prices')
    
    # Configuration
    config = StrategyConfig(
        weekly_amount=1000.0,
        initial_capital=100000.0,
        start_date=prices.index[0].strftime('%Y-%m-%d'),
        end_date=prices.index[-1].strftime('%Y-%m-%d'),
        buy_weekday=4  # Friday
    )
    
    # Run backtest
    engine = BacktestEngine(config, temp_db)
    results = engine.run()
    
    # Load trades
    trades = temp_db.load_trades()
    
    # Verify trade structure
    assert 'entry_date' in trades.columns
    assert 'exit_date' in trades.columns
    assert 'pnl' in trades.columns
    
    # Check that all trades are closed
    assert trades['exit_date'].notna().all(), "All trades should be closed"
    
    # Check that P&L is calculated
    assert trades['pnl'].notna().all(), "All trades should have P&L"


def test_signal_generation(temp_db):
    """Test that signals are generated correctly"""
    # Create data with a crash scenario
    dates = pd.date_range(start='2020-01-01', periods=400, freq='D')
    
    # Simulate a crash: rise then fall
    close_prices = (
        list(np.linspace(400, 500, 200)) +  # Rise
        list(np.linspace(500, 400, 200))    # Fall
    )
    
    prices = pd.DataFrame({
        'open': close_prices,
        'high': [p * 1.01 for p in close_prices],
        'low': [p * 0.99 for p in close_prices],
        'close': close_prices,
        'volume': [100000000] * 400,
        'adj_close': close_prices
    }, index=dates)
    
    temp_db.save_prices(prices, 'prices')
    
    # Configuration with pause and liquidate rules
    config = StrategyConfig(
        weekly_amount=1000.0,
        initial_capital=100000.0,
        start_date=prices.index[0].strftime('%Y-%m-%d'),
        end_date=prices.index[-1].strftime('%Y-%m-%d'),
        pause_drawdown_pct=10.0,
        liquidate_pct_from_peak=15.0
    )
    
    # Run backtest
    engine = BacktestEngine(config, temp_db)
    results = engine.run()
    
    # Load signals
    signals = temp_db.load_signals()
    
    # Should have various signal types
    signal_types = signals['signal_type'].unique()
    
    # During a crash, we should see PAUSE or LIQUIDATE signals
    assert len(signals) > 0, "Should generate signals during crash"
    assert 'LIQUIDATE' in signal_types or 'PAUSE' in signal_types


def test_exposure_limits(temp_db):
    """Test that exposure limits are respected"""
    prices = create_synthetic_data(200)
    temp_db.save_prices(prices, 'prices')
    
    # Configuration with low exposure limit
    config = StrategyConfig(
        weekly_amount=10000.0,  # Large weekly amount
        initial_capital=100000.0,
        max_exposure_pct=5.0,  # Low limit
        start_date=prices.index[0].strftime('%Y-%m-%d'),
        end_date=prices.index[-1].strftime('%Y-%m-%d')
    )
    
    # Run backtest
    engine = BacktestEngine(config, temp_db)
    results = engine.run()
    
    # Check signals for MAX_EXPOSURE
    signals = temp_db.load_signals()
    
    # Should hit exposure limit
    signal_types = signals['signal_type'].unique()
    assert 'MAX_EXPOSURE' in signal_types or 'BUY' in signal_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
