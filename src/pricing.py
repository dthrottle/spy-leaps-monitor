"""
Option pricing module using Black-Scholes model
"""
import numpy as np
from scipy.stats import norm
from typing import Optional


def black_scholes_call(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """
    Calculate Black-Scholes call option price
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free rate
        sigma: Volatility (annualized)
    
    Returns:
        Call option price
    """
    if T <= 0:
        return max(S - K, 0)
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return call_price


def calculate_historical_volatility(prices: np.ndarray, window: int = 30) -> float:
    """
    Calculate historical volatility from price series
    
    Args:
        prices: Array of prices
        window: Lookback window in days
    
    Returns:
        Annualized volatility
    """
    if len(prices) < 2:
        return 0.20  # Default volatility
    
    if len(prices) < window + 1:
        window = len(prices) - 1
    
    if window <= 0:
        return 0.20  # Default volatility
    
    # Calculate returns correctly
    price_slice = prices[-window-1:]
    if len(price_slice) < 2:
        return 0.20
    
    returns = np.log(price_slice[1:] / price_slice[:-1])
    
    if len(returns) == 0:
        return 0.20
    
    volatility = np.std(returns) * np.sqrt(252)  # Annualize
    
    return volatility if volatility > 0 else 0.20


def get_strike_price(spot: float, moneyness: float, strike_spacing: float = 1.0) -> float:
    """
    Get strike price based on moneyness
    
    Args:
        spot: Current spot price
        moneyness: Percentage (0=ATM, 5=5% OTM for calls)
        strike_spacing: Strike price increment
    
    Returns:
        Strike price
    """
    target_strike = spot * (1 + moneyness / 100)
    # Round to nearest strike spacing
    strike = round(target_strike / strike_spacing) * strike_spacing
    return strike


def calculate_option_premium(
    spot_price: float,
    strike: float,
    days_to_expiry: float,
    risk_free_rate: float,
    historical_prices: np.ndarray,
    vol_window: int = 30
) -> float:
    """
    Calculate synthetic option premium using Black-Scholes
    
    Args:
        spot_price: Current underlying price
        strike: Option strike price
        days_to_expiry: Days until expiration
        risk_free_rate: Risk-free interest rate
        historical_prices: Historical price series for volatility calculation
        vol_window: Window for volatility calculation
    
    Returns:
        Option premium
    """
    T = days_to_expiry / 365.0
    
    if T <= 0:
        return max(spot_price - strike, 0)
    
    sigma = calculate_historical_volatility(historical_prices, vol_window)
    
    premium = black_scholes_call(spot_price, strike, T, risk_free_rate, sigma)
    return premium


def calculate_greeks(S: float, K: float, T: float, r: float, sigma: float) -> dict:
    """
    Calculate option Greeks
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free rate
        sigma: Volatility
    
    Returns:
        Dictionary with delta, gamma, theta, vega
    """
    if T <= 0:
        return {
            'delta': 1.0 if S > K else 0.0,
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0
        }
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    delta = norm.cdf(d1)
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
             - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
    vega = S * norm.pdf(d1) * np.sqrt(T) / 100
    
    return {
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega
    }
