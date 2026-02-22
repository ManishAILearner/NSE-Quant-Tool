from .data import fetch_data
from .backtest import run_backtest, run_analysis
try:
    from config import NSE_SYMBOLS
except ImportError:
    try:
        from ..config import NSE_SYMBOLS
    except ImportError:
        from backend.config import NSE_SYMBOLS


def scan_market(symbols=None, live=False):
    """Scan a list of symbols and return metrics.

    - symbols: optional iterable of symbol strings (defaults to `NSE_SYMBOLS`)
    - live: if True, fetch shorter-period intraday data for latest prices
    """
    symbols = symbols or NSE_SYMBOLS
    results = []

    for symbol in symbols:
        try:
            if live:
                data = fetch_data(symbol, period="1d", interval="5m")
            else:
                data = fetch_data(symbol)

            if data is None or data.empty:
                print(f"No data for {symbol}")
                continue

            metrics = run_backtest(data)

            last_price = None
            try:
                arr = data["Close"].to_numpy()
                if arr.size:
                    val = arr[-1]
                    if hasattr(val, 'item'):
                        last_price = float(val.item())
                    else:
                        last_price = float(val)
                else:
                    last_price = None
            except Exception:
                last_price = None

            results.append({
                "symbol": symbol,
                "last_price": last_price,
                **metrics
            })
        except Exception as e:
            print(f"Error scanning {symbol}: {e}")

    return results


def scan_analysis(symbols=None, live=False):
    symbols = symbols or NSE_SYMBOLS
    results = []

    for symbol in symbols:
        try:
            if live:
                data = fetch_data(symbol, period="1d", interval="5m")
                freq = "5m"
            else:
                data = fetch_data(symbol)
                freq = "1D"

            if data is None or data.empty:
                continue

            analysis = run_analysis(data, freq=freq)
            last_price = None
            if not data["Close"].empty:
                arr = data["Close"].to_numpy()
                if arr.size > 0:
                    val = arr[-1]
                    last_price = float(val.item()) if hasattr(val, 'item') else float(val)

            results.append({"symbol": symbol, "last_price": last_price, **analysis})
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")

    return results
