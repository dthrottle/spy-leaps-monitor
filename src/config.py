"""
Configuration module for SPY LEAPS strategy parameters
"""
from dataclasses import dataclass
from typing import Optional
import json


@dataclass
class StrategyConfig:
    """Strategy configuration parameters"""
    
    # Weekly buy parameters
    weekly_amount: float = 1000.0
    buy_weekday: int = 4  # 0=Monday, 4=Friday
    strike_moneyness: float = 0.0  # 0=ATM, positive=OTM, negative=ITM
    
    # Pause rules
    pause_drawdown_pct: float = 10.0
    pause_lookback_days: int = 100
    vix_threshold: float = 25.0
    
    # Liquidation rules
    liquidate_pct_from_200ma: float = 15.0
    liquidate_pct_from_peak: float = 18.0
    use_death_cross: bool = False
    
    # Resume rules
    resume_consec_days: int = 15
    resume_pct: float = 5.0  # Within 5% of peak
    
    # Risk management
    max_exposure_pct: float = 10.0
    pos_loss_pct: Optional[float] = None  # Per-position stop loss
    
    # Option parameters
    time_to_expiry_years: float = 1.0
    risk_free_rate: float = 0.045
    
    # Backtest parameters
    initial_capital: float = 100000.0
    start_date: str = "2010-01-01"
    end_date: Optional[str] = None
    
    def to_dict(self):
        """Convert config to dictionary"""
        return {
            'weekly_amount': self.weekly_amount,
            'buy_weekday': self.buy_weekday,
            'strike_moneyness': self.strike_moneyness,
            'pause_drawdown_pct': self.pause_drawdown_pct,
            'pause_lookback_days': self.pause_lookback_days,
            'vix_threshold': self.vix_threshold,
            'liquidate_pct_from_200ma': self.liquidate_pct_from_200ma,
            'liquidate_pct_from_peak': self.liquidate_pct_from_peak,
            'use_death_cross': self.use_death_cross,
            'resume_consec_days': self.resume_consec_days,
            'resume_pct': self.resume_pct,
            'max_exposure_pct': self.max_exposure_pct,
            'pos_loss_pct': self.pos_loss_pct,
            'time_to_expiry_years': self.time_to_expiry_years,
            'risk_free_rate': self.risk_free_rate,
            'initial_capital': self.initial_capital,
            'start_date': self.start_date,
            'end_date': self.end_date
        }
    
    def to_json(self):
        """Convert config to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, config_dict):
        """Create config from dictionary"""
        return cls(**config_dict)
    
    @classmethod
    def from_json(cls, json_str):
        """Create config from JSON string"""
        return cls.from_dict(json.loads(json_str))


# Database configuration
DB_PATH = "data/spy_leaps.db"
