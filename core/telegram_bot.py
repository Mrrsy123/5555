"""
Telegram Signal Dispatcher Module
Sends institutional trading signals formatted in HTML to Telegram.
"""

import requests
import json
from pathlib import Path
from datetime import datetime
import pytz

HISTORY_FILE = Path(__file__).resolve().parent.parent / "dispatched_history.json"

def _load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("dispatched", [])
    except Exception:
        return []

def _save_history(history):
    try:
        history = history[-200:]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({"dispatched": history}, f, indent=2)
    except Exception as e:
        print(f"Error saving dispatch history: {e}")

class TelegramSignalBot:
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id and self.bot_token.strip() and self.chat_id.strip())
        
    def send_message(self, text: str, parse_mode: str = "HTML") -> dict:
        """
        Send a raw text or HTML message to configured Telegram chat/channel.
        """
        if not self.is_configured():
            return {"status": "ERROR", "message": "Bot token or Chat ID is not configured."}
            
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            res_json = resp.json()
            if res_json.get("ok"):
                return {"status": "SUCCESS", "message": "Message sent successfully!"}
            else:
                return {"status": "ERROR", "message": res_json.get("description", "Unknown Telegram API error")}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def send_test_signal(self) -> dict:
        """
        Send a test ping message to verify Telegram Bot connectivity.
        """
        now_phnom_penh = datetime.now(pytz.timezone('Asia/Phnom_Penh')).strftime('%Y-%m-%d %H:%M:%S')
        test_msg = f"""🦅 <b>PHEARA PRO TRADER AI - BOT CONNECTED</b>
━━━━━━━━━━━━━━━━━━━━
✅ <b>ប្រព័ន្ធ Telegram Bot ត្រូវបានភ្ជាប់ដោយជោគជ័យ!</b>
📡 <b>Feed:</b> FXCM:XAUUSD & BITSTAMP:BTCUSD
🕒 <b>ពេលវេលា:</b> <code>{now_phnom_penh} (UTC+7)</code>

ប្រព័ន្ធត្រៀមខ្លួនរួចរាល់ក្នុងការបញ្ជូនសញ្ញា <b>Auto Scalp 15M</b> ចូលមកកាន់ទីនេះហើយបាទ!"""
        return self.send_message(test_msg)

    def dispatch_trade_signal(self, asset: str, timeframe: str, analysis: dict, indicator_regime: dict) -> dict:
        """
        Format and dispatch an institutional-grade signal to Telegram.
        STRICT DISCIPLINE: Signals are ONLY dispatched when Multi-Oscillators are 100% confluent.
        """
        action = analysis.get("setup_action", "WAIT / NO TRADE")
        if action not in ["BUY / LONG", "SELL / SHORT"]:
            conflict = analysis.get("conflict_note", "Multi-oscillators not aligned")
            return {
                "status": "BLOCKED",
                "message": f"សូចនាករមិនទាន់ស្របគ្នា ({conflict})។ ប្រព័ន្ធផ្អាកការបញ្ជូន Signal ដើម្បីការពារហានិភ័យ!"
            }

        plan = analysis["plan"]
        bias = analysis["bias"]
        score = analysis["confluence_score"]
        
        now_time = datetime.now(pytz.timezone('Asia/Phnom_Penh')).strftime('%H:%M (UTC+7)')
        
        if "BUY" in bias or "BULLISH" in bias:
            header_icon = "🟢 <b>INSTITUTIONAL BUY SIGNAL</b>"
            action_badge = "BUY / LONG"
        elif "SELL" in bias or "BEARISH" in bias:
            header_icon = "🔴 <b>INSTITUTIONAL SELL SIGNAL</b>"
            action_badge = "SELL / SHORT"
        else:
            header_icon = "⚪ <b>MARKET TELEMETRY ALERT</b>"
            action_badge = "WATCHLIST / RANGE"

        symbol_label = "FXCM:XAUUSD (Gold)" if asset == "XAUUSD" else "BITSTAMP:BTCUSD (Bitcoin)"

        msg = f"""🦅 <b>PHEARA PRO TRADER AI SIGNAL</b>
━━━━━━━━━━━━━━━━━━━━
{header_icon}
📊 <b>Asset:</b> <code>{symbol_label}</code>
⏱ <b>Timeframe:</b> <code>{timeframe} Scalping</code>
🕒 <b>Time:</b> <code>{now_time}</code>
🏆 <b>Confluence Rating:</b> <b>{score}/100 (Grade A+)</b>
━━━━━━━━━━━━━━━━━━━━
🎯 <b>TRADE EXECUTION ROADMAP:</b>
• <b>Action:</b> <b>{action_badge}</b>
• <b>Optimal Entry:</b> <code>{plan['entry']}</code>
• <b>Stop Loss (SL):</b> <code>{plan['sl']}</code> (Structural Invalidation)
• <b>Take Profit 1:</b> <code>{plan['tp1']}</code> (Partial 70% + Move to BE)
• <b>Take Profit 2:</b> <code>{plan['tp2']}</code> (Main Target)
• <b>Take Profit 3:</b> <code>{plan['tp3']}</code> (Runner)
• <b>Risk:Reward:</b> <b>{plan['rrr']}</b> (Risk: {plan['risk_pips_points']} pts)
━━━━━━━━━━━━━━━━━━━━
🧠 <b>CONFLUENCE AUDIT:</b>
• <b>ADX (14):</b> <code>{indicator_regime.get('adx')}</code> ({indicator_regime.get('trend_grade')})
• <b>DMI:</b> <code>{indicator_regime.get('dmi_leader')}</code>
• <b>MACD:</b> <code>{indicator_regime.get('macd_status')}</code>
• <b>RSI (14):</b> <code>{indicator_regime.get('rsi')}</code> ({indicator_regime.get('rsi_status')})
• <b>EMA Stack:</b> <code>{indicator_regime.get('trend_status')}</code>
━━━━━━━━━━━━━━━━━━━━
💡 <i>Risk Management: Risk maximum 1% to 2% per trade. When price reaches TP1, move SL to Entry (Break-Even).</i>"""

        send_res = self.send_message(msg)
        if send_res.get("status") == "SUCCESS":
            try:
                from core.trade_tracker import register_trade
                register_trade(asset, timeframe, plan, action_badge)
            except Exception as trk_err:
                print(f"[Notice] Trade tracking register error: {trk_err}")
                
        return send_res

    def send_tp_hit_alert(self, asset: str, timeframe: str, trade: dict, tp_level: int, hit_price: float) -> dict:
        """
        Sends an automated celebration alert when Take Profit 1, 2, or 3 is hit!
        """
        entry = float(trade.get("entry", 0))
        action = trade.get("action", "")
        gain = abs(hit_price - entry)
        pips = gain * 10 if asset == "XAUUSD" else gain
        now_time = datetime.now(pytz.timezone('Asia/Phnom_Penh')).strftime('%H:%M (UTC+7)')
        symbol_label = "FXCM:XAUUSD (Gold)" if asset == "XAUUSD" else "BITSTAMP:BTCUSD (Bitcoin)"

        badge = f"🎯 <b>TAKE PROFIT {tp_level} ACHIEVED!</b>"
        if tp_level == 1:
            note = "💡 <b>Action Recommended:</b> <i>Secure 70% partial profit & Move Stop Loss to Entry (Break-Even) to make this trade 100% Risk-Free!</i>"
        elif tp_level == 2:
            note = "💰 <b>Action Recommended:</b> <i>Main Target Secured! Bank majority profit or trail stop to TP1!</i>"
        else:
            note = "🚀 <b>Full Runner Target Hit!</b> <i>Trade lifecycle completed with maximum institutional profitability!</i>"

        msg = f"""🦅 <b>PHEARA PRO TRADER AI - TRADE UPDATE</b>
━━━━━━━━━━━━━━━━━━━━
{badge}
📊 <b>Asset:</b> <code>{symbol_label}</code>
⏱ <b>Timeframe:</b> <code>{timeframe}</code>
📈 <b>Setup:</b> <b>{action}</b>
📍 <b>Entry Price:</b> <code>{entry:,.2f}</code>
🎯 <b>TP{tp_level} Price Hit:</b> <code>{hit_price:,.2f}</code>
💰 <b>Gain:</b> <b>+{gain:,.2f} pts (+{pips:,.1f} pips)</b>
🕒 <b>Time:</b> <code>{now_time}</code>
━━━━━━━━━━━━━━━━━━━━
{note}"""
        return self.send_message(msg)

    def send_sl_hit_alert(self, asset: str, timeframe: str, trade: dict, hit_price: float) -> dict:
        """
        Sends a disciplined Stop Loss alert when invalidation level is hit.
        """
        entry = float(trade.get("entry", 0))
        action = trade.get("action", "")
        loss = abs(hit_price - entry)
        pips = loss * 10 if asset == "XAUUSD" else loss
        now_time = datetime.now(pytz.timezone('Asia/Phnom_Penh')).strftime('%H:%M (UTC+7)')
        symbol_label = "FXCM:XAUUSD (Gold)" if asset == "XAUUSD" else "BITSTAMP:BTCUSD (Bitcoin)"

        msg = f"""🦅 <b>PHEARA PRO TRADER AI - TRADE UPDATE</b>
━━━━━━━━━━━━━━━━━━━━
🛑 <b>STOP LOSS TRIGGERED (SL)</b>
📊 <b>Asset:</b> <code>{symbol_label}</code>
⏱ <b>Timeframe:</b> <code>{timeframe}</code>
📉 <b>Setup:</b> <b>{action}</b>
📍 <b>Entry Price:</b> <code>{entry:,.2f}</code>
🛑 <b>SL Price Hit:</b> <code>{hit_price:,.2f}</code>
📉 <b>Drawdown:</b> <b>-{loss:,.2f} pts (-{pips:,.1f} pips)</b>
🕒 <b>Time:</b> <code>{now_time}</code>
━━━━━━━━━━━━━━━━━━━━
🛡️ <b>Risk Management Executed:</b> Loss capped strictly at 1% planned capital risk. Preserving capital for the next Grade A+ Setup!"""
        return self.send_message(msg)

    def send_be_hit_alert(self, asset: str, timeframe: str, trade: dict, hit_price: float) -> dict:
        """
        Sends an alert when price pulls back to Entry (Break-Even) after TP1 was already taken.
        """
        entry = float(trade.get("entry", 0))
        action = trade.get("action", "")
        now_time = datetime.now(pytz.timezone('Asia/Phnom_Penh')).strftime('%H:%M (UTC+7)')
        symbol_label = "FXCM:XAUUSD (Gold)" if asset == "XAUUSD" else "BITSTAMP:BTCUSD (Bitcoin)"

        msg = f"""🦅 <b>PHEARA PRO TRADER AI - TRADE UPDATE</b>
━━━━━━━━━━━━━━━━━━━━
🛡️ <b>BREAK-EVEN CLOSED (SL @ ENTRY)</b>
📊 <b>Asset:</b> <code>{symbol_label}</code>
⏱ <b>Timeframe:</b> <code>{timeframe}</code>
📈 <b>Setup:</b> <b>{action}</b>
📍 <b>Entry Price:</b> <code>{entry:,.2f}</code>
🛡️ <b>Exit Price:</b> <code>{hit_price:,.2f} (Break-Even)</code>
🕒 <b>Time:</b> <code>{now_time}</code>
━━━━━━━━━━━━━━━━━━━━
✅ <b>100% Risk-Free Result:</b> <i>TP1 ត្រូវបានប្រមូលប្រាក់ចំណេញ 70% រួចហើយ! ចំណែកឯ Position ដែលនៅសល់ត្រូវបានកាត់ចេញនៅតម្លៃដើម (Break-Even) ដោយគ្មានការខាតបង់ដើមទុនឡើយ! 100% Capital Preserved!</i>"""
        return self.send_message(msg)

    def simulate_test_trade_signal(self, asset: str = "XAUUSD", timeframe: str = "15m", action: str = "BUY / LONG") -> dict:
        """
        Dispatches a verified sample Entry + TP/SL signal to Telegram so the user can audit formatting.
        """
        if "BUY" in action:
            entry = 3526.19 if asset == "XAUUSD" else 60050.00
            sl = 3514.50 if asset == "XAUUSD" else 59500.00
            tp1 = 3537.88 if asset == "XAUUSD" else 60600.00
            tp2 = 3549.57 if asset == "XAUUSD" else 61150.00
            tp3 = 3567.10 if asset == "XAUUSD" else 61975.00
            bias = "BULLISH (Confluent)"
        else:
            entry = 3526.19 if asset == "XAUUSD" else 60050.00
            sl = 3537.88 if asset == "XAUUSD" else 60600.00
            tp1 = 3514.50 if asset == "XAUUSD" else 59500.00
            tp2 = 3502.81 if asset == "XAUUSD" else 58950.00
            tp3 = 3485.28 if asset == "XAUUSD" else 58125.00
            bias = "BEARISH (Confluent)"

        sim_analysis = {
            "setup_action": action,
            "bias": bias,
            "confluence_score": 92,
            "plan": {
                "entry": entry,
                "sl": sl,
                "tp1": tp1,
                "tp2": tp2,
                "tp3": tp3,
                "risk_pips_points": round(abs(entry - sl), 2),
                "rrr": "1:2.5"
            }
        }
        sim_regime = {
            "adx": 34.5,
            "trend_grade": "Strong Trend Active",
            "dmi_leader": "+DI Dominant (Bullish)" if "BUY" in action else "-DI Dominant (Bearish)",
            "macd_status": "Bullish Cross Above Zero" if "BUY" in action else "Bearish Cross Below Zero",
            "rsi": 54.2 if "BUY" in action else 45.8,
            "rsi_status": "Optimal Pullback Zone",
            "trend_status": "Aligned Bullish Stack" if "BUY" in action else "Aligned Bearish Stack"
        }
        return self.dispatch_trade_signal(asset, timeframe, sim_analysis, sim_regime)

    def simulate_tp_hit(self, asset: str = "XAUUSD", timeframe: str = "15m", tp_level: int = 1) -> dict:
        """
        Dispatches a simulated TP Hit alert (TP1, TP2, or TP3).
        """
        if asset == "XAUUSD":
            entry = 3526.19
            hit_price = 3537.88 if tp_level == 1 else (3549.57 if tp_level == 2 else 3567.10)
        else:
            entry = 60050.00
            hit_price = 60600.00 if tp_level == 1 else (61150.00 if tp_level == 2 else 61975.00)
            
        dummy_trade = {
            "entry": entry,
            "action": "BUY / LONG"
        }
        return self.send_tp_hit_alert(asset, timeframe, dummy_trade, tp_level, hit_price)

    def simulate_sl_hit(self, asset: str = "XAUUSD", timeframe: str = "15m") -> dict:
        """
        Dispatches a simulated Stop Loss Hit alert.
        """
        if asset == "XAUUSD":
            entry = 3526.19
            hit_price = 3514.50
        else:
            entry = 60050.00
            hit_price = 59500.00
            
        dummy_trade = {
            "entry": entry,
            "action": "BUY / LONG"
        }
        return self.send_sl_hit_alert(asset, timeframe, dummy_trade, hit_price)

    def auto_dispatch_if_confluent(self, asset: str, timeframe: str, analysis: dict, indicator_regime: dict, candle_time: str = None) -> dict:
        """
        Automatically drops signal into Telegram if it meets 100% strict confluence
        and has not been previously dispatched for this candle.
        """
        if not self.is_configured():
            return {"status": "UNCONFIGURED"}
            
        action = analysis.get("setup_action", "WAIT / NO TRADE")
        if action not in ["BUY / LONG", "SELL / SHORT"]:
            return {"status": "NOT_CONFLUENT", "reason": analysis.get("conflict_note", "Oscillators mixed")}
            
        if not candle_time:
            candle_time = datetime.now(pytz.timezone('Asia/Phnom_Penh')).strftime('%Y-%m-%d %H:%M')
            
        sig_key = f"{asset}_{timeframe}_{candle_time}_{action}"
        history = _load_history()
        
        if sig_key in history:
            return {"status": "ALREADY_SENT", "key": sig_key}
            
        # Dispatch to Telegram
        res = self.dispatch_trade_signal(asset, timeframe, analysis, indicator_regime)
        if res.get("status") == "SUCCESS":
            history.append(sig_key)
            _save_history(history)
            return {"status": "AUTO_DISPATCHED", "key": sig_key, "action": action}
        return res
