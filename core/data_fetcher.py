"""
Market Data Fetcher for XAU/USD and BTC/USD
Primary Engine: Direct TradingView WebSocket Stream (OANDA:XAUUSD & BINANCE:BTCUSDT)
Fallback Engine: yfinance (GC=F, XAUUSD=X, BTC-USD)
"""

import sys
from pathlib import Path

# Ensure root workspace is in sys.path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pandas as pd
from core.tradingview_stream import fetch_tradingview_candles

def fetch_market_data(symbol_key: str, timeframe: str = "1h", n_bars: int = 250) -> pd.DataFrame:
    """
    Fetch live OHLCV data directly from TradingView.
    Returns cleaned pandas DataFrame with Datetime index and Open, High, Low, Close, Volume.
    """
    try:
        # 1. Primary: Direct TradingView Chart WebSocket stream
        df = fetch_tradingview_candles(symbol_key, timeframe, n_bars=n_bars)
        if df is not None and not df.empty:
            df.attrs["source"] = "TradingView (Live WebSocket Feed)"
            return df
    except Exception as tv_err:
        print(f"[Notice] TradingView stream fallback invoked: {tv_err}")

    # 2. Secondary Fallback: yfinance
    import yfinance as yf
    
    symbols_map = {
        "XAUUSD": "GC=F",
        "BTCUSD": "BTC-USD",
    }
    tf_map = {
        "15m": {"period": "5d", "interval": "15m"},
        "1h": {"period": "30d", "interval": "1h"},
        "4h": {"period": "90d", "interval": "1h"},
        "1d": {"period": "365d", "interval": "1d"}
    }
    
    ticker_sym = symbols_map.get(symbol_key, "GC=F")
    conf = tf_map.get(timeframe, tf_map["1h"])
    ticker = yf.Ticker(ticker_sym)
    df = ticker.history(period=conf["period"], interval=conf["interval"])
    
    if df.empty and symbol_key == "XAUUSD":
        alt_ticker = yf.Ticker("XAUUSD=X")
        df = alt_ticker.history(period=conf["period"], interval=conf["interval"])
        
    if df.empty:
        raise RuntimeError(f"Unable to fetch live market data for {symbol_key}.")
        
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    df.index = pd.to_datetime(df.index)
    
    if timeframe == "4h":
        df = df.resample('4h').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        
    df = df.dropna()
    df.attrs["source"] = "Secondary Fallback (Yahoo Finance)"
    return df

if __name__ == "__main__":
    for sym in ["XAUUSD", "BTCUSD"]:
        data = fetch_market_data(sym, "1h")
        print(f"[{sym}] Source: {data.attrs.get('source')}, Bars: {len(data)}, Latest Price: {data['Close'].iloc[-1]}")
