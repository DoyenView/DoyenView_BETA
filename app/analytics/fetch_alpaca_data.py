# app/analytics/fetch_alpaca_data.py

import os
import pandas as pd
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# Load Alpaca credentials
load_dotenv("alpaca_keys.env")
API_KEY = os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("APCA_API_SECRET_KEY")

# Initialize client
client = StockHistoricalDataClient(API_KEY, API_SECRET)

# Define tickers and timeframe
tickers = ['AAPL', 'SPY', 'QQQ', 'DIA', 'UVXY', 'IBIT', 'HIMS', 'HOOD']
timeframe = TimeFrame.Day
start = "2023-01-01"
end = "2024-12-31"

# Output directory
output_dir = "DoyenView_DataCache"
os.makedirs(output_dir, exist_ok=True)

# Fetch and store each symbol
for symbol in tickers:
    print(f"Fetching {symbol}...")
    req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=timeframe, start=start, end=end)
    bars = client.get_stock_bars(req)
    df = bars.df
    if df.empty:
        print(f"⚠️ No data for {symbol}")
        continue
    df.to_csv(f"{output_dir}/{symbol}_{timeframe}.csv")
    print(f"✅ Saved {symbol} to CSV.")
