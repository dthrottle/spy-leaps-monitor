"""
Main Streamlit application for SPY LEAPS Monitor
"""
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import StrategyConfig, DB_PATH
from src.db import Database
from src.backtest import BacktestEngine
from src.signals import SignalGenerator
from src.analysis import (
    plot_equity_curve, plot_drawdown, plot_exposure,
    plot_price_with_signals, plot_trade_returns,
    plot_rolling_metrics, create_metrics_summary,
    run_sensitivity_analysis
)

# Page config
st.set_page_config(
    page_title="SPY LEAPS Monitor",
    page_icon="📈",
    layout="wide"
)

# Initialize session state
if 'db' not in st.session_state:
    st.session_state.db = Database(DB_PATH)

if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = None


def download_data(ticker: str, start_date: str, end_date: str = None):
    """Download data from Yahoo Finance"""
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    with st.spinner(f'Downloading {ticker} data...'):
        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)
        
        if len(data) == 0:
            st.error(f"No data retrieved for {ticker}")
            return None
        
        # Handle multi-index columns from yfinance
        if isinstance(data.columns, pd.MultiIndex):
            # Flatten multi-index columns
            data.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in data.columns.values]
            # Clean up the column names
            data.columns = [col.split('_')[0].lower() if '_' in col else col.lower() for col in data.columns]
        else:
            # Rename columns to lowercase for single-index
            data.columns = [col.lower().replace(' ', '_') for col in data.columns]
        
        # Ensure adj_close exists
        if 'adj' in data.columns:
            data.rename(columns={'adj': 'adj_close'}, inplace=True)
        if 'adj_close' not in data.columns and 'close' in data.columns:
            data['adj_close'] = data['close']
        
        # Ensure we have the required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in data.columns:
                st.error(f"Missing required column: {col}")
                return None
        
        return data


def load_or_download_data(db: Database, config: StrategyConfig):
    """Load data from database or download if not available"""
    try:
        prices = db.load_prices('prices', config.start_date, config.end_date)
        if len(prices) < 252:  # Less than 1 year of data
            raise ValueError("Insufficient data in database")
    except:
        prices = download_data('SPY', config.start_date, config.end_date)
        if prices is not None:
            db.save_prices(prices, 'prices')
    
    try:
        vix = db.load_prices('vix', config.start_date, config.end_date)
    except:
        vix = download_data('^VIX', config.start_date, config.end_date)
        if vix is not None:
            db.save_prices(vix, 'vix')
    
    return prices is not None


# Sidebar navigation
st.sidebar.title("📈 SPY LEAPS Monitor")
page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Backtest", "Trades", "Sensitivity", "Signals", "Data Management"]
)

# Sidebar - Data management
with st.sidebar.expander("Data Management", expanded=False):
    col1, col2 = st.columns(2)
    
    if col1.button("Download SPY Data"):
        if download_data('SPY', '2010-01-01') is not None:
            st.session_state.db.save_prices(
                download_data('SPY', '2010-01-01'), 'prices'
            )
            st.success("SPY data downloaded")
    
    if col2.button("Download VIX Data"):
        if download_data('^VIX', '2010-01-01') is not None:
            st.session_state.db.save_prices(
                download_data('^VIX', '2010-01-01'), 'vix'
            )
            st.success("VIX data downloaded")
    
    if st.button("Reset Database", type="secondary"):
        st.session_state.db.reset_database()
        st.success("Database reset")

# Main content
if page == "Overview":
    st.title("📊 Overview")
    st.markdown("---")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        prices = st.session_state.db.load_prices('prices')
        if len(prices) > 0:
            latest_price = prices['close'].iloc[-1]
            latest_date = prices.index[-1]
            
            col1.metric("Latest SPY Price", f"${latest_price:.2f}")
            col2.metric("Data Updated", latest_date.strftime('%Y-%m-%d'))
            
            # Calculate simple metrics
            ma_50 = prices['close'].rolling(50).mean().iloc[-1]
            ma_200 = prices['close'].rolling(200).mean().iloc[-1]
            
            col3.metric("50-day MA", f"${ma_50:.2f}")
            col4.metric("200-day MA", f"${ma_200:.2f}")
    except:
        st.warning("No data available. Please download data using the sidebar.")
    
    st.markdown("---")
    
    # Recent signals
    st.subheader("Recent Signals")
    try:
        signals = st.session_state.db.load_signals()
        if len(signals) > 0:
            st.dataframe(signals.tail(10), use_container_width=True)
        else:
            st.info("No signals recorded. Run a backtest to generate signals.")
    except:
        st.info("No signals available.")
    
    # Portfolio status
    st.markdown("---")
    st.subheader("Portfolio Status")
    
    if st.session_state.backtest_results:
        results = st.session_state.backtest_results
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Return", f"{results.get('total_return', 0):.2f}%")
        col2.metric("Max Drawdown", f"{results.get('max_drawdown', 0):.2f}%")
        col3.metric("Sharpe Ratio", f"{results.get('sharpe_ratio', 0):.2f}")
    else:
        st.info("Run a backtest to see portfolio status.")

