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
            print(f"Warning: No data found for {ticker} from Marketstack in the specified range.")
            return pd.DataFrame(), None

        # Marketstack returns a list of dictionaries, one for each date and symbol
        ticker_data = [item for item in data['data'] if item['symbol'] == ticker]

        if not ticker_data:
            print(f"Warning: No data found for {ticker} after filtering Marketstack response.")
            return pd.DataFrame(), None

        # Convert to DataFrame
        df = pd.DataFrame(ticker_data)

        # Ensure 'date' column is datetime and set as index
        df['date'] = pd.to_datetime(df['date']).dt.date
        df = df.set_index('date')
        df.index.name = 'Date'

        # Select and rename columns to match previous structure
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            print(f"Error: Marketstack response for {ticker} is missing expected columns. Found: {df.columns.tolist()}")
            return pd.DataFrame(), None

        df = df[required_cols]
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df.sort_index() # Ensure ascending date order for calculations

        # Get latest info for metrics
        if len(df) < 2: # Need at least two data points for previous close
            print(f"Warning: Not enough data for {ticker} to calculate daily change. Showing current price only.")
            latest_data = df.iloc[-1]
            info = {
                'regularMarketPrice': latest_data['Close'],
                'regularMarketChange': 0,
                'regularMarketChangePercent': 0,
                'previousClose': latest_data['Close'],
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
                'regularMarketChangePercent': daily_percent_change / 100,
                'previousClose': prev_close,
                'regularMarketVolume': latest_data['Volume']
            }

        return df, info

    except requests.exceptions.RequestException as e:
        print(f"Error: Network or API error fetching data for {ticker}: {e}")
    except KeyError as e:
        print(f"Error: Data format error from Marketstack for {ticker}: Missing key {e}. API response might be unexpected.")
    except Exception as e:
        print(f"Error: An unexpected error occurred while processing Marketstack data for {ticker}: {e}")
    finally:
        # This block will always execute, regardless of whether an exception occurred or not.
        pass # No specific cleanup needed for this simple request, but good for demonstration.

    return pd.DataFrame(), None # Return empty DataFrame and None info on error


# --- Core Logic (without Streamlit UI or Plotly) ---

# Example usage (you would integrate this into your application logic)
if __name__ == "__main__":
    # IMPORTANT: Replace 'YOUR_MARKETSTACK_API_KEY_HERE' with your actual Marketstack API key.
    # For demonstration, you might want to set it here if not using Streamlit.
    # MARKETSTACK_API_KEY = "YOUR_MARKETSTACK_API_KEY_HERE"

    if not MARKETSTACK_API_KEY or MARKETSTACK_API_KEY == "YOUR_MARKETSTACK_API_KEY_HERE":
        print("Please replace 'YOUR_MARKETSTACK_API_KEY_HERE' in the code with your actual Marketstack API key.")
    else:
        # Define tickers and date range for demonstration
        tickers_to_process = ["AAPL", "GOOGL"]
        today = datetime.now().date()
        start_date = today - timedelta(days=365)
        end_date = today

        # Define Moving Average periods
        ma_short = 20
        ma_long = 50

        for ticker in tickers_to_process:
            print(f"\n--- Processing {ticker} ---")

            try:
                data, info = fetch_marketstack_data(ticker, start_date, end_date, MARKETSTACK_API_KEY)

                if data.empty or info is None:
                    print(f"Skipping further processing for {ticker} due to data fetching issues.")
                    continue

                print(f"Current Price: ${info.get('regularMarketPrice', 'N/A'):.2f}")
                print(f"Daily Change: ${info.get('regularMarketChange', 0):.2f} ({info.get('regularMarketChangePercent', 0) * 100:.2f}%)")
                print(f"Previous Close: ${info.get('previousClose', 'N/A'):.2f}")
                print(f"Volume: {info.get('regularMarketVolume', 'N/A'):,}")

                # Calculate Moving Averages
                if len(data) >= ma_long:
                    data[f'MA_{ma_short}'] = data['Close'].rolling(window=ma_short).mean()
                    data[f'MA_{ma_long}'] = data['Close'].rolling(window=ma_long).mean()
                    print(f"{ma_short}-Day MA: {data[f'MA_{ma_short}'].iloc[-1]:.2f}")
                    print(f"{ma_long}-Day MA: {data[f'MA_{ma_long}'].iloc[-1]:.2f}")
                else:
                    print(f"Not enough data points ({len(data)}) for {ticker} to calculate {ma_long}-day Moving Average.")

                print("\nRaw Historical Data (Last 5 rows):")
                print(data.tail())

            except Exception as e:
                print(f"An overall error occurred while processing {ticker}: {e}")
            finally:
                print(f"Finished processing core data for {ticker}.")

        print("\n--- End of Report ---")
        print("Data provided by Marketstack. This report is for informational purposes only and not investment advice.")


