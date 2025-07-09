import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests # Import the requests library for API calls

# --- Marketstack API Configuration ---
# IMPORTANT: Replace 'YOUR_MARKETSTACK_API_KEY_HERE' with your actual Marketstack API key.
# You can get one from https://marketstack.com/
MARKETSTACK_API_KEY = "ebd13cb01404512ea3e1ab2ae81a7b0f"
MARKETSTACK_BASE_URL = "http://api.marketstack.com/v1/"

# --- Function to fetch data from Marketstack ---
def fetch_marketstack_data(ticker, start_date, end_date, api_key):
    """
    Fetches historical End-Of-Day (EOD) stock data from Marketstack API.

    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL').
        start_date (datetime.date): The start date for the historical data.
        end_date (datetime.date): The end date for the historical data.
        api_key (str): Your Marketstack API key.

    Returns:
        pandas.DataFrame: A DataFrame with 'Open', 'High', 'Low', 'Close', 'Volume'
                          indexed by 'Date', or an empty DataFrame if data fetch fails.
        dict: A dictionary containing the latest stock info, or None.
    """
    endpoint = f"eod"
    params = {
        "access_key": api_key,
        "symbols": ticker,
        "date_from": start_date.strftime("%Y-%m-%d"),
        "date_to": end_date.strftime("%Y-%m-%d"),
        "limit": 1000, # Max limit per request, adjust if needed for longer periods
        "sort": "ASC" # Ensure data is sorted ascending by date
    }

    try:
        response = requests.get(f"{MARKETSTACK_BASE_URL}{endpoint}", params=params)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if not data or 'data' not in data or not data['data']:
            st.warning(f"No data found for {ticker} from Marketstack in the specified range.")
            return pd.DataFrame(), None

        # Marketstack returns a list of dictionaries, one for each date and symbol
        # We need to filter for the specific ticker if multiple symbols were requested (though we request one here)
        ticker_data = [item for item in data['data'] if item['symbol'] == ticker]

        if not ticker_data:
            st.warning(f"No data found for {ticker} after filtering Marketstack response.")
            return pd.DataFrame(), None

        # Convert to DataFrame
        df = pd.DataFrame(ticker_data)

        # Ensure 'date' column is datetime and set as index
        # Convert to date object first to avoid time components interfering with indexing
        df['date'] = pd.to_datetime(df['date']).dt.date
        df = df.set_index('date')
        df.index.name = 'Date'

        # Select and rename columns to match previous structure
        # Ensure these column names match what Marketstack returns (e.g., 'open', 'high', 'low', 'close', 'volume')
        # If Marketstack uses different names, you'll need to adjust these.
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            st.error(f"Marketstack response for {ticker} is missing expected columns. Found: {df.columns.tolist()}")
            return pd.DataFrame(), None

        df = df[required_cols]
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df.sort_index() # Ensure ascending date order for calculations

        # Get latest info for metrics
        if len(df) < 2: # Need at least two data points for previous close
            st.warning(f"Not enough data for {ticker} to calculate daily change. Showing current price only.")
            latest_data = df.iloc[-1]
            info = {
                'regularMarketPrice': latest_data['Close'],
                'regularMarketChange': 0,
                'regularMarketChangePercent': 0,
                'previousClose': latest_data['Close'], # Set previous close to current if only one data point
                'regularMarketVolume': latest_data['Volume']
            }
        else:
            latest_data = df.iloc[-1]
            prev_close = df.iloc[-2]['Close']
            daily_change = latest_data['Close'] - prev_close
            daily_percent_change = (daily_change / prev_close) * 100 if prev_close != 0 else 0

            info = {
                'regularMarketPrice': latest_data['Close'],
                'regularMarketChange': daily_change,
                'regularMarketChangePercent': daily_percent_change / 100, # Convert to decimal for consistency
                'previousClose': prev_close,
                'regularMarketVolume': latest_data['Volume']
            }

        return df, info

    except requests.exceptions.RequestException as e:
        st.error(f"Network or API error fetching data for {ticker}: {e}")
        st.info("Please check your internet connection and Marketstack API key.")
    except KeyError as e:
        st.error(f"Data format error from Marketstack for {ticker}: Missing key {e}. API response might be unexpected.")
    except Exception as e:
        st.error(f"An unexpected error occurred while processing Marketstack data for {ticker}: {e}")

    return pd.DataFrame(), None # Return empty DataFrame and None info on error


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
    help="Example: AAPL,MSFT,GOOGL. Use official Marketstack tickers."
)
tickers = [t.strip().upper() for t in ticker_input.split(',') if t.strip()]

# Date range selection
today = datetime.now().date() # Get only date part for comparison
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

if not MARKETSTACK_API_KEY or MARKETSTACK_API_KEY == "YOUR_MARKETSTACK_API_KEY_HERE":
    st.error("Please replace 'YOUR_MARKETSTACK_API_KEY_HERE' in the code with your actual Marketstack API key.")
elif not tickers:
    st.warning("Please enter at least one stock ticker in the sidebar.")
else:
    for ticker in tickers:
        st.header(f"📊 {ticker} Stock Report")

        # Fetch data using Marketstack API
        data, info = fetch_marketstack_data(ticker, start_date, end_date, MARKETSTACK_API_KEY)

        if data.empty or info is None:
            # Error message already handled in fetch_marketstack_data
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

        # Calculate Moving Averages
        # Ensure there's enough data for MA calculation
        if len(data) >= ma_long:
            data[f'MA_{ma_short}'] = data['Close'].rolling(window=ma_short).mean()
            data[f'MA_{ma_long}'] = data['Close'].rolling(window=ma_long).mean()
        else:
            st.warning(f"Not enough data points ({len(data)}) for {ticker} to calculate {ma_long}-day Moving Average. Moving averages will not be displayed.")
            # Set MAs to None or drop columns if not enough data
            data[f'MA_{ma_short}'] = None
            data[f'MA_{ma_long}'] = None


        # Plotting with Plotly
        st.subheader("Historical Price Chart")

        # --- Debugging: Display DataFrame head and columns ---
        st.write("--- Debugging Info ---")
        st.write("DataFrame Head:")
        st.write(data.head())
        st.write("DataFrame Columns:")
        st.write(data.columns.tolist())
        st.write("--- End Debugging Info ---")

        try:
            fig = go.Figure()

            # Check if required columns for candlestick exist
            if all(col in data.columns for col in ['Open', 'High', 'Low', 'Close']) and not data.empty:
                # Candlestick chart
                fig.add_trace(go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name='Candlestick'
                ))
            else:
                st.warning("Cannot plot candlestick chart: Missing 'Open', 'High', 'Low', or 'Close' columns, or data is empty.")

            # Moving Averages - only add if calculated and columns exist
            if f'MA_{ma_short}' in data.columns and data[f'MA_{ma_short}'].notna().any():
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data[f'MA_{ma_short}'],
                    mode='lines',
                    name=f'{ma_short}-Day MA',
                    line=dict(color='orange', width=1)
                ))
            if f'MA_{ma_long}' in data.columns and data[f'MA_{ma_long}'].notna().any():
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
st.finally( 
    """
    ---
    *Data provided by Marketstack. This report is for informational purposes only and not investment advice.*
    """
) 

