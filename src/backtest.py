"""
Backtest engine for SPY LEAPS strategy
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from .config import StrategyConfig
from .db import Database
from .pricing import calculate_option_premium, get_strike_price
from .signals import SignalGenerator


class Position:
    """Represents a single LEAP position"""
    
    def __init__(self, entry_date: str, entry_price: float, strike: float, 
                 premium: float, contracts: int, expiry_date: str):
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.strike = strike
        self.entry_premium = premium
        self.contracts = contracts
        self.expiry_date = expiry_date
        self.exit_date = None
        self.exit_price = None
        self.exit_premium = None
        self.pnl = 0.0
    
    def mark_to_market(self, current_price: float, current_date: str, 
                       risk_free_rate: float, historical_prices: np.ndarray) -> float:
        """
        Calculate current value of position
        
        Args:
            current_price: Current underlying price
            current_date: Current date
            risk_free_rate: Risk-free rate
            historical_prices: Historical prices for volatility
        
        Returns:
            Current position value
        """
        entry_dt = pd.to_datetime(self.entry_date)
        current_dt = pd.to_datetime(current_date)
        expiry_dt = pd.to_datetime(self.expiry_date)
        
        days_to_expiry = (expiry_dt - current_dt).days
        
        if days_to_expiry <= 0:
            # Option expired
            current_premium = max(current_price - self.strike, 0)
        else:
            current_premium = calculate_option_premium(
                current_price, self.strike, days_to_expiry,
                risk_free_rate, historical_prices
            )
        
        return current_premium * self.contracts * 100  # Contract multiplier
    
    def close(self, exit_date: str, exit_price: float, exit_premium: float):
        """Close the position"""
        self.exit_date = exit_date
        self.exit_price = exit_price
        self.exit_premium = exit_premium
        self.pnl = (exit_premium - self.entry_premium) * self.contracts * 100
    
    def to_dict(self) -> Dict:
        """Convert position to dictionary"""
        return {
            'entry_date': self.entry_date,
            'exit_date': self.exit_date,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'option_strike': self.strike,
            'option_entry_premium': self.entry_premium,
            'option_exit_premium': self.exit_premium,
            'contracts': self.contracts,
            'pnl': self.pnl,
            'notes': ''
        }


class BacktestEngine:
    """Core backtesting engine"""
    
    def __init__(self, config: StrategyConfig, db: Database):
        self.config = config
        self.db = db
        self.signal_gen = SignalGenerator(config)
        
        self.positions: List[Position] = []
        self.closed_positions: List[Position] = []
        self.equity_curve = []
        self.signals = []
        
        self.cash = config.initial_capital
        self.pause_buying = False
        
    def load_data(self) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
        """Load price data from database"""
        prices = self.db.load_prices('prices', self.config.start_date, self.config.end_date)
        
        try:
            vix = self.db.load_prices('vix', self.config.start_date, self.config.end_date)
        except:
            vix = None
        
        return prices, vix
    
    def calculate_exposure(self) -> float:
        """Calculate current exposure as percentage of initial capital"""
        total_premium = sum(
            pos.entry_premium * pos.contracts * 100 
            for pos in self.positions
        )
        return (total_premium / self.config.initial_capital) * 100
    
    def open_position(self, date: str, price: float, historical_prices: np.ndarray):
        """
        Open a new LEAP position
        
        Args:
            date: Entry date
            price: Current underlying price
            historical_prices: Historical prices for pricing
        """
        # Calculate strike
        strike = get_strike_price(price, self.config.strike_moneyness)
        
        # Calculate expiry date (1 year from now)
        entry_dt = pd.to_datetime(date)
        expiry_dt = entry_dt + timedelta(days=int(self.config.time_to_expiry_years * 365))
        
        # Calculate option premium
        premium = calculate_option_premium(
            price, strike, 365,
            self.config.risk_free_rate,
            historical_prices
        )
        
        # Calculate number of contracts based on weekly amount
        # Each contract costs premium * 100
        contract_cost = premium * 100
        if contract_cost > 0:
            contracts = max(1, int(self.config.weekly_amount / contract_cost))
        else:
            contracts = 1
        
        total_cost = premium * contracts * 100
        
        # Check if we have enough cash and exposure limits
        if total_cost > self.cash:
            return
        
        if self.calculate_exposure() + (total_cost / self.config.initial_capital * 100) > self.config.max_exposure_pct:
            self.signals.append({
                'date': date,
                'signal_type': 'MAX_EXPOSURE',
                'details': 'Maximum exposure reached, skipping buy'
            })
            return
        
        # Create position
        position = Position(
            date, price, strike, premium, contracts,
            expiry_dt.strftime('%Y-%m-%d')
        )
        
        self.positions.append(position)
        self.cash -= total_cost
        
        self.signals.append({
            'date': date,
            'signal_type': 'BUY',
            'details': f'Bought {contracts} contracts, strike {strike:.0f}, premium ${premium:.2f}'
        })
    
    def close_all_positions(self, date: str, price: float, 
                           risk_free_rate: float, historical_prices: np.ndarray,
                           reason: str):
        """
        Close all open positions
        
        Args:
            date: Exit date
            price: Current underlying price
            risk_free_rate: Risk-free rate
            historical_prices: Historical prices
            reason: Reason for closing
        """
        for position in self.positions:
            # Calculate days to expiry
            entry_dt = pd.to_datetime(position.entry_date)
            current_dt = pd.to_datetime(date)
            expiry_dt = pd.to_datetime(position.expiry_date)
            days_to_expiry = (expiry_dt - current_dt).days
            
            # Calculate exit premium
            if days_to_expiry <= 0:
                exit_premium = max(price - position.strike, 0)
            else:
                exit_premium = calculate_option_premium(
                    price, position.strike, days_to_expiry,
                    risk_free_rate, historical_prices
                )
            
            # Close position
            position.close(date, price, exit_premium)
            
            # Add cash back
            proceeds = exit_premium * position.contracts * 100
            self.cash += proceeds
            
            # Save to database
            self.db.save_trade(position.to_dict())
            
            self.closed_positions.append(position)
        
        self.positions = []
        
        self.signals.append({
            'date': date,
            'signal_type': 'LIQUIDATE',
            'details': reason
        })
    
    def mark_to_market_all(self, date: str, price: float, historical_prices: np.ndarray) -> float:
        """
        Mark all positions to market
        
        Args:
            date: Current date
            price: Current price
            historical_prices: Historical prices
        
        Returns:
            Total portfolio value
        """
        positions_value = sum(
            pos.mark_to_market(price, date, self.config.risk_free_rate, historical_prices)
            for pos in self.positions
        )
        
        return self.cash + positions_value
    
    def run(self) -> Dict:
        """
        Run the backtest
        
        Returns:
            Dictionary with results
        """
        # Load data
        prices, vix = self.load_data()
        
        if len(prices) == 0:
            raise ValueError("No price data available")
        
        # Calculate indicators
        prices_with_indicators = self.signal_gen.calculate_indicators(prices)
        
        # Clear existing data
        self.db.clear_trades()
        self.db.clear_signals()
        
        # Initialize
        self.positions = []
        self.closed_positions = []
        self.equity_curve = []
        self.signals = []
        self.cash = self.config.initial_capital
        self.pause_buying = False
        
        # Iterate through dates
        for i, (date, row) in enumerate(prices.iterrows()):
            current_price = row['close']
            
            # Get historical prices for volatility calculation
            historical_prices = prices['close'].iloc[:i+1].values
            
            # Mark to market
            portfolio_value = self.mark_to_market_all(
                date.strftime('%Y-%m-%d'), current_price, historical_prices
            )
            
            self.equity_curve.append({
                'date': date,
                'value': portfolio_value,
                'spy_price': current_price,
                'positions': len(self.positions)
            })
            
            # Check liquidation condition first
            should_liquidate, liquidate_reason = self.signal_gen.check_liquidate_condition(
                date, prices_with_indicators
            )
            
            if should_liquidate and len(self.positions) > 0:
                self.close_all_positions(
                    date.strftime('%Y-%m-%d'), current_price,
                    self.config.risk_free_rate, historical_prices,
                    liquidate_reason
                )
                self.pause_buying = True
                continue
            
            # Check resume condition if paused
            if self.pause_buying:
                should_resume, resume_reason = self.signal_gen.check_resume_condition(
                    date, prices_with_indicators
                )
                
                if should_resume:
                    self.pause_buying = False
                    self.signals.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'signal_type': 'RESUME',
                        'details': resume_reason
                    })
            
            # Check if it's a buy day and we're not paused
            if self.signal_gen.is_buy_day(date) and not self.pause_buying:
                # Check pause condition
                should_pause, pause_reason = self.signal_gen.check_pause_condition(
                    date, prices_with_indicators, vix
                )
                
                if should_pause:
                    self.pause_buying = True
                    self.signals.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'signal_type': 'PAUSE',
                        'details': pause_reason
                    })
                else:
                    # Execute buy
                    self.open_position(
                        date.strftime('%Y-%m-%d'), current_price, historical_prices
                    )
        
        # Close any remaining positions at end
        if len(self.positions) > 0:
            last_date = prices.index[-1].strftime('%Y-%m-%d')
            last_price = prices['close'].iloc[-1]
            historical_prices = prices['close'].values
            
            self.close_all_positions(
                last_date, last_price,
                self.config.risk_free_rate, historical_prices,
                "End of backtest period"
            )
        
        # Save signals to database
        for signal in self.signals:
            self.db.save_signal(signal['date'], signal['signal_type'], signal['details'])
        
        # Calculate metrics
        results = self.calculate_metrics(prices)
        
        return results
    
    def calculate_metrics(self, prices: pd.DataFrame) -> Dict:
        """Calculate performance metrics"""
        equity_df = pd.DataFrame(self.equity_curve)
        
        if len(equity_df) == 0:
            return {}
        
        equity_df.set_index('date', inplace=True)
        
        # Total return
        initial_value = self.config.initial_capital
        final_value = equity_df['value'].iloc[-1]
        total_return = ((final_value - initial_value) / initial_value) * 100
        
        # Calculate buy-and-hold return for comparison
        first_spy = equity_df['spy_price'].iloc[0]
        last_spy = equity_df['spy_price'].iloc[-1]
        buy_hold_return = ((last_spy - first_spy) / first_spy) * 100
        
        # CAGR
        years = len(equity_df) / 252
        cagr = ((final_value / initial_value) ** (1 / years) - 1) * 100 if years > 0 else 0
        
        # Max drawdown
        equity_df['peak'] = equity_df['value'].cummax()
        equity_df['drawdown'] = ((equity_df['value'] - equity_df['peak']) / equity_df['peak']) * 100
        max_drawdown = equity_df['drawdown'].min()
        
        # Win rate
        winning_trades = sum(1 for pos in self.closed_positions if pos.pnl > 0)
        total_trades = len(self.closed_positions)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Average win/loss
        wins = [pos.pnl for pos in self.closed_positions if pos.pnl > 0]
        losses = [pos.pnl for pos in self.closed_positions if pos.pnl < 0]
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        
        # Sharpe ratio
        equity_df['returns'] = equity_df['value'].pct_change()
        sharpe = (equity_df['returns'].mean() / equity_df['returns'].std() * np.sqrt(252)) if equity_df['returns'].std() > 0 else 0
        
        # Sortino ratio
        downside_returns = equity_df['returns'][equity_df['returns'] < 0]
        sortino = (equity_df['returns'].mean() / downside_returns.std() * np.sqrt(252)) if len(downside_returns) > 0 and downside_returns.std() > 0 else 0
        
        return {
            'total_return': total_return,
            'buy_hold_return': buy_hold_return,
            'cagr': cagr,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'final_value': final_value,
            'equity_curve': equity_df
        }
