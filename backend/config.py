# NOTE: The '.NS' suffix is required for Yahoo Finance to identify NSE stocks.
# If you switch to a direct NSE data provider (like nselib), you may need to 
# remove these suffixes or update this list to just ["ADANIENT", "ADANIPORTS", ...]
# For Zerodha Kite (USE_ZERODHA=true), the code automatically strips '.NS'.

NSE_SYMBOLS = [
    "ADANIENT.NS",
    "ADANIPORTS.NS",
    "AMBUJACEM.NS",
    "ASIANPAINT.NS",
    "AUROPHARMA.NS",
    "AXISBANK.NS",
    "BAJAJ-AUTO.NS",
    "BAJFINANCE.NS",
    "BAJAJFINSV.NS",
    "BHARTIARTL.NS",
    "BPCL.NS",
    "BRITANNIA.NS",
    "CIPLA.NS",
    "COALINDIA.NS",
    "DIVISLAB.NS",
    "DRREDDY.NS",
    "EICHERMOT.NS",
    "GRASIM.NS",
    "HCLTECH.NS",
    "HDFCBANK.NS",
    "HDFCLIFE.NS",
    "HEROMOTOCO.NS",
    "HINDALCO.NS",
    "HINDUNILVR.NS",
    "HINDPETRO.NS",
    "HINDZINC.NS",
    "ICICIBANK.NS",
    "INDUSINDBK.NS",
    "INFY.NS",
    "JSWSTEEL.NS",
    "KOTAKBANK.NS",
    "LT.NS",
    "M&M.NS",
    "MARUTI.NS",
    "NESTLEIND.NS",
    "NTPC.NS",
    "ONGC.NS",
    "POWERGRID.NS",
    "RELIANCE.NS",
    "SBIN.NS",
    "SUNPHARMA.NS",
    "TATACHEM.NS",
    "TATACONSUM.NS",
    "TATASTEEL.NS",
    "TECHM.NS",
    "TCS.NS",
    "ULTRACEMCO.NS",
    "WIPRO.NS",
]

# Mapping of human-friendly index names to symbol lists. Add more indexes here as needed.
NIFTY_BANK = [
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "AXISBANK.NS",
    "KOTAKBANK.NS",
    "SBIN.NS",
    "INDUSINDBK.NS",
]

NIFTY_IT = [
    "TCS.NS",
    "INFY.NS",
    "WIPRO.NS",
    "HCLTECH.NS",
    "TECHM.NS",
]

NIFTY_AUTO = [
    "MARUTI.NS",
    "BAJAJ-AUTO.NS",
    "M&M.NS",
    "EICHERMOT.NS",
    "HEROMOTOCO.NS",
]

NIFTY_FMCG = [
    "HINDUNILVR.NS",
    "BRITANNIA.NS",
    "NESTLEIND.NS",
    "TATACONSUM.NS",
]

INDEXES = {
    "NSE 50": NSE_SYMBOLS,
    "NIFTY 50": NSE_SYMBOLS,
    "NIFTY BANK": NIFTY_BANK,
    "NIFTY IT": NIFTY_IT,
    "NIFTY AUTO": NIFTY_AUTO,
    "NIFTY FMCG": NIFTY_FMCG,
}