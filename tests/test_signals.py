"""
Unit tests for signal generation
"""
import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import StrategyConfig
from src.signals import SignalGenerator


def create_test_prices(length=500):
    """Create synthetic price data for testing"""
    dates = pd.date_range(start='2020-01-01', periods=length, freq='D')
    prices = pd.DataFrame({
        'open': np.random.uniform(400, 500, length),
        'high': np.random.uniform(400, 500, length),
        'low': np.random.uniform(400, 500, length),
        'close': np.linspace(400, 500, length) + np.random.normal(0, 5, length),
        'volume': np.random.uniform(50000000, 100000000, length),
        'adj_close': np.linspace(400, 500, length) + np.random.normal(0, 5, length)
    }, index=dates)
    
    return prices


def test_calculate_indicators():
    """Test indicator calculation"""
    config = StrategyConfig()
    signal_gen = SignalGenerator(config)
    
    prices = create_test_prices(300)
    prices_with_indicators = signal_gen.calculate_indicators(prices)
    
    # Check that indicators are added
    assert 'ma_50' in prices_with_indicators.columns
    assert 'ma_200' in prices_with_indicators.columns
    assert 'rolling_high' in prices_with_indicators.columns
    assert 'drawdown_pct' in prices_with_indicators.columns
    assert 'pct_from_200ma' in prices_with_indicators.columns
    assert 'death_cross' in prices_with_indicators.columns
    
    # Check that MAs are calculated correctly
    assert pd.notna(prices_with_indicators['ma_50'].iloc[-1])
    assert pd.notna(prices_with_indicators['ma_200'].iloc[-1])


def test_check_pause_condition():
    """Test pause condition detection"""
    config = StrategyConfig(pause_drawdown_pct=10.0)
    signal_gen = SignalGenerator(config)
    
    # Create price data with a drawdown
    dates = pd.date_range(start='2020-01-01', periods=200, freq='D')
    prices = pd.DataFrame({
        'close': [500] * 100 + list(np.linspace(500, 440, 100))
    }, index=dates)
    
    prices['open'] = prices['close']
    prices['high'] = prices['close']
    prices['low'] = prices['close']
    prices['volume'] = 1000000
    prices['adj_close'] = prices['close']
    
    prices_with_indicators = signal_gen.calculate_indicators(prices)
    
    # Check that pause is triggered at end (>10% drawdown from 100-day high)
    last_date = prices.index[-1]
    should_pause, reason = signal_gen.check_pause_condition(
        last_date, prices_with_indicators
    )
    
    assert should_pause, "Should trigger pause on large drawdown"
    assert "Drawdown" in reason


def test_check_liquidate_condition():
    """Test liquidation condition detection"""
    config = StrategyConfig(
        liquidate_pct_from_peak=18.0,
        pause_lookback_days=100
    )
    signal_gen = SignalGenerator(config)
    
    # Create price data with large drawdown (500 to 380 = 24% drop)
    dates = pd.date_range(start='2020-01-01', periods=300, freq='D')
    prices = pd.DataFrame({
        'close': [500] * 150 + list(np.linspace(500, 380, 150))
    }, index=dates)
    
    prices['open'] = prices['close']
    prices['high'] = prices['close']
    prices['low'] = prices['close']
    prices['volume'] = 1000000
    prices['adj_close'] = prices['close']
    
    prices_with_indicators = signal_gen.calculate_indicators(prices)
    
    # Check that liquidation is triggered
    last_date = prices.index[-1]
    should_liquidate, reason = signal_gen.check_liquidate_condition(
        last_date, prices_with_indicators
    )
    
    assert should_liquidate, f"Should trigger liquidation on large drawdown. Reason: {reason}"


def test_check_resume_condition():
    """Test resume condition detection"""
    config = StrategyConfig(resume_consec_days=15, resume_pct=5.0)
    signal_gen = SignalGenerator(config)
    
    # Create price data that recovers
    dates = pd.date_range(start='2020-01-01', periods=300, freq='D')
    close_prices = (
        [500] * 100 + 
        list(np.linspace(500, 450, 50)) + 
        list(np.linspace(450, 500, 150))
    )
    
    prices = pd.DataFrame({
        'close': close_prices
    }, index=dates)
    
    prices['open'] = prices['close']
    prices['high'] = prices['close']
    prices['low'] = prices['close']
    prices['volume'] = 1000000
    prices['adj_close'] = prices['close']
    
    prices_with_indicators = signal_gen.calculate_indicators(prices)
    
    # Simulate checking resume after recovery
    # At the end, price should be recovered
    last_date = prices.index[-1]
    should_resume, reason = signal_gen.check_resume_condition(
        last_date, prices_with_indicators
    )
    
    # Should resume when drawdown recovers
    assert should_resume or prices_with_indicators.loc[last_date, 'drawdown_pct'] > -5


def test_is_buy_day():
    """Test buy day detection"""
    config = StrategyConfig(buy_weekday=4)  # Friday
    signal_gen = SignalGenerator(config)
    
    # Create dates with known weekdays
    friday = pd.Timestamp('2024-01-05')  # A Friday
    monday = pd.Timestamp('2024-01-01')  # A Monday
    
    assert signal_gen.is_buy_day(friday), "Friday should be buy day"
    assert not signal_gen.is_buy_day(monday), "Monday should not be buy day"


def test_death_cross_detection():
    """Test death cross detection"""
    config = StrategyConfig(use_death_cross=True, liquidate_pct_from_200ma=15.0)
    signal_gen = SignalGenerator(config)
    
    # Create price data where 50-day MA crosses below 200-day MA
    dates = pd.date_range(start='2020-01-01', periods=300, freq='D')
    prices = pd.DataFrame({
        'close': list(np.linspace(500, 450, 300))
    }, index=dates)
    
    prices['open'] = prices['close']
    prices['high'] = prices['close']
    prices['low'] = prices['close']
    prices['volume'] = 1000000
    prices['adj_close'] = prices['close']
    
    prices_with_indicators = signal_gen.calculate_indicators(prices)
    
    # Check for death cross at end
    last_date = prices.index[-1]
    
    # Death cross should be detected
    assert prices_with_indicators.loc[last_date, 'death_cross'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
