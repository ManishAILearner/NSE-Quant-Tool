import yfinance as yf
import pandas as pd
import os
import datetime

# Global cache for Kite instruments to avoid fetching on every call
_KITE_INSTRUMENT_MAP = None


def fetch_data(symbol, period="6mo", interval="1d"):
    """
    Fetch historical market data for a symbol.
    
    Default: Uses yfinance (Yahoo Finance).
    To use a direct NSE source (like nselib), you can modify the logic below.
    """

    # --- Option 2: Zerodha Kite Connect ---
    if os.getenv("USE_ZERODHA") == "true":
        try:
            from kiteconnect import KiteConnect
        except ImportError:
            print("Error: 'kiteconnect' not installed. Run: pip install kiteconnect")
            return pd.DataFrame()

        api_key = os.getenv("KITE_API_KEY")
        access_token = os.getenv("KITE_ACCESS_TOKEN")

        if not api_key or not access_token:
            print("Error: KITE_API_KEY and KITE_ACCESS_TOKEN env vars required.")
            return pd.DataFrame()

        try:
            kite = KiteConnect(api_key=api_key)
            kite.set_access_token(access_token)

            # Fetch and cache instruments once
            global _KITE_INSTRUMENT_MAP
            if _KITE_INSTRUMENT_MAP is None:
                print("Fetching Kite instruments map (NSE)...")
                instruments = kite.instruments("NSE")
                _KITE_INSTRUMENT_MAP = {i['tradingsymbol']: i['instrument_token'] for i in instruments}

            # Convert "RELIANCE.NS" -> "RELIANCE" for Kite
            clean_symbol = symbol.replace(".NS", "")
            token = _KITE_INSTRUMENT_MAP.get(clean_symbol)

            if not token:
                print(f"Token not found for {clean_symbol}")
                return pd.DataFrame()

            # Map interval/period to Kite format
            kite_interval = "day"
            days = 200  # default approx 6mo
            if interval == "5m":
                kite_interval = "5minute"
                days = 5  # Kite limits intraday data fetch duration
            elif interval == "1d":
                if period == "1y": days = 365
                elif period == "1mo": days = 30

            to_date = datetime.datetime.now()
            from_date = to_date - datetime.timedelta(days=days)

            records = kite.historical_data(token, from_date, to_date, kite_interval)
            df = pd.DataFrame(records)
            
            if not df.empty:
                df.set_index('date', inplace=True)
                # Normalize columns to match yfinance format expected by backtest.py
                df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
            
            return df

        except Exception as e:
            print(f"Kite error for {symbol}: {e}")
            return pd.DataFrame()
    
    # --- Option 1: Yahoo Finance (Default) ---
    # Supports NSE symbols with '.NS' suffix (e.g., 'TCS.NS')
    try:
        data = yf.download(symbol, period=period, interval=interval, progress=False, threads=False)
        
        if data is None or data.empty:
            return pd.DataFrame()
            
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

    # --- Option 2: Example for Direct NSE (e.g., using nselib) ---
    # import nselib
    # from nselib import capital_market
    #
    # # 1. Remove '.NS' suffix as official NSE APIs usually expect just 'TCS'
    # clean_symbol = symbol.replace('.NS', '')
    #
    # # 2. Fetch data
    # # data = capital_market.price_volume_and_delivery_position_data(symbol=clean_symbol, ...)
    #
    # # 3. Format DataFrame to have columns: ['Open', 'High', 'Low', 'Close', 'Volume'] with DatetimeIndex
    # # return formatted_data
