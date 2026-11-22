"""
Technical Indicators Engine:
Computes:
1. EMA 20, 50, 200 & Dynamic Stacks
2. ATR (14) for Volatility & Dynamic Risk Sizing
3. RSI (14) with Overbought/Oversold and Pullback Zones
4. MACD (12, 26, 9) with Exact Line/Signal Crosses & Histogram
5. ADX (14) with +DI, -DI and Institutional Trend Strength Grading
"""

import pandas as pd
import numpy as np

def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate EMA 20/50/200, ATR(14), RSI(14), MACD(12,26,9), and ADX(14)
    and append them as columns in the DataFrame.
    """
    data = df.copy()
    
    # 1. EMAs
    data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()
    data['EMA50'] = data['Close'].ewm(span=50, adjust=False).mean()
    data['EMA200'] = data['Close'].ewm(span=200, adjust=False).mean()
    
    # 2. True Range & ATR (14)
    high_low = data['High'] - data['Low']
    high_close = (data['High'] - data['Close'].shift()).abs()
    low_close = (data['Low'] - data['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    data['TR'] = tr
    data['ATR'] = tr.rolling(14).mean().bfill()
    
    # 3. RSI (14)
    delta = data['Close'].diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    
    rs = avg_gain / (avg_loss + 1e-10)
    data['RSI'] = (100.0 - (100.0 / (1.0 + rs))).fillna(50.0)
    
    # 4. MACD (12, 26, 9)
    ema12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema26 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = ema12 - ema26
    data['MACD_SIGNAL'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['MACD_HIST'] = data['MACD'] - data['MACD_SIGNAL']
    
    # 5. ADX (14) & DMI (+DI, -DI)
    up_move = data['High'] - data['High'].shift()
    down_move = data['Low'].shift() - data['Low']
    
    pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    
    pos_dm_series = pd.Series(pos_dm, index=data.index)
    neg_dm_series = pd.Series(neg_dm, index=data.index)
    
    smooth_tr = tr.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    smooth_pos_dm = pos_dm_series.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    smooth_neg_dm = neg_dm_series.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    
    data['PLUS_DI'] = (100.0 * (smooth_pos_dm / (smooth_tr + 1e-10))).fillna(20.0)
    data['MINUS_DI'] = (100.0 * (smooth_neg_dm / (smooth_tr + 1e-10))).fillna(20.0)
    
    di_diff = (data['PLUS_DI'] - data['MINUS_DI']).abs()
    di_sum = data['PLUS_DI'] + data['MINUS_DI']
    dx = (100.0 * (di_diff / (di_sum + 1e-10))).fillna(20.0)
    data['ADX'] = dx.ewm(alpha=1/14, min_periods=14, adjust=False).mean().fillna(20.0)
    
    return data

# Backward compatibility alias
calculate_emas = calculate_technical_indicators

def analyze_indicator_telemetry(df: pd.DataFrame) -> dict:
    """
    Produce comprehensive indicator metrics: EMAs, RSI, MACD Crosses, and ADX strength.
    """
    if len(df) < 5:
        return {"status": "INSUFFICIENT_DATA", "close": 0.0}
        
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    close = float(latest['Close'])
    ema20 = float(latest.get('EMA20', close))
    ema50 = float(latest.get('EMA50', close))
    ema200 = float(latest.get('EMA200', close))
    atr = float(latest.get('ATR', abs(latest['High'] - latest['Low'])))
    
    # EMA Alignment
    is_bullish_stack = (ema20 > ema50) and (ema50 > ema200)
    is_bearish_stack = (ema20 < ema50) and (ema50 < ema200)
    price_vs_ema200 = "ABOVE" if close > ema200 else "BELOW"
    price_vs_ema50 = "ABOVE" if close > ema50 else "BELOW"
    price_vs_ema20 = "ABOVE" if close > ema20 else "BELOW"
    
    # 2. RSI Metrics
    rsi = float(latest.get('RSI', 50.0))
    rsi_status = "NEUTRAL"
    if rsi >= 70.0:
        rsi_status = "OVERBOUGHT (High Sell Reversal Probability)"
    elif rsi <= 30.0:
        rsi_status = "OVERSOLD (High Buy Bounce Probability)"
    elif 40.0 <= rsi <= 60.0:
        rsi_status = "VALUE_PULLBACK_ZONE (Optimal Trend Continuation)"
        
    # 3. MACD Crosses
    macd = float(latest.get('MACD', 0.0))
    macd_signal = float(latest.get('MACD_SIGNAL', 0.0))
    macd_hist = float(latest.get('MACD_HIST', 0.0))
    
    # Scan last 3 candles for fresh crosses
    recent = df.tail(min(5, len(df)))
    macd_bullish_cross = False
    macd_bearish_cross = False
    for i in range(1, len(recent)):
        if (recent['MACD'].iloc[i] > recent['MACD_SIGNAL'].iloc[i]) and (recent['MACD'].iloc[i-1] <= recent['MACD_SIGNAL'].iloc[i-1]):
            macd_bullish_cross = True
        if (recent['MACD'].iloc[i] < recent['MACD_SIGNAL'].iloc[i]) and (recent['MACD'].iloc[i-1] >= recent['MACD_SIGNAL'].iloc[i-1]):
            macd_bearish_cross = True
            
    macd_status = "BULLISH_MOMENTUM" if macd > macd_signal else "BEARISH_MOMENTUM"
    if macd_bullish_cross:
        macd_status = "FRESH_BULLISH_CROSS (🚀 Buy Trigger Ignition)"
    elif macd_bearish_cross:
        macd_status = "FRESH_BEARISH_CROSS (🔻 Sell Trigger Ignition)"
        
    # 4. ADX & DMI Strength Metrics
    adx = float(latest.get('ADX', 20.0))
    plus_di = float(latest.get('PLUS_DI', 20.0))
    minus_di = float(latest.get('MINUS_DI', 20.0))
    
    adx_trend = "RISING" if adx > float(prev.get('ADX', adx)) else "FALLING"
    
    if adx < 20.0:
        adx_strength = "WEAK / SIDEWAYS (❌ Warning: Choppy Market / High Fakeout Risk)"
        trend_grade = "CHOPPY"
    elif 20.0 <= adx < 25.0:
        adx_strength = "TREND_EMERGING (⚠️ Trend heating up)"
        trend_grade = "EMERGING"
    elif 25.0 <= adx < 40.0:
        adx_strength = "STRONG_TREND (✅ The Sweet Spot for EMA Pullback Scalping)"
        trend_grade = "STRONG"
    elif 40.0 <= adx < 50.0:
        adx_strength = "VERY_STRONG_TREND (🚀 High Velocity Move)"
        trend_grade = "VERY_STRONG"
    else:
        adx_strength = "EXTREME_TREND (⚠️ Overextended / Climax Risk)"
        trend_grade = "EXTREME"
        
    dmi_leader = "BUYERS_IN_CONTROL (+DI > -DI)" if plus_di > minus_di else "SELLERS_IN_CONTROL (-DI > +DI)"
    
    # Overall Technical Regime
    if is_bullish_stack and price_vs_ema200 == "ABOVE":
        trend_status = "STRONG_BULLISH"
        summary_km = f"និន្នាការកើនឡើងខ្លាំង (Bullish Stack: 20 > 50 > 200) | ADX={adx:.1f} ({trend_grade})"
    elif is_bearish_stack and price_vs_ema200 == "BELOW":
        trend_status = "STRONG_BEARISH"
        summary_km = f"និន្នាការធ្លាក់ចុះខ្លាំង (Bearish Stack: 20 < 50 < 200) | ADX={adx:.1f} ({trend_grade})"
    elif close > ema200:
        trend_status = "MODERATE_BULLISH"
        summary_km = f"និន្នាការឡើងមធ្យម (តម្លៃលើ EMA200 តែមាន Pullback) | ADX={adx:.1f}"
    else:
        trend_status = "MODERATE_BEARISH"
        summary_km = f"និន្នាការធ្លាក់មធ្យម (តម្លៃក្រោម EMA200 តែមាន Pullback) | ADX={adx:.1f}"
        
    return {
        "close": round(close, 3),
        "ema20": round(ema20, 3),
        "ema50": round(ema50, 3),
        "ema200": round(ema200, 3),
        "atr": round(atr, 3),
        "is_bullish_stack": is_bullish_stack,
        "is_bearish_stack": is_bearish_stack,
        "price_vs_ema200": price_vs_ema200,
        "price_vs_ema50": price_vs_ema50,
        "price_vs_ema20": price_vs_ema20,
        # RSI
        "rsi": round(rsi, 2),
        "rsi_status": rsi_status,
        # MACD
        "macd": round(macd, 3),
        "macd_signal": round(macd_signal, 3),
        "macd_hist": round(macd_hist, 3),
        "macd_bullish_cross": macd_bullish_cross,
        "macd_bearish_cross": macd_bearish_cross,
        "macd_status": macd_status,
        # ADX & DMI
        "adx": round(adx, 2),
        "plus_di": round(plus_di, 2),
        "minus_di": round(minus_di, 2),
        "adx_strength": adx_strength,
        "adx_trend": adx_trend,
        "trend_grade": trend_grade,
        "dmi_leader": dmi_leader,
        "trend_status": trend_status,
        "summary_km": summary_km
    }

# Backward compatibility alias
analyze_ema_regime = analyze_indicator_telemetry
