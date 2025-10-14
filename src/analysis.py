"""
Analysis and plotting utilities
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List


def plot_equity_curve(equity_df: pd.DataFrame, config) -> go.Figure:
    """
    Plot strategy equity curve vs buy-and-hold
    
    Args:
        equity_df: DataFrame with equity curve data
        config: Strategy configuration
    
    Returns:
        Plotly figure
    """
    # Calculate buy-and-hold equity
    first_spy = equity_df['spy_price'].iloc[0]
    equity_df['buy_hold_value'] = (
        config.initial_capital * equity_df['spy_price'] / first_spy
    )
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=equity_df.index,
        y=equity_df['value'],
        mode='lines',
        name='LEAPS Strategy',
        line=dict(color='blue', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=equity_df.index,
        y=equity_df['buy_hold_value'],
        mode='lines',
        name='Buy & Hold SPY',
        line=dict(color='gray', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title='Portfolio Value: LEAPS Strategy vs Buy & Hold',
        xaxis_title='Date',
        yaxis_title='Portfolio Value ($)',
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    
    return fig


def plot_drawdown(equity_df: pd.DataFrame) -> go.Figure:
    """
    Plot drawdown chart
    
    Args:
        equity_df: DataFrame with equity curve data
    
    Returns:
        Plotly figure
    """
    equity_df = equity_df.copy()
    equity_df['peak'] = equity_df['value'].cummax()
    equity_df['drawdown'] = ((equity_df['value'] - equity_df['peak']) / equity_df['peak']) * 100
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=equity_df.index,
        y=equity_df['drawdown'],
        mode='lines',
        name='Drawdown',
        fill='tozeroy',
        line=dict(color='red', width=1)
    ))
    
    fig.update_layout(
        title='Strategy Drawdown',
        xaxis_title='Date',
        yaxis_title='Drawdown (%)',
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return fig


def plot_exposure(equity_df: pd.DataFrame) -> go.Figure:
    """
    Plot exposure over time
    
    Args:
        equity_df: DataFrame with equity curve data
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=equity_df.index,
        y=equity_df['positions'],
        mode='lines',
        name='Open Positions',
        fill='tozeroy',
        line=dict(color='green', width=2)
    ))
    
    fig.update_layout(
        title='Number of Open Positions Over Time',
        xaxis_title='Date',
        yaxis_title='Number of Positions',
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return fig


def plot_price_with_signals(prices: pd.DataFrame, signals: pd.DataFrame) -> go.Figure:
    """
    Plot SPY price with trading signals
    
    Args:
        prices: DataFrame with price data
        signals: DataFrame with signals
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    # Plot price
    fig.add_trace(go.Scatter(
        x=prices.index,
        y=prices['close'],
        mode='lines',
        name='SPY Close',
        line=dict(color='black', width=1)
    ))
    
    # Plot moving averages if available
    if 'ma_50' in prices.columns:
        fig.add_trace(go.Scatter(
            x=prices.index,
            y=prices['ma_50'],
            mode='lines',
            name='50-day MA',
            line=dict(color='blue', width=1, dash='dash')
        ))
    
    if 'ma_200' in prices.columns:
        fig.add_trace(go.Scatter(
            x=prices.index,
            y=prices['ma_200'],
            mode='lines',
            name='200-day MA',
            line=dict(color='red', width=1, dash='dash')
        ))
    
    # Add signals
    if len(signals) > 0:
        signals['date'] = pd.to_datetime(signals['date'])
        
        for signal_type, color, symbol in [
            ('BUY', 'green', 'triangle-up'),
            ('PAUSE', 'orange', 'x'),
            ('LIQUIDATE', 'red', 'triangle-down'),
            ('RESUME', 'blue', 'circle')
        ]:
            signal_data = signals[signals['signal_type'] == signal_type]
            if len(signal_data) > 0:
                # Merge with prices to get y-values
                merged = signal_data.merge(
                    prices.reset_index()[['date', 'close']], 
                    on='date', 
                    how='left'
                )
                
                fig.add_trace(go.Scatter(
                    x=merged['date'],
                    y=merged['close'],
                    mode='markers',
                    name=signal_type,
                    marker=dict(color=color, size=10, symbol=symbol),
                    text=merged['details'],
                    hovertemplate='%{text}<br>%{x}<extra></extra>'
                ))
    
    fig.update_layout(
        title='SPY Price with Trading Signals',
        xaxis_title='Date',
        yaxis_title='Price ($)',
        hovermode='x unified',
        template='plotly_white',
        height=600
    )
    
    return fig


def plot_trade_returns(trades: pd.DataFrame) -> go.Figure:
    """
    Plot histogram of trade returns
    
    Args:
        trades: DataFrame with trade data
    
    Returns:
        Plotly figure
    """
    if len(trades) == 0 or 'pnl' not in trades.columns:
        return go.Figure()
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=trades['pnl'],
        nbinsx=30,
        name='Trade P&L',
        marker=dict(
            color=trades['pnl'],
            colorscale='RdYlGn',
            cmin=-abs(trades['pnl'].max()),
            cmax=abs(trades['pnl'].max())
        )
    ))
    
    fig.update_layout(
        title='Distribution of Trade Returns',
        xaxis_title='P&L ($)',
        yaxis_title='Frequency',
        template='plotly_white',
        height=400
    )
    
    return fig


def plot_rolling_metrics(equity_df: pd.DataFrame, window: int = 60) -> go.Figure:
    """
    Plot rolling Sharpe ratio and volatility
    
    Args:
        equity_df: DataFrame with equity curve data
        window: Rolling window size
    
    Returns:
        Plotly figure
    """
    equity_df = equity_df.copy()
    equity_df['returns'] = equity_df['value'].pct_change()
    
    equity_df['rolling_sharpe'] = (
        equity_df['returns'].rolling(window).mean() / 
        equity_df['returns'].rolling(window).std() * np.sqrt(252)
    )
    
    equity_df['rolling_vol'] = (
        equity_df['returns'].rolling(window).std() * np.sqrt(252) * 100
    )
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Rolling Sharpe Ratio', 'Rolling Volatility (%)'),
        vertical_spacing=0.12
    )
    
    fig.add_trace(
        go.Scatter(
            x=equity_df.index,
            y=equity_df['rolling_sharpe'],
            mode='lines',
            name='Rolling Sharpe',
            line=dict(color='blue', width=2)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=equity_df.index,
            y=equity_df['rolling_vol'],
            mode='lines',
            name='Rolling Volatility',
            line=dict(color='red', width=2)
        ),
        row=2, col=1
    )
    
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Sharpe Ratio", row=1, col=1)
    fig.update_yaxes(title_text="Volatility (%)", row=2, col=1)
    
    fig.update_layout(
        height=600,
        template='plotly_white',
        showlegend=False
    )
    
    return fig


def create_metrics_summary(results: Dict) -> pd.DataFrame:
    """
    Create a summary table of metrics
    
    Args:
        results: Dictionary with backtest results
    
    Returns:
        DataFrame with metrics
    """
    metrics = {
        'Metric': [
            'Total Return',
            'Buy & Hold Return',
            'CAGR',
            'Max Drawdown',
            'Sharpe Ratio',
            'Sortino Ratio',
            'Win Rate',
            'Total Trades',
            'Winning Trades',
            'Losing Trades',
            'Avg Win',
            'Avg Loss',
            'Final Value'
        ],
        'Value': [
            f"{results.get('total_return', 0):.2f}%",
            f"{results.get('buy_hold_return', 0):.2f}%",
            f"{results.get('cagr', 0):.2f}%",
            f"{results.get('max_drawdown', 0):.2f}%",
            f"{results.get('sharpe_ratio', 0):.2f}",
            f"{results.get('sortino_ratio', 0):.2f}",
            f"{results.get('win_rate', 0):.2f}%",
            f"{results.get('total_trades', 0)}",
            f"{results.get('winning_trades', 0)}",
            f"{results.get('losing_trades', 0)}",
            f"${results.get('avg_win', 0):.2f}",
            f"${results.get('avg_loss', 0):.2f}",
            f"${results.get('final_value', 0):.2f}"
        ]
    }
    
    return pd.DataFrame(metrics)


def run_sensitivity_analysis(base_config, db, param_ranges: Dict) -> pd.DataFrame:
    """
    Run sensitivity analysis across parameter ranges
    
    Args:
        base_config: Base configuration
        db: Database instance
        param_ranges: Dictionary of parameter ranges
    
    Returns:
        DataFrame with sensitivity results
    """
    from .backtest import BacktestEngine
    
    results = []
    
    for param_name, values in param_ranges.items():
        for value in values:
            # Create modified config
            config = StrategyConfig(**base_config.to_dict())
            setattr(config, param_name, value)
            
            # Run backtest
            try:
                engine = BacktestEngine(config, db)
                backtest_results = engine.run()
                
                results.append({
                    'Parameter': param_name,
                    'Value': value,
                    'Total Return (%)': backtest_results.get('total_return', 0),
                    'CAGR (%)': backtest_results.get('cagr', 0),
                    'Max Drawdown (%)': backtest_results.get('max_drawdown', 0),
                    'Sharpe Ratio': backtest_results.get('sharpe_ratio', 0),
                    'Win Rate (%)': backtest_results.get('win_rate', 0),
                    'Total Trades': backtest_results.get('total_trades', 0)
                })
            except Exception as e:
                print(f"Error with {param_name}={value}: {e}")
    
    return pd.DataFrame(results)
