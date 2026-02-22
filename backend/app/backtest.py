import vectorbt as vbt
import numpy as np
from .strategies import momentum_strategy, mean_reversion_strategy


def _to_float(x):
    arr = np.asarray(x)
    try:
        val = float(arr.item())
        if np.isnan(val) or np.isinf(val):
            return None
        return val
    except Exception:
        return None


def run_backtest(data):
    close = data["Close"]
    # Ensure `close` is a Series (single column). If yfinance returned a DataFrame
    # (multi-index columns when a ticker is present), pick the first column to
    # keep downstream indicator logic simple.
    try:
        # pandas DataFrame has `columns` attribute
        if hasattr(close, 'columns'):
            close = close.iloc[:, 0]
    except Exception:
        pass

    m_entries, m_exits = momentum_strategy(close)
    mr_entries, mr_exits = mean_reversion_strategy(close)

    pf_m = vbt.Portfolio.from_signals(close, m_entries, m_exits)
    pf_mr = vbt.Portfolio.from_signals(close, mr_entries, mr_exits)

    m_ret = _to_float(pf_m.total_return())
    mr_ret = _to_float(pf_mr.total_return())

    return {
        "momentum_return": round(m_ret * 100, 2) if m_ret is not None else None,
        "mean_rev_return": round(mr_ret * 100, 2) if mr_ret is not None else None,
    }


def run_analysis(data, freq=None):
    close = data["Close"]
    try:
        if hasattr(close, 'columns'):
            close = close.iloc[:, 0]
    except Exception:
        pass

    m_entries, m_exits = momentum_strategy(close)
    mr_entries, mr_exits = mean_reversion_strategy(close)

    mom_pf = vbt.Portfolio.from_signals(close, m_entries, m_exits, init_cash=100000, freq=freq)
    rev_pf = vbt.Portfolio.from_signals(close, mr_entries, mr_exits, init_cash=100000, freq=freq)

    def get_metrics(pf):
        return {
            "return_pct": _to_float(pf.total_return() * 100),
            "sharpe": _to_float(pf.sharpe_ratio()),
            "max_dd_pct": _to_float(pf.max_drawdown() * 100),
            "win_rate_pct": _to_float(pf.trades.win_rate() * 100)
        }

    mom_metrics = get_metrics(mom_pf)
    rev_metrics = get_metrics(rev_pf)

    # Determine current signals based on the last candle
    mom_signal = "Neutral"
    if not m_entries.empty:
        if m_entries.iloc[-1]:
            mom_signal = "Buy"
        elif m_exits.iloc[-1]:
            mom_signal = "Sell"

    rev_signal = "Neutral"
    if not mr_entries.empty:
        if mr_entries.iloc[-1]:
            rev_signal = "Buy"
        elif mr_exits.iloc[-1]:
            rev_signal = "Sell"

    # Decision Framework
    is_short_term_good = (rev_metrics["win_rate_pct"] or 0) > 50
    is_long_term_good = (mom_metrics["sharpe"] or 0) > 1

    recommendation = "Avoid"
    if is_short_term_good and is_long_term_good:
        recommendation = "Strong Buy"
    elif is_short_term_good:
        recommendation = "Short Term Buy"
    elif is_long_term_good:
        recommendation = "Long Term Buy"

    return {
        "momentum": {**mom_metrics, "signal": mom_signal},
        "mean_reversion": {**rev_metrics, "signal": rev_signal},
        "recommendation": recommendation
    }
