"""
TradingView Live Data Engine
Connects directly to TradingView's Chart WebSocket stream
Fetches real-time candles and official TradingView TA ratings for:
- FX:XAUUSD (FXCM Spot Gold on TradingView)
- BITSTAMP:BTCUSD (Bitstamp Spot Bitcoin on TradingView)
"""

import asyncio
import websockets
import json
import re
import random
import string
import threading
import pandas as pd
from datetime import datetime, timezone
from tradingview_ta import TA_Handler, Interval

TV_SYMBOLS = {
    "XAUUSD": "FX:XAUUSD",       # FXCM Gold on TradingView
    "BTCUSD": "BITSTAMP:BTCUSD"  # Bitstamp Bitcoin on TradingView
}

TV_CONFIG = {
    "XAUUSD": {"symbol": "XAUUSD", "exchange": "FX", "screener": "cfd"},
    "BTCUSD": {"symbol": "BTCUSD", "exchange": "BITSTAMP", "screener": "crypto"}
}

TV_INTERVAL_MAP = {
    "15m": "15",
    "1h": "60",
    "4h": "240",
    "1d": "1D"
}

TA_INTERVAL_MAP = {
    "15m": Interval.INTERVAL_15_MINUTES,
    "1h": Interval.INTERVAL_1_HOUR,
    "4h": Interval.INTERVAL_4_HOURS,
    "1d": Interval.INTERVAL_1_DAY
}

def generate_session():
    rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"cs_{rand}"

def format_tv_message(name: str, params: list) -> str:
    payload = json.dumps({"m": name, "p": params})
    return f"~m~{len(payload)}~m~{payload}"

async def _fetch_tradingview_candles_async(symbol: str, timeframe: str = "15m", n_bars: int = 250) -> pd.DataFrame:
    tv_symbol = TV_SYMBOLS.get(symbol, TV_SYMBOLS["XAUUSD"])
    tv_res = TV_INTERVAL_MAP.get(timeframe, "15")
    
    uri = "wss://data.tradingview.com/socket.io/websocket?from=chart%2F&date=2024_01_01"
    headers = {"Origin": "https://www.tradingview.com"}
    session_id = generate_session()
    
    async with websockets.connect(uri, additional_headers=headers) as ws:
        await ws.recv()
        
        await ws.send(format_tv_message("set_auth_token", ["unauthorized_user_token"]))
        await ws.send(format_tv_message("chart_create_session", [session_id, ""]))
        await ws.send(format_tv_message("resolve_symbol", [session_id, "sym_1", f'={{"symbol":"{tv_symbol}","adjustment":"splits"}}']))
        await ws.send(format_tv_message("create_series", [session_id, "ser_1", "s1", "sym_1", tv_res, n_bars, ""]))
        
        candles = []
        for _ in range(15):
            res = await asyncio.wait_for(ws.recv(), timeout=7)
            if "timescale_update" in res:
                parts = re.split(r"~m~\d+~m~", res)
                for p in parts:
                    if not p.strip():
                        continue
                    try:
                        data = json.loads(p)
                        if data.get("m") == "timescale_update":
                            payload = data["p"][1]
                            for k, val in payload.items():
                                if isinstance(val, dict) and "s" in val:
                                    raw_bars = val["s"]
                                    for bar in raw_bars:
                                        v = bar["v"]
                                        ts = datetime.fromtimestamp(v[0], tz=timezone.utc)
                                        candles.append({
                                            "Datetime": ts,
                                            "Open": float(v[1]),
                                            "High": float(v[2]),
                                            "Low": float(v[3]),
                                            "Close": float(v[4]),
                                            "Volume": float(v[5]) if len(v) > 5 else 0.0
                                        })
                                    break
                    except Exception:
                        pass
                if candles:
                    break
                    
        if not candles:
            raise RuntimeError(f"No candles returned from TradingView for {tv_symbol}")
            
        df = pd.DataFrame(candles)
        df = df.set_index("Datetime")
        df = df.sort_index()
        df = df[~df.index.duplicated(keep='last')]
        return df

def fetch_tradingview_candles(symbol: str, timeframe: str = "15m", n_bars: int = 250) -> pd.DataFrame:
    """
    Thread-safe synchronous fetcher for TradingView candles.
    """
    result = {}
    err = {}

    def worker():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            df = loop.run_until_complete(_fetch_tradingview_candles_async(symbol, timeframe, n_bars))
            loop.close()
            result['df'] = df
        except Exception as e:
            err['e'] = e

    t = threading.Thread(target=worker)
    t.start()
    t.join(timeout=15)
    
    if 'df' in result:
        return result['df']
    if 'e' in err:
        raise err['e']
    raise TimeoutError("Timeout fetching live candles from TradingView WebSocket.")

def get_tradingview_official_ta(symbol: str, timeframe: str = "15m") -> dict:
    """
    Fetches official TradingView Technical Analysis summary (Oscillators, Moving Averages, Recommendation).
    """
    cfg = TV_CONFIG.get(symbol, TV_CONFIG["XAUUSD"])
    interval_enum = TA_INTERVAL_MAP.get(timeframe, Interval.INTERVAL_15_MINUTES)
    try:
        handler = TA_Handler(
            symbol=cfg["symbol"],
            exchange=cfg["exchange"],
            screener=cfg["screener"],
            interval=interval_enum
        )
        analysis = handler.get_analysis()
        return {
            "status": "SUCCESS",
            "summary": analysis.summary,
            "oscillators": analysis.oscillators,
            "moving_averages": analysis.moving_averages,
            "indicators": analysis.indicators
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": str(e)
        }
