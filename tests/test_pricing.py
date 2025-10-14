"""
Unit tests for pricing module
"""
import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pricing import (
    black_scholes_call,
    calculate_historical_volatility,
    get_strike_price,
    calculate_option_premium,
    calculate_greeks
)


def test_black_scholes_call():
    """Test Black-Scholes call pricing"""
    # Known values (approximately)
    S = 100.0
    K = 100.0
    T = 1.0
    r = 0.05
    sigma = 0.20
    
    price = black_scholes_call(S, K, T, r, sigma)
    
    # Expected value is approximately $10.45
    assert 9.0 < price < 11.0, f"Expected price around 10.45, got {price}"
    
    # Test ITM option
    price_itm = black_scholes_call(110, 100, 1.0, 0.05, 0.20)
    assert price_itm > price, "ITM option should be more expensive than ATM"
    
    # Test expired option
    price_expired = black_scholes_call(110, 100, 0, 0.05, 0.20)
    assert price_expired == 10.0, "Expired ITM option should equal intrinsic value"


def test_calculate_historical_volatility():
    """Test historical volatility calculation"""
    # Create synthetic price series with known volatility
    np.random.seed(42)
    prices = np.exp(np.cumsum(np.random.normal(0, 0.01, 100)))
    prices = prices * 100
    
    vol = calculate_historical_volatility(prices, window=30)
    
    # Volatility should be positive and reasonable
    assert vol > 0, "Volatility should be positive"
    assert vol < 1.0, "Volatility should be less than 100%"


def test_get_strike_price():
    """Test strike price calculation"""
    spot = 450.5
    
    # ATM strike
    strike_atm = get_strike_price(spot, 0.0)
    assert abs(strike_atm - spot) < 1.0, "ATM strike should be close to spot"
    
    # OTM strike (5%)
    strike_otm = get_strike_price(spot, 5.0)
    assert strike_otm > spot, "OTM call strike should be above spot"
    assert abs(strike_otm - spot * 1.05) < 2.0, "OTM strike should be ~5% above spot"
    
    # ITM strike (-5%)
    strike_itm = get_strike_price(spot, -5.0)
    assert strike_itm < spot, "ITM call strike should be below spot"


def test_calculate_option_premium():
    """Test option premium calculation"""
    spot_price = 450.0
    strike = 450.0
    days_to_expiry = 365
    risk_free_rate = 0.045
    
    # Create synthetic historical prices
    historical_prices = np.linspace(400, 450, 100)
    
    premium = calculate_option_premium(
        spot_price, strike, days_to_expiry,
        risk_free_rate, historical_prices
    )
    
    # Premium should be positive
    assert premium > 0, "Premium should be positive"
    
    # ATM 1-year option should have substantial time value
    assert premium > 15.0, "ATM 1-year option should have significant premium"
    
    # Test expired option
    premium_expired = calculate_option_premium(
        460, 450, 0, risk_free_rate, historical_prices
    )
    assert premium_expired == 10.0, "Expired option should equal intrinsic value"


def test_calculate_greeks():
    """Test Greeks calculation"""
    S = 450.0
    K = 450.0
    T = 1.0
    r = 0.045
    sigma = 0.20
    
    greeks = calculate_greeks(S, K, T, r, sigma)
    
    # Check delta
    assert 0.4 < greeks['delta'] < 0.7, "ATM delta should be around 0.5-0.6"
    
    # Check gamma
    assert greeks['gamma'] > 0, "Gamma should be positive"
    
    # Check theta
    assert greeks['theta'] < 0, "Theta should be negative (time decay)"
    
    # Check vega
    assert greeks['vega'] > 0, "Vega should be positive"
    
    # Test expired option Greeks
    greeks_expired = calculate_greeks(S, K, 0, r, sigma)
    assert greeks_expired['delta'] in [0.0, 1.0], "Expired delta should be 0 or 1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
