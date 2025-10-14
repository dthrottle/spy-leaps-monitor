"""
Signal generation module for pause/liquidation logic
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional


class SignalGenerator:
    """Generate trading signals based on strategy rules"""
    
    def __init__(self, config):
        self.config = config
        self.pause_state = False
        self.days_above_200ma = 0
    
    def calculate_indicators(self, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators
        
        Args:
            prices: DataFrame with OHLCV data
        
        Returns:
            DataFrame with added indicators
        """
        df = prices.copy()
        
        # Moving averages
        df['ma_50'] = df['close'].rolling(window=50).mean()
        df['ma_200'] = df['close'].rolling(window=200).mean()
        
        # Rolling high for drawdown calculation
        df['rolling_high'] = df['close'].rolling(
            window=self.config.pause_lookback_days
        ).max()
        
        # Drawdown from recent high
        df['drawdown_pct'] = ((df['close'] - df['rolling_high']) / df['rolling_high']) * 100
        
        # Distance from 200-day MA
        df['pct_from_200ma'] = ((df['close'] - df['ma_200']) / df['ma_200']) * 100
        
        # Death cross indicator (50-day MA crosses below 200-day MA)
        df['death_cross'] = (df['ma_50'] < df['ma_200']).astype(int)
        
        return df
    
    def check_pause_condition(
        self, 
        date: pd.Timestamp,
        prices_with_indicators: pd.DataFrame,
        vix_data: Optional[pd.DataFrame] = None
    ) -> Tuple[bool, str]:
        """
        Check if buying should be paused
        
        Args:
            date: Current date
            prices_with_indicators: Price data with indicators
            vix_data: VIX data (optional)
        
        Returns:
            Tuple of (should_pause, reason)
        """
        if date not in prices_with_indicators.index:
            return False, ""
        
        row = prices_with_indicators.loc[date]
        
        # Check drawdown from recent high
        if pd.notna(row['drawdown_pct']):
            if row['drawdown_pct'] <= -self.config.pause_drawdown_pct:
                return True, f"Drawdown {row['drawdown_pct']:.1f}% exceeds threshold"
        
        # Check VIX threshold
        if vix_data is not None and date in vix_data.index:
            vix_close = vix_data.loc[date, 'close']
            if vix_close > self.config.vix_threshold:
                return True, f"VIX {vix_close:.1f} exceeds threshold {self.config.vix_threshold}"
        
        return False, ""
    
    def check_liquidate_condition(
        self,
        date: pd.Timestamp,
        prices_with_indicators: pd.DataFrame
    ) -> Tuple[bool, str]:
        """
        Check if positions should be liquidated
        
        Args:
            date: Current date
            prices_with_indicators: Price data with indicators
        
        Returns:
            Tuple of (should_liquidate, reason)
        """
        if date not in prices_with_indicators.index:
            return False, ""
        
        row = prices_with_indicators.loc[date]
        
        # Check distance from 200-day MA
        if pd.notna(row['pct_from_200ma']):
            if row['pct_from_200ma'] <= -self.config.liquidate_pct_from_200ma:
                return True, f"Price {row['pct_from_200ma']:.1f}% below 200-day MA"
        
        # Check drawdown from peak
        if pd.notna(row['drawdown_pct']):
            if row['drawdown_pct'] <= -self.config.liquidate_pct_from_peak:
                return True, f"Drawdown {row['drawdown_pct']:.1f}% from peak exceeds liquidation threshold"
        
        # Check death cross if enabled
        if self.config.use_death_cross:
            if row['death_cross'] == 1:
                return True, "Death cross detected (50-day MA < 200-day MA)"
        
        return False, ""
    
    def check_resume_condition(
        self,
        date: pd.Timestamp,
        prices_with_indicators: pd.DataFrame
    ) -> Tuple[bool, str]:
        """
        Check if buying should resume
        
        Args:
            date: Current date
            prices_with_indicators: Price data with indicators
        
        Returns:
            Tuple of (should_resume, reason)
        """
        if date not in prices_with_indicators.index:
            return False, ""
        
        row = prices_with_indicators.loc[date]
        
        # Check if price is above 200-day MA
        if pd.notna(row['ma_200']):
            if row['close'] > row['ma_200']:
                self.days_above_200ma += 1
                if self.days_above_200ma >= self.config.resume_consec_days:
                    self.days_above_200ma = 0  # Reset counter
                    return True, f"Price above 200-day MA for {self.config.resume_consec_days} consecutive days"
            else:
                self.days_above_200ma = 0
        
        # Check if drawdown has recovered
        if pd.notna(row['drawdown_pct']):
            if row['drawdown_pct'] >= -self.config.resume_pct:
                return True, f"Drawdown recovered to {row['drawdown_pct']:.1f}%"
        
        return False, ""
    
    def is_buy_day(self, date: pd.Timestamp) -> bool:
        """
        Check if current date is a buy day
        
        Args:
            date: Current date
        
        Returns:
            True if it's a buy day
        """
        return date.weekday() == self.config.buy_weekday
