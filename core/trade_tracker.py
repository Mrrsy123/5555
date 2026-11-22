"""
Trade Tracker & Outcome Lifecycle Engine
Monitors open trading positions against live market price (High, Low, Close).
Automatically triggers Telegram alerts when Target (TP1, TP2, TP3) or Stop Loss (SL) is hit!
"""

import json
import time
from pathlib import Path
from datetime import datetime
import pytz

TRADES_FILE = Path(__file__).resolve().parent.parent / "active_trades.json"

def load_trades() -> list:
    if not TRADES_FILE.exists():
        return []
    try:
        with open(TRADES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("trades", [])
    except Exception:
        return []

def save_trades(trades: list):
    try:
        # Keep latest 100 historical trades
        trades = trades[-100:]
        with open(TRADES_FILE, "w", encoding="utf-8") as f:
            json.dump({"trades": trades}, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving trades: {e}")

def clear_closed_trades() -> int:
    """
    Cleans up closed historical trades, keeping only active OPEN positions.
    """
    trades = load_trades()
    open_trades = [t for t in trades if t.get("status") == "OPEN"]
    removed_count = len(trades) - len(open_trades)
    save_trades(open_trades)
    return removed_count

def clear_all_trades() -> int:
    """
    Completely resets the trade database.
    """
    trades = load_trades()
    total = len(trades)
    save_trades([])
    return total

def register_trade(asset: str, timeframe: str, plan: dict, action: str) -> dict:
    """
    Registers a new dispatched trade into active monitoring database.
    Prevents duplicate active trades for the same asset & timeframe.
    """
    trades = load_trades()
    entry = float(plan.get("entry", 0))
    sl = float(plan.get("sl", 0))
    tp1 = float(plan.get("tp1", 0))
    tp2 = float(plan.get("tp2", 0))
    tp3 = float(plan.get("tp3", tp2))
    
    # Check if an active trade is ALREADY running for this asset & timeframe
    for t in trades:
        if t.get("asset") == asset and t.get("timeframe") == timeframe and t.get("status") == "OPEN":
            return {"status": "ALREADY_ACTIVE", "id": t.get("id"), "trade": t}
                
    now_khmer = datetime.now(pytz.timezone('Asia/Phnom_Penh')).strftime('%Y-%m-%d %H:%M:%S')
    trade_id = f"{asset}_{timeframe}_{int(time.time())}"
    
    new_trade = {
        "id": trade_id,
        "asset": asset,
        "timeframe": timeframe,
        "action": action,
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "risk_pts": float(plan.get("risk_pips_points", abs(entry - sl))),
        "opened_at": now_khmer,
        "status": "OPEN",
        "tp1_hit": False,
        "tp2_hit": False,
        "tp3_hit": False,
        "sl_hit": False,
        "closed_at": None,
        "outcome": "RUNNING"
    }
    trades.append(new_trade)
    save_trades(trades)
    return {"status": "REGISTERED", "trade": new_trade}

def monitor_trade_outcomes(asset: str, timeframe: str, latest_bar: dict, bot) -> list:
    """
    Checks active open trades against the current candle High and Low.
    Dispatches instant alerts to Telegram when TP or SL is triggered.
    Includes institutional Break-Even (BE) handling once TP1 is secured!
    """
    trades = load_trades()
    updated = False
    events = []
    
    high = float(latest_bar.get("High", 0))
    low = float(latest_bar.get("Low", 0))
    close = float(latest_bar.get("Close", 0))
    now_khmer = datetime.now(pytz.timezone('Asia/Phnom_Penh')).strftime('%Y-%m-%d %H:%M:%S')
    
    for t in trades:
        if t.get("asset") == asset and t.get("timeframe") == timeframe and t.get("status") == "OPEN":
            action = t.get("action", "")
            entry = t.get("entry", 0)
            sl = t.get("sl", 0)
            tp1 = t.get("tp1", 0)
            tp2 = t.get("tp2", 0)
            tp3 = t.get("tp3", 0)
            
            # ---------------------------------------------
            # BUY POSITION EVALUATION
            # ---------------------------------------------
            if "BUY" in action:
                # 0. Break-Even Check (If TP1 was hit, SL was moved to Entry)
                if t.get("tp1_hit") and low <= entry and entry > 0:
                    t["status"] = "CLOSED"
                    t["outcome"] = "BE_CLOSED"
                    t["closed_at"] = now_khmer
                    updated = True
                    events.append({"type": "BE", "trade": t, "hit_price": entry})
                    if bot and bot.is_configured():
                        if hasattr(bot, "send_be_hit_alert"):
                            bot.send_be_hit_alert(asset, timeframe, t, hit_price=entry)
                    continue

                # 1. Check Stop Loss Hit (Only if TP1 has not been hit)
                if not t.get("tp1_hit") and low <= sl and sl > 0 and not t.get("sl_hit"):
                    t["sl_hit"] = True
                    t["status"] = "CLOSED"
                    t["outcome"] = "SL_HIT"
                    t["closed_at"] = now_khmer
                    updated = True
                    events.append({"type": "SL", "trade": t, "hit_price": sl})
                    if bot and bot.is_configured():
                        bot.send_sl_hit_alert(asset, timeframe, t, hit_price=sl)
                    continue  # Stop evaluating once SL is hit
                    
                # 2. Check Take Profit 1 Hit
                if high >= tp1 and tp1 > 0 and not t.get("tp1_hit"):
                    t["tp1_hit"] = True
                    updated = True
                    events.append({"type": "TP1", "trade": t, "hit_price": tp1})
                    if bot and bot.is_configured():
                        bot.send_tp_hit_alert(asset, timeframe, t, tp_level=1, hit_price=tp1)
                        
                # 3. Check Take Profit 2 Hit
                if high >= tp2 and tp2 > 0 and not t.get("tp2_hit"):
                    t["tp2_hit"] = True
                    updated = True
                    events.append({"type": "TP2", "trade": t, "hit_price": tp2})
                    if bot and bot.is_configured():
                        bot.send_tp_hit_alert(asset, timeframe, t, tp_level=2, hit_price=tp2)
                        
                # 4. Check Take Profit 3 (Final Runner) Hit
                if high >= tp3 and tp3 > 0 and not t.get("tp3_hit"):
                    t["tp3_hit"] = True
                    t["status"] = "CLOSED"
                    t["outcome"] = "TP3_FULL_HIT"
                    t["closed_at"] = now_khmer
                    updated = True
                    events.append({"type": "TP3", "trade": t, "hit_price": tp3})
                    if bot and bot.is_configured():
                        bot.send_tp_hit_alert(asset, timeframe, t, tp_level=3, hit_price=tp3)

            # ---------------------------------------------
            # SELL POSITION EVALUATION
            # ---------------------------------------------
            elif "SELL" in action:
                # 0. Break-Even Check (If TP1 was hit, SL was moved to Entry)
                if t.get("tp1_hit") and high >= entry and entry > 0:
                    t["status"] = "CLOSED"
                    t["outcome"] = "BE_CLOSED"
                    t["closed_at"] = now_khmer
                    updated = True
                    events.append({"type": "BE", "trade": t, "hit_price": entry})
                    if bot and bot.is_configured():
                        if hasattr(bot, "send_be_hit_alert"):
                            bot.send_be_hit_alert(asset, timeframe, t, hit_price=entry)
                    continue

                # 1. Check Stop Loss Hit (Only if TP1 has not been hit)
                if not t.get("tp1_hit") and high >= sl and sl > 0 and not t.get("sl_hit"):
                    t["sl_hit"] = True
                    t["status"] = "CLOSED"
                    t["outcome"] = "SL_HIT"
                    t["closed_at"] = now_khmer
                    updated = True
                    events.append({"type": "SL", "trade": t, "hit_price": sl})
                    if bot and bot.is_configured():
                        bot.send_sl_hit_alert(asset, timeframe, t, hit_price=sl)
                    continue  # Stop evaluating once SL is hit
                    
                # 2. Check Take Profit 1 Hit
                if low <= tp1 and tp1 > 0 and not t.get("tp1_hit"):
                    t["tp1_hit"] = True
                    updated = True
                    events.append({"type": "TP1", "trade": t, "hit_price": tp1})
                    if bot and bot.is_configured():
                        bot.send_tp_hit_alert(asset, timeframe, t, tp_level=1, hit_price=tp1)
                        
                # 3. Check Take Profit 2 Hit
                if low <= tp2 and tp2 > 0 and not t.get("tp2_hit"):
                    t["tp2_hit"] = True
                    updated = True
                    events.append({"type": "TP2", "trade": t, "hit_price": tp2})
                    if bot and bot.is_configured():
                        bot.send_tp_hit_alert(asset, timeframe, t, tp_level=2, hit_price=tp2)
                        
                # 4. Check Take Profit 3 (Final Runner) Hit
                if low <= tp3 and tp3 > 0 and not t.get("tp3_hit"):
                    t["tp3_hit"] = True
                    t["status"] = "CLOSED"
                    t["outcome"] = "TP3_FULL_HIT"
                    t["closed_at"] = now_khmer
                    updated = True
                    events.append({"type": "TP3", "trade": t, "hit_price": tp3})
                    if bot and bot.is_configured():
                        bot.send_tp_hit_alert(asset, timeframe, t, tp_level=3, hit_price=tp3)
                    t["closed_at"] = now_khmer
                    updated = True
                    events.append({"type": "TP3", "trade": t, "hit_price": tp3})
                    if bot and bot.is_configured():
                        bot.send_tp_hit_alert(asset, timeframe, t, tp_level=3, hit_price=tp3)
                        
    if updated:
        save_trades(trades)
        
    return events
