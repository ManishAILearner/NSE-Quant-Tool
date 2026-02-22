import vectorbt as vbt

def momentum_strategy(close):
    fast = vbt.MA.run(close, 10).ma  # type: ignore
    slow = vbt.MA.run(close, 30).ma  # type: ignore
    entries = fast > slow
    exits = fast < slow
    return entries, exits

def mean_reversion_strategy(close):
    rsi = vbt.RSI.run(close, 14).rsi  # type: ignore
    entries = rsi < 30
    exits = rsi > 55
    return entries, exits