elif page == "Backtest":
    st.title("🔬 Backtest Configuration")
    st.markdown("---")
    
    # Configuration parameters
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Strategy Parameters")
        
        weekly_amount = st.number_input(
            "Weekly Investment ($)",
            min_value=100.0,
            max_value=10000.0,
            value=1000.0,
            step=100.0
        )
        
        strike_moneyness = st.slider(
            "Strike Moneyness (%)",
            min_value=-10.0,
            max_value=10.0,
            value=0.0,
            step=1.0,
            help="0% = ATM, positive = OTM"
        )
        
        initial_capital = st.number_input(
            "Initial Capital ($)",
            min_value=10000.0,
            max_value=1000000.0,
            value=100000.0,
            step=10000.0
        )
        
        buy_weekday = st.selectbox(
            "Buy Day",
            options=[0, 1, 2, 3, 4],
            format_func=lambda x: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'][x],
            index=4
        )
    
    with col2:
        st.subheader("Risk Parameters")
        
        pause_drawdown_pct = st.slider(
            "Pause Drawdown Threshold (%)",
            min_value=5.0,
            max_value=20.0,
            value=10.0,
            step=1.0
        )
        
        liquidate_pct_from_200ma = st.slider(
            "Liquidate % from 200-day MA",
            min_value=5.0,
            max_value=25.0,
            value=15.0,
            step=1.0
        )
        
        liquidate_pct_from_peak = st.slider(
            "Liquidate % from Peak",
            min_value=10.0,
            max_value=30.0,
            value=18.0,
            step=1.0
        )
        
        vix_threshold = st.slider(
            "VIX Pause Threshold",
            min_value=15.0,
            max_value=40.0,
            value=25.0,
            step=1.0
        )
        
        max_exposure_pct = st.slider(
            "Max Exposure (%)",
            min_value=5.0,
            max_value=20.0,
            value=10.0,
            step=1.0
        )
    
    # Date range
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=pd.to_datetime("2015-01-01"),
            min_value=pd.to_datetime("2010-01-01"),
            max_value=pd.to_datetime("2024-12-31")
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            min_value=pd.to_datetime("2010-01-01"),
            max_value=datetime.now()
        )
    
    # Run backtest button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    if col1.button("🚀 Run Backtest", type="primary", use_container_width=True):
        # Create configuration
        config = StrategyConfig(
            weekly_amount=weekly_amount,
            buy_weekday=buy_weekday,
            strike_moneyness=strike_moneyness,
            pause_drawdown_pct=pause_drawdown_pct,
            liquidate_pct_from_200ma=liquidate_pct_from_200ma,
            liquidate_pct_from_peak=liquidate_pct_from_peak,
            vix_threshold=vix_threshold,
            max_exposure_pct=max_exposure_pct,
            initial_capital=initial_capital,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        # Load or download data
        if load_or_download_data(st.session_state.db, config):
            # Run backtest
            with st.spinner("Running backtest..."):
                try:
                    engine = BacktestEngine(config, st.session_state.db)
                    results = engine.run()
                    st.session_state.backtest_results = results
                    st.success("✅ Backtest completed!")
                except Exception as e:
                    st.error(f"Error running backtest: {str(e)}")
                    st.exception(e)
        else:
            st.error("Failed to load data")
    
    if col2.button("📋 Export Results", use_container_width=True):
        if st.session_state.backtest_results:
            # Export trades
            trades = st.session_state.db.load_trades()
            if len(trades) > 0:
                csv = trades.to_csv(index=False)
                st.download_button(
                    "Download Trades CSV",
                    csv,
                    "trades.csv",
                    "text/csv"
                )
        else:
            st.warning("No results to export. Run a backtest first.")
    
    # Display results
    if st.session_state.backtest_results:
        st.markdown("---")
        st.subheader("📈 Results")
        
        results = st.session_state.backtest_results
        
        # Metrics summary
        metrics_df = create_metrics_summary(results)
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.dataframe(metrics_df, hide_index=True, use_container_width=True)
        
        with col2:
            # Equity curve
            if 'equity_curve' in results:
                fig = plot_equity_curve(results['equity_curve'], config)
                st.plotly_chart(fig, use_container_width=True)
        
        # Additional charts
        st.markdown("---")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "Drawdown", "Exposure", "Trade Returns", "Rolling Metrics"
        ])
        
        with tab1:
            if 'equity_curve' in results:
                fig = plot_drawdown(results['equity_curve'])
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            if 'equity_curve' in results:
                fig = plot_exposure(results['equity_curve'])
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            trades = st.session_state.db.load_trades()
            if len(trades) > 0:
                fig = plot_trade_returns(trades)
                st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            if 'equity_curve' in results:
                fig = plot_rolling_metrics(results['equity_curve'])
                st.plotly_chart(fig, use_container_width=True)

