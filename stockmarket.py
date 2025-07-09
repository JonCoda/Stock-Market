import numpy as np
from scipy.signal import argrelextrema
from numpy import polyfit
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

    Args:
        api_key (str): ebd13cb01404512ea3e1ab2ae81a7b0f

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="General Stock Market Report",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for better aesthetics ---
st.markdown("""
    <style>
        .main {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 16px;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #45a049;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .stTextInput>div>div>input {
            border-radius: 8px;
            border: 1px solid #ccc;
            padding: 10px;
        }
        .stSelectbox>div>div {
            border-radius: 8px;
            border: 1px solid #ccc;
            padding: 5px;
        }
        .stAlert {
            border-radius: 8px;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 5%;
            padding-right: 5%;
        }
    </style>
""", unsafe_allow_html=True)

# --- Title and Description ---
st.title("📈 General Stock Market Report")
st.markdown(
    """
    Welcome to your personalized stock market analysis tool!
    Enter one or more stock tickers (e.g., `AAPL`, `GOOGL`, `MSFT`) to get real-time data,
    historical charts, and basic technical analysis.
    """
)

# --- Sidebar for User Inputs ---
st.sidebar.header("Configuration")

# Input for stock tickers
ticker_input = st.sidebar.text_input(
    "Enter Stock Ticker(s) (comma-separated)",
    "AAPL,GOOGL",
    help="Example: AAPL,MSFT,GOOGL. Use official Yahoo Finance tickers."
)
tickers = [t.strip().upper() for t in ticker_input.split(',') if t.strip()]

# Date range selection
today = datetime.now()
default_start_date = today - timedelta(days=365) # Default to 1 year ago
start_date = st.sidebar.date_input("Start Date", default_start_date)
end_date = st.sidebar.date_input("End Date", today)

# Check if start date is before end date
if start_date > end_date:
    st.sidebar.error("Error: End date must be after start date.")
    st.stop()

# Moving Average periods
st.sidebar.subheader("Moving Averages")
ma_short = st.sidebar.slider("Short MA Period", 5, 50, 20)
ma_long = st.sidebar.slider("Long MA Period", 20, 200, 50)

# --- Main Content Area ---

if not tickers:
    st.warning("Please enter at least one stock ticker in the sidebar.")
else:
    for ticker in tickers:
        st.header(f"📊 {ticker} Stock Report")

        try:
            # Fetch data using yfinance
            stock = yf.Ticker(ticker)

            # Get basic stock info
            info = stock.info
            if not info:
                st.error(f"Could not retrieve information for {ticker}. Please check the ticker symbol.")
                continue

            # Display key information in columns
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Current Price", f"${info.get('regularMarketPrice', 'N/A'):.2f}")
            with col2:
                daily_change = info.get('regularMarketChange', 0)
                daily_percent_change = info.get('regularMarketChangePercent', 0) * 100
                st.metric(
                    "Daily Change",
                    f"${daily_change:.2f}",
                    delta=f"{daily_percent_change:.2f}%",
                    delta_color="normal" if daily_change >= 0 else "inverse"
                )
            with col3:
                st.metric("Previous Close", f"${info.get('previousClose', 'N/A'):.2f}")
            with col4:
                st.metric("Volume", f"{info.get('regularMarketVolume', 'N/A'):,}")

            st.markdown("---")

            # Fetch historical data
            data = stock.history(start=start_date, end=end_date)

            if data.empty:
                st.warning(f"No historical data found for {ticker} in the selected date range.")
                continue

            # Calculate Moving Averages
            data[f'MA_{ma_short}'] = data['Close'].rolling(window=ma_short).mean()
            data[f'MA_{ma_long}'] = data['Close'].rolling(window=ma_long).mean()

            # Plotting with Plotly
            st.subheader("Historical Price Chart")

            fig = go.Figure()

            # Candlestick chart
            fig.add_trace(go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Candlestick'
            ))

            # Moving Averages
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data[f'MA_{ma_short}'],
                mode='lines',
                name=f'{ma_short}-Day MA',
                line=dict(color='orange', width=1)
            ))
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data[f'MA_{ma_long}'],
                mode='lines',
                name=f'{ma_long}-Day MA',
                line=dict(color='purple', width=1)
            ))

            # Update layout for better visualization
            fig.update_layout(
                title=f'{ticker} Price Chart with Moving Averages',
                xaxis_title='Date',
                yaxis_title='Price ($)',
                xaxis_rangeslider_visible=False, # Hide range slider for cleaner look
                template='plotly_white',
                height=500,
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Display raw data (optional)
            st.subheader("Raw Historical Data")
            st.dataframe(data.tail(10)) # Show last 10 rows of data

            st.markdown("---")

        except Exception as e:
            st.error(f"An error occurred while fetching data for {ticker}: {e}")
            st.info("Please ensure the ticker symbol is correct and you have an active internet connection.")

st.markdown(
    """
    ---
    *Data provided by Yahoo Finance. This report is for informational purposes only and not investment advice.*
    """
)

