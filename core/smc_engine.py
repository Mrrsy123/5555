"""
Smart Money Concepts (SMC) & Inner Circle Trader (ICT) Algorithmic Engine.
Detects:
1. Swing Highs & Swing Lows (Fractals)
2. BOS (Break of Structure) & MSS/CHoCH (Market Structure Shift)
3. Order Blocks (OB) - Bullish & Bearish
4. Fair Value Gaps (FVG) & Consequent Encroachment (CE - 50%)
5. Liquidity Pools: BSL (Buy-Side Liquidity) & SSL (Sell-Side Liquidity) + Sweeps
6. Dealing Range: Premium vs Discount (Equilibrium 0.5 & OTE 0.62-0.79)
7. ICT Killzones Detection
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone
import pytz

def find_swings(df: pd.DataFrame, window: int = 3) -> tuple[list[dict], list[dict]]:
    """
    Identifies swing highs and swing lows using an N-bar fractal window.
    """
    swing_highs = []
    swing_lows = []
    
    highs = df['High'].values
    lows = df['Low'].values
    times = df.index
    
    for i in range(window, len(df) - window):
        current_high = highs[i]
        current_low = lows[i]
        
        # Check Swing High
        is_sh = True
        for k in range(1, window + 1):
            if highs[i - k] >= current_high or highs[i + k] >= current_high:
                is_sh = False
                break
        if is_sh:
            swing_highs.append({
                "index": i,
                "time": times[i],
                "price": float(current_high),
                "type": "SWING_HIGH"
            })
            
        # Check Swing Low
        is_sl = True
        for k in range(1, window + 1):
            if lows[i - k] <= current_low or lows[i + k] <= current_low:
                is_sl = False
                break
        if is_sl:
            swing_lows.append({
                "index": i,
                "time": times[i],
                "price": float(current_low),
                "type": "SWING_LOW"
            })
            
    return swing_highs, swing_lows

def detect_fvgs(df: pd.DataFrame, min_gap_percent: float = 0.05) -> list[dict]:
    """
    Detects Fair Value Gaps (FVGs) in 3-candle patterns.
    Bullish FVG: Candle[i-2].High < Candle[i].Low
    Bearish FVG: Candle[i-2].Low > Candle[i].High
    Tracks mitigation status against latest prices.
    """
    fvgs = []
    closes = df['Close'].values
    highs = df['High'].values
    lows = df['Low'].values
    times = df.index
    latest_close = closes[-1]
    
    for i in range(2, len(df)):
        c1_high = highs[i - 2]
        c1_low = lows[i - 2]
        c3_high = highs[i]
        c3_low = lows[i]
        mid_close = closes[i - 1]
        
        # Bullish FVG
        if c3_low > c1_high:
            gap_size = c3_low - c1_high
            gap_pct = (gap_size / mid_close) * 100
            if gap_pct >= min_gap_percent:
                ce = (c3_low + c1_high) / 2.0  # Consequent Encroachment (50%)
                
                # Check if mitigated by any subsequent candle
                future_lows = lows[i + 1:] if i + 1 < len(df) else []
                is_mitigated = False
                if len(future_lows) > 0 and np.min(future_lows) <= c1_high:
                    is_mitigated = True
                    
                fvgs.append({
                    "type": "BULLISH_FVG",
                    "time": times[i - 1],
                    "top": float(c3_low),
                    "bottom": float(c1_high),
                    "ce": float(ce),
                    "size": float(gap_size),
                    "size_pct": round(gap_pct, 2),
                    "mitigated": is_mitigated,
                    "active": not is_mitigated
                })
                
        # Bearish FVG
        elif c1_low > c3_high:
            gap_size = c1_low - c3_high
            gap_pct = (gap_size / mid_close) * 100
            if gap_pct >= min_gap_percent:
                ce = (c1_low + c3_high) / 2.0
                
                future_highs = highs[i + 1:] if i + 1 < len(df) else []
                is_mitigated = False
                if len(future_highs) > 0 and np.max(future_highs) >= c1_low:
                    is_mitigated = True
                    
                fvgs.append({
                    "type": "BEARISH_FVG",
                    "time": times[i - 1],
                    "top": float(c1_low),
                    "bottom": float(c3_high),
                    "ce": float(ce),
                    "size": float(gap_size),
                    "size_pct": round(gap_pct, 2),
                    "mitigated": is_mitigated,
                    "active": not is_mitigated
                })
                
    return fvgs

def detect_market_structure(df: pd.DataFrame, swing_highs: list[dict], swing_lows: list[dict]) -> list[dict]:
    """
    Detects BOS (Break of Structure) and MSS (Market Structure Shift / CHoCH).
    """
    events = []
    closes = df['Close'].values
    highs = df['High'].values
    lows = df['Low'].values
    times = df.index
    
    # Sort swings by index
    all_swings = sorted(swing_highs + swing_lows, key=lambda x: x['index'])
    
    # Track latest swing high and low
    active_sh = None
    active_sl = None
    prev_trend = "NEUTRAL"
    
    for s in all_swings:
        if s['type'] == 'SWING_HIGH':
            if active_sh is not None:
                if s['price'] > active_sh['price']:
                    # Higher High
                    pass
            active_sh = s
        elif s['type'] == 'SWING_LOW':
            if active_sl is not None:
                if s['price'] < active_sl['price']:
                    # Lower Low
                    pass
            active_sl = s
            
    # Check breaks in the last 40 bars
    start_bar = max(0, len(df) - 40)
    for i in range(start_bar, len(df)):
        bar_close = closes[i]
        bar_time = times[i]
        
        # Check break of recent Swing High
        recent_shs = [sh for sh in swing_highs if sh['index'] < i]
        if recent_shs:
            last_sh = recent_shs[-1]
            if bar_close > last_sh['price'] and (i - last_sh['index']) < 30:
                event_type = "BULLISH_MSS" if prev_trend == "BEARISH" else "BULLISH_BOS"
                events.append({
                    "type": event_type,
                    "time": bar_time,
                    "broken_level": float(last_sh['price']),
                    "bar_index": i
                })
                prev_trend = "BULLISH"
                
        # Check break of recent Swing Low
        recent_sls = [sl for sl in swing_lows if sl['index'] < i]
        if recent_sls:
            last_sl = recent_sls[-1]
            if bar_close < last_sl['price'] and (i - last_sl['index']) < 30:
                event_type = "BEARISH_MSS" if prev_trend == "BULLISH" else "BEARISH_BOS"
                events.append({
                    "type": event_type,
                    "time": bar_time,
                    "broken_level": float(last_sl['price']),
                    "bar_index": i
                })
                prev_trend = "BEARISH"
                
    return events

def detect_order_blocks(df: pd.DataFrame, min_displacement_atr: float = 1.2) -> list[dict]:
    """
    Identifies institutional Order Blocks:
    Bullish OB: The last bearish candle before strong aggressive impulse moving upward.
    Bearish OB: The last bullish candle before strong aggressive impulse moving downward.
    """
    obs = []
    opens = df['Open'].values
    closes = df['Close'].values
    highs = df['High'].values
    lows = df['Low'].values
    times = df.index
    
    # Calculate ATR approx
    body_sizes = np.abs(closes - opens)
    avg_body = np.mean(body_sizes[-50:]) if len(body_sizes) >= 50 else np.mean(body_sizes)
    
    # Scan recent 60 candles
    start_idx = max(2, len(df) - 60)
    for i in range(start_idx, len(df) - 2):
        # Bullish OB Check: Candle i is bearish, followed by i+1 and i+2 massive bullish displacement
        if closes[i] < opens[i]:  # Bearish candle
            displacement = closes[i+2] - opens[i+1]
            if displacement > (avg_body * min_displacement_atr) and closes[i+2] > highs[i]:
                # Check mitigation
                future_lows = lows[i+3:] if i+3 < len(df) else []
                mitigated = len(future_lows) > 0 and np.min(future_lows) < lows[i]
                
                obs.append({
                    "type": "BULLISH_OB",
                    "time": times[i],
                    "top": float(max(opens[i], closes[i])),
                    "bottom": float(lows[i]),
                    "mitigated": mitigated,
                    "active": not mitigated
                })
                
        # Bearish OB Check: Candle i is bullish, followed by massive bearish displacement
        elif closes[i] > opens[i]:  # Bullish candle
            displacement = opens[i+1] - closes[i+2]
            if displacement > (avg_body * min_displacement_atr) and closes[i+2] < lows[i]:
                future_highs = highs[i+3:] if i+3 < len(df) else []
                mitigated = len(future_highs) > 0 and np.max(future_highs) > highs[i]
                
                obs.append({
                    "type": "BEARISH_OB",
                    "time": times[i],
                    "top": float(highs[i]),
                    "bottom": float(min(opens[i], closes[i])),
                    "mitigated": mitigated,
                    "active": not mitigated
                })
                
    return obs

def calculate_dealing_range(swing_highs: list[dict], swing_lows: list[dict], current_price: float) -> dict:
    """
    Calculates Dealing Range, Equilibrium (0.5), Premium and Discount zones, and OTE.
    """
    if not swing_highs or not swing_lows:
        return {"status": "UNKNOWN"}
        
    latest_sh = swing_highs[-1]['price']
    latest_sl = swing_lows[-1]['price']
    
    if latest_sh <= latest_sl:
        # Fallback to absolute max/min of recent 2 swings
        latest_sh = max([s['price'] for s in swing_highs[-2:]])
        latest_sl = min([s['price'] for s in swing_lows[-2:]])
        
    range_span = latest_sh - latest_sl
    if range_span <= 0:
        return {"status": "INVALID_RANGE"}
        
    equilibrium = latest_sl + (range_span * 0.5)
    ote_62 = latest_sl + (range_span * 0.618)
    ote_79 = latest_sl + (range_span * 0.786)
    
    current_pct = ((current_price - latest_sl) / range_span) * 100
    
    zone = "PREMIUM" if current_price > equilibrium else "DISCOUNT"
    if 50.0 <= current_pct <= 61.8:
        zone_detail = "EQUILIBRIUM_TRANSITION"
    elif current_pct > 70.0:
        zone_detail = "DEEP_PREMIUM (High Sell Probability)"
    elif current_pct < 30.0:
        zone_detail = "DEEP_DISCOUNT (High Buy Probability)"
    else:
        zone_detail = f"{zone} ZONE"
        
    return {
        "range_high": round(latest_sh, 2),
        "range_low": round(latest_sl, 2),
        "equilibrium": round(equilibrium, 2),
        "ote_618": round(ote_62, 2),
        "ote_786": round(ote_79, 2),
        "current_price": round(current_price, 2),
        "relative_position_pct": round(current_pct, 1),
        "zone": zone,
        "zone_detail": zone_detail
    }

def detect_liquidity_sweeps(df: pd.DataFrame, swing_highs: list[dict], swing_lows: list[dict]) -> list[dict]:
    """
    Detects Liquidity Sweeps (Turtle Soup):
    BSL Sweep: Price wicks above previous Swing High but closes below it.
    SSL Sweep: Price wicks below previous Swing Low but closes above it.
    """
    sweeps = []
    if len(df) < 5 or not swing_highs or not swing_lows:
        return sweeps
        
    recent_bars = df.tail(10)
    
    # Check BSL Sweeps
    for sh in swing_highs[-3:]:
        sh_price = sh['price']
        for idx, row in recent_bars.iterrows():
            if row['High'] > sh_price and row['Close'] < sh_price:
                sweeps.append({
                    "type": "BSL_SWEEP (Sell Signal / Turtle Soup)",
                    "level": round(sh_price, 2),
                    "time": idx,
                    "action": "BEARISH_REVERSAL_TRIGGER"
                })
                break
                
    # Check SSL Sweeps
    for sl in swing_lows[-3:]:
        sl_price = sl['price']
        for idx, row in recent_bars.iterrows():
            if row['Low'] < sl_price and row['Close'] > sl_price:
                sweeps.append({
                    "type": "SSL_SWEEP (Buy Signal / Turtle Soup)",
                    "level": round(sl_price, 2),
                    "time": idx,
                    "action": "BULLISH_REVERSAL_TRIGGER"
                })
                break
                
    return sweeps

def check_ict_killzone() -> dict:
    """
    Checks if current UTC time falls within institutional ICT Killzones.
    """
    now_utc = datetime.now(timezone.utc)
    hour = now_utc.hour
    minute = now_utc.minute
    current_time_str = now_utc.strftime("%H:%M UTC")
    
    # London Open: 07:00 - 10:00 UTC
    if 7 <= hour < 10:
        return {"active": True, "session": "LONDON_OPEN", "name": "London Open Killzone (High Volatility)", "time_utc": current_time_str}
    # New York Open: 12:00 - 15:00 UTC
    elif 12 <= hour < 15:
        return {"active": True, "session": "NEW_YORK_OPEN", "name": "New York Open Killzone (High Volatility)", "time_utc": current_time_str}
    # London Close: 15:00 - 17:00 UTC
    elif 15 <= hour < 17:
        return {"active": True, "session": "LONDON_CLOSE", "name": "London Close Killzone (Profit Taking)", "time_utc": current_time_str}
    # Asian Session: 00:00 - 05:00 UTC
    elif 0 <= hour < 5:
        return {"active": True, "session": "ASIAN_RANGE", "name": "Asian Session (Accumulation / Consolidation)", "time_utc": current_time_str}
    else:
        return {"active": False, "session": "OFF_HOURS", "name": "Outside Major Killzones (Standard Market Flow)", "time_utc": current_time_str}