elif page == "Trades":
    st.title("💼 Trade History")
    st.markdown("---")
    
    # Load trades
    trades = st.session_state.db.load_trades()
    
    if len(trades) > 0:
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        total_pnl = trades['pnl'].sum()
        winning_trades = len(trades[trades['pnl'] > 0])
        losing_trades = len(trades[trades['pnl'] < 0])
        win_rate = (winning_trades / len(trades)) * 100 if len(trades) > 0 else 0
        
        col1.metric("Total P&L", f"${total_pnl:,.2f}")
        col2.metric("Winning Trades", winning_trades)
        col3.metric("Losing Trades", losing_trades)
        col4.metric("Win Rate", f"{win_rate:.1f}%")
        
        st.markdown("---")
        
        # Trades table
        st.subheader("All Trades")
        
        # Format for display
        display_trades = trades.copy()
        if 'pnl' in display_trades.columns:
            display_trades['pnl'] = display_trades['pnl'].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(display_trades, use_container_width=True, height=600)
        
        # Export button
        csv = trades.to_csv(index=False)
        st.download_button(
            "📥 Download Trades CSV",
            csv,
            "trades.csv",
            "text/csv"
        )
    else:
        st.info("No trades recorded. Run a backtest to generate trades.")

elif page == "Sensitivity":
    st.title("🔍 Sensitivity Analysis")
    st.markdown("---")
    
    st.write("Analyze how different parameter values affect strategy performance.")
    
    # Base configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Base Configuration")
        
        base_weekly_amount = st.number_input(
            "Base Weekly Amount ($)",
            value=1000.0,
            step=100.0
        )
        
        base_initial_capital = st.number_input(
            "Initial Capital ($)",
            value=100000.0,
            step=10000.0
        )
    
    with col2:
        st.subheader("Parameter to Sweep")
        
        param_to_sweep = st.selectbox(
            "Parameter",
            [
                "pause_drawdown_pct",
                "liquidate_pct_from_200ma",
                "liquidate_pct_from_peak",
                "weekly_amount",
                "vix_threshold"
            ]
        )
    
    # Define ranges
    st.markdown("---")
    st.subheader("Parameter Range")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_val = st.number_input("Min Value", value=5.0, step=1.0)
    
    with col2:
        max_val = st.number_input("Max Value", value=20.0, step=1.0)
    
    with col3:
        step_val = st.number_input("Step", value=5.0, step=1.0)
    
    # Date range
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=pd.to_datetime("2015-01-01"),
            key="sens_start"
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            key="sens_end"
        )
    
    # Run sensitivity analysis
    if st.button("🚀 Run Sensitivity Analysis", type="primary"):
        # Create base config
        base_config = StrategyConfig(
            weekly_amount=base_weekly_amount,
            initial_capital=base_initial_capital,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        # Load or download data
        if load_or_download_data(st.session_state.db, base_config):
            # Generate parameter range
            param_range = np.arange(min_val, max_val + step_val, step_val)
            param_ranges = {param_to_sweep: param_range}
            
            # Run sensitivity analysis
            with st.spinner("Running sensitivity analysis..."):
                try:
                    sensitivity_results = run_sensitivity_analysis(
                        base_config,
                        st.session_state.db,
                        param_ranges
                    )
                    
                    st.success("✅ Sensitivity analysis completed!")
                    
                    # Display results
                    st.markdown("---")
                    st.subheader("Results")
                    
                    st.dataframe(sensitivity_results, use_container_width=True)
                    
                    # Plot results
                    import plotly.express as px
                    
                    fig = px.line(
                        sensitivity_results,
                        x='Value',
                        y=['Total Return (%)', 'CAGR (%)', 'Sharpe Ratio'],
                        title=f'Sensitivity to {param_to_sweep}',
                        labels={'value': 'Metric Value', 'Value': param_to_sweep}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Export
                    csv = sensitivity_results.to_csv(index=False)
                    st.download_button(
                        "📥 Download Results CSV",
                        csv,
                        "sensitivity_results.csv",
                        "text/csv"
                    )
                    
                except Exception as e:
                    st.error(f"Error running sensitivity analysis: {str(e)}")
                    st.exception(e)
        else:
            st.error("Failed to load data")

elif page == "Signals":
    st.title("🚦 Trading Signals")
    st.markdown("---")
    
    # Load signals
    signals = st.session_state.db.load_signals()
    
    if len(signals) > 0:
        # Signal type filter
        signal_types = ['All'] + signals['signal_type'].unique().tolist()
        selected_type = st.selectbox("Filter by Signal Type", signal_types)
        
        if selected_type != 'All':
            filtered_signals = signals[signals['signal_type'] == selected_type]
        else:
            filtered_signals = signals
        
        # Display signals
        st.dataframe(filtered_signals, use_container_width=True, height=600)
        
        # Export
        csv = filtered_signals.to_csv(index=False)
        st.download_button(
            "📥 Download Signals CSV",
            csv,
            "signals.csv",
            "text/csv"
        )
        
        # Chart
        try:
            prices = st.session_state.db.load_prices('prices')
            signal_gen = SignalGenerator(StrategyConfig())
            prices_with_indicators = signal_gen.calculate_indicators(prices)
            
            fig = plot_price_with_signals(prices_with_indicators, signals)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not generate chart: {str(e)}")
    else:
        st.info("No signals recorded. Run a backtest to generate signals.")

elif page == "Data Management":
    st.title("💾 Data Management")
    st.markdown("---")
    
    # Data download section
    st.subheader("Download Historical Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ticker = st.text_input("Ticker Symbol", value="SPY")
        start_date = st.date_input(
            "Start Date",
            value=pd.to_datetime("2010-01-01"),
            key="data_start"
        )
    
    with col2:
        table_name = st.text_input("Save to Table", value="prices")
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            key="data_end"
        )
    
    if st.button("Download Data", type="primary"):
        data = download_data(ticker, start_date.strftime('%Y-%m-%d'), 
                           end_date.strftime('%Y-%m-%d'))
        
        if data is not None:
            st.session_state.db.save_prices(data, table_name)
            st.success(f"✅ Downloaded and saved {len(data)} rows to '{table_name}' table")
            st.dataframe(data.head(), use_container_width=True)
    
    # Database info
    st.markdown("---")
    st.subheader("Database Information")
    
    try:
        prices = st.session_state.db.load_prices('prices')
        st.write(f"**SPY Prices:** {len(prices)} rows")
        st.write(f"**Date Range:** {prices.index[0]} to {prices.index[-1]}")
    except:
        st.write("**SPY Prices:** No data")
    
    try:
        vix = st.session_state.db.load_prices('vix')
        st.write(f"**VIX Data:** {len(vix)} rows")
        st.write(f"**Date Range:** {vix.index[0]} to {vix.index[-1]}")
    except:
        st.write("**VIX Data:** No data")
    
    trades = st.session_state.db.load_trades()
    st.write(f"**Trades:** {len(trades)} rows")
    
    signals = st.session_state.db.load_signals()
    st.write(f"**Signals:** {len(signals)} rows")
    
    # Database actions
    st.markdown("---")
    st.subheader("Database Actions")
    
    col1, col2 = st.columns(2)
    
    if col1.button("🗑️ Clear Trades & Signals", type="secondary"):
        st.session_state.db.reset_database()
        st.success("Trades and signals cleared")
    
    if col2.button("⚠️ Reset Entire Database", type="secondary"):
        st.session_state.db.reset_database()
        st.warning("Database reset. Price data preserved.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
**SPY LEAPS Monitor v1.0**

A backtesting and monitoring tool for SPY LEAPS accumulation strategies.

Built with Streamlit
""")
