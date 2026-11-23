"""
Local AI Analyst & Institutional Reasoning Engine.
Synthesizes Technicals (EMA 20/50/200, ADX, MACD, RSI), SMC/ICT structure to generate:
- Precision Real-Time Scalping Execution (Entry anchored to Live Tick, Tight Structural SL, Scalp TPs)
- Institutional Confluence Score (0-100)
- Deep Narrative Analysis in Khmer (ភាសាខ្មែរ) & English
"""

import requests
import json

class LocalAIAnalyst:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url

    def analyze(self, symbol: str, timeframe: str, df, ema_regime: dict, smc_data: dict) -> dict:
        current_price = float(ema_regime["close"])
        atr = float(ema_regime.get("atr", current_price * 0.003))
        
        # 1. Extract Institutional Multi-Oscillator Telemetry
        is_bullish_stack = ema_regime.get("is_bullish_stack", False)
        is_bearish_stack = ema_regime.get("is_bearish_stack", False)
        price_vs_ema200 = ema_regime.get("price_vs_ema200", "BELOW")
        price_vs_ema50 = ema_regime.get("price_vs_ema50", "BELOW")
        price_vs_ema20 = ema_regime.get("price_vs_ema20", "BELOW")
        
        # ADX & DMI
        adx = float(ema_regime.get("adx", 20.0))
        plus_di = float(ema_regime.get("plus_di", 20.0))
        minus_di = float(ema_regime.get("minus_di", 20.0))
        trend_grade = ema_regime.get("trend_grade", "NORMAL")
        
        # MACD
        macd = float(ema_regime.get("macd", 0.0))
        macd_signal = float(ema_regime.get("macd_signal", 0.0))
        macd_hist = float(ema_regime.get("macd_hist", 0.0))
        macd_bull_cross = bool(ema_regime.get("macd_bullish_cross", False))
        macd_bear_cross = bool(ema_regime.get("macd_bearish_cross", False))
        
        # RSI
        rsi = float(ema_regime.get("rsi", 50.0))
        
        # 2. Strict Multi-Oscillator Conflict Auditing
        conflicts = []
        
        # Check A: ADX Trend Filter (Veto if choppy sideways range)
        if adx < 20.0:
            conflicts.append(f"ADX={adx:.1f} < 20 (ទីផ្សារ Sideways គ្មានកម្លាំងច្បាស់)")
            
        # Check B: MACD vs EMA Conflict
        if (macd_bull_cross or (macd > macd_signal and macd_hist > 0)) and (price_vs_ema200 == "BELOW" or is_bearish_stack or price_vs_ema50 == "BELOW"):
            conflicts.append("MACD Bullish Cross ផ្ទុយនឹង EMA Bearish Trend")
            
        if (macd_bear_cross or (macd < macd_signal and macd_hist < 0)) and (price_vs_ema200 == "ABOVE" or is_bullish_stack or price_vs_ema50 == "ABOVE"):
            conflicts.append("MACD Bearish Momentum ផ្ទុយនឹង EMA Bullish Trend")
            
        # Check C: DMI Directional Conflict
        if plus_di > minus_di and (macd < macd_signal and macd_hist < 0):
            conflicts.append("+DI កម្លាំងទិញ ផ្ទុយនឹង MACD Momentum អវិជ្ជមាន")
            
        if minus_di > plus_di and (macd > macd_signal and macd_hist > 0):
            conflicts.append("-DI កម្លាំងលក់ ផ្ទុយនឹង MACD Momentum វិជ្ជមាន")
            
        # Check D: RSI Overbought / Oversold Veto
        if rsi >= 70.0:
            conflicts.append(f"RSI={rsi:.1f} Overbought ខ្ពស់ពេក (ប្រឈមនឹងការទាញទម្លាក់ - ហាម BUY)")
            
        if rsi <= 30.0:
            conflicts.append(f"RSI={rsi:.1f} Oversold ជ្រៅពេក (ប្រឈមនឹងការងើបឡើងវិញ - ហាម SELL)")

        # 3. EMA 20 / EMA 50 Cross & Retest Dynamic Entry Check
        ema20_above_ema50 = ema_regime.get("ema20_above_ema50", (ema_regime.get("ema20", 0) > ema_regime.get("ema50", 0)))
        ema20_below_ema50 = ema_regime.get("ema20_below_ema50", (ema_regime.get("ema20", 0) < ema_regime.get("ema50", 0)))
        touches_ema_entry = ema_regime.get("touches_ema_entry_zone", False)
        ema_touch_label = ema_regime.get("ema_touch_label", "")

        # Check E: Price must touch EMA 20 or EMA 50 for Entry trigger!
        if ema20_above_ema50 and not touches_ema_entry:
            conflicts.append("រង់ចាំតម្លៃទាញថយក្រោយមកប៉ះ EMA 20 ឬ EMA 50 ដើម្បីចូល Entry (Awaiting EMA Retest)")
        if ema20_below_ema50 and not touches_ema_entry:
            conflicts.append("រង់ចាំតម្លៃងើបឡើងមកប៉ះ EMA 20 ឬ EMA 50 ដើម្បីចូល Entry (Awaiting EMA Retest)")
            
        # 4. Check for TRUE Full Bullish Alignment (EMA 20 > EMA 50 + Touches EMA 20/50 + Momentum)
        bullish_ema_aligned = (ema20_above_ema50 and touches_ema_entry and (current_price >= ema_regime.get("ema50", 0) * 0.998))
        bullish_adx_aligned = (adx >= 20.0 and plus_di > minus_di)
        bullish_macd_aligned = (macd > macd_signal and (macd_hist > 0 or macd_bull_cross))
        bullish_rsi_aligned = (38.0 <= rsi <= 68.0)
        
        is_true_bullish = (
            bullish_ema_aligned and
            bullish_adx_aligned and
            bullish_macd_aligned and
            bullish_rsi_aligned and
            not any("Bearish" in c or "Overbought" in c for c in conflicts if "Awaiting EMA" not in c)
        )
        
        # 5. Check for TRUE Full Bearish Alignment (EMA 20 < EMA 50 + Touches EMA 20/50 + Momentum)
        bearish_ema_aligned = (ema20_below_ema50 and touches_ema_entry and (current_price <= ema_regime.get("ema50", 0) * 1.002))
        bearish_adx_aligned = (adx >= 20.0 and minus_di > plus_di)
        bearish_macd_aligned = (macd < macd_signal and (macd_hist < 0 or macd_bear_cross))
        bearish_rsi_aligned = (32.0 <= rsi <= 62.0)
        
        is_true_bearish = (
            bearish_ema_aligned and
            bearish_adx_aligned and
            bearish_macd_aligned and
            bearish_rsi_aligned and
            not any("Bullish" in c or "Oversold" in c for c in conflicts if "Awaiting EMA" not in c)
        )
        
        bullish_reasons = []
        bearish_reasons = []
        
        # Final Confluence Decision
        if is_true_bullish:
            bias = "STRONG_BULLISH"
            bias_km = "🟢 សញ្ញា BUY: EMA 20 > EMA 50 (តម្លៃប៉ះ EMA 20/50 ➔ ទិសដៅ EMA 200)"
            setup_action = "BUY / LONG"
            confluence_score = min(98, max(80, int(78 + (adx * 0.4))))
            conflict_note = "EMA 20 > EMA 50 + តម្លៃប៉ះ EMA 20/50 បង្កើតចំណុច Entry ឆ្ពោះទៅ EMA 200"
            bullish_reasons.append("Strategy Trigger: EMA 20 កាត់ឡើងលើ EMA 50 (Bullish Cross)")
            bullish_reasons.append(f"Entry Confirmation: តម្លៃបានទាញថយក្រោយមកប៉ះ EMA 20/50 ({ema_touch_label})")
            bullish_reasons.append(f"Destination Target: EMA 200 (${ema_regime['ema200']:,.2f}) ជាទិសដៅផ្សារ")
            bullish_reasons.append(f"ADX={adx:.1f} ({trend_grade}) + +DI > -DI (Trending Buy)")
            bullish_reasons.append("MACD Bullish Momentum (MACD > Signal Line)")
        elif is_true_bearish:
            bias = "STRONG_BEARISH"
            bias_km = "🔴 សញ្ញា SELL: EMA 20 < EMA 50 (តម្លៃប៉ះ EMA 20/50 ➔ ទិសដៅ EMA 200)"
            setup_action = "SELL / SHORT"
            confluence_score = min(98, max(80, int(78 + (adx * 0.4))))
            conflict_note = "EMA 20 < EMA 50 + តម្លៃប៉ះ EMA 20/50 បង្កើតចំណុច Entry ឆ្ពោះទៅ EMA 200"
            bearish_reasons.append("Strategy Trigger: EMA 20 កាត់ចុះក្រោម EMA 50 (Bearish Cross)")
            bearish_reasons.append(f"Entry Confirmation: តម្លៃបានងើបឡើងមកប៉ះ EMA 20/50 ({ema_touch_label})")
            bearish_reasons.append(f"Destination Target: EMA 200 (${ema_regime['ema200']:,.2f}) ជាទិសដៅផ្សារ")
            bearish_reasons.append(f"ADX={adx:.1f} ({trend_grade}) + -DI > +DI (Trending Sell)")
            bearish_reasons.append("MACD Bearish Momentum (MACD < Signal Line)")
        else:
            bias = "NEUTRAL"
            bias_km = "⚪ រង់ចាំសូចនាករស្របគ្នា (Awaiting Confluence)"
            setup_action = "WAIT / NO TRADE"
            confluence_score = 45
            conflict_note = conflicts[0] if conflicts else "Oscillators Mixed / Neutral (No Trade Zone)"
            bearish_reasons.append(f"⚠️ {conflict_note}")
            bullish_reasons.append(f"⚠️ {conflict_note}")
            
        # 2. Precision Scalping Execution Plan
        plan = self._calculate_real_execution_plan(symbol, timeframe, setup_action, current_price, df, atr, ema_regime)
        plan["conflict_note"] = conflict_note
        
        # 3. Commentary
        khmer_report = self._generate_khmer_report(symbol, timeframe, bias_km, confluence_score, plan, bullish_reasons, bearish_reasons, ema_regime, smc_data)
        english_report = self._generate_english_report(symbol, timeframe, bias, confluence_score, plan, bullish_reasons, bearish_reasons, ema_regime, smc_data)
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "bias": bias,
            "bias_km": bias_km,
            "confluence_score": confluence_score,
            "setup_action": setup_action,
            "conflict_note": conflict_note,
            "plan": plan,
            "bullish_reasons": bullish_reasons,
            "bearish_reasons": bearish_reasons,
            "report_km": khmer_report,
            "report_en": english_report
        }

    def _calculate_real_execution_plan(self, symbol: str, timeframe: str, action: str, current_price: float, df, atr: float, ema_regime: dict) -> dict:
        """
        Calculates actionable Entry, Stop Loss, and Take Profit.
        Strategy Rule:
        - Entry: Dynamic Pullback touching EMA 20 or EMA 50.
        - Target (TP): EMA 200 is the primary market destination (ទិសដៅផ្សារ)!
        - Stop Loss: Invalidation beyond EMA 50.
        """
        is_scalping = (timeframe == "15m")
        recent = df.tail(4) if is_scalping else df.tail(10)
        recent_high = float(recent['High'].max())
        recent_low = float(recent['Low'].min())
        
        ema200 = float(ema_regime.get("ema200", current_price))
        ema50 = float(ema_regime.get("ema50", current_price))
        ema20 = float(ema_regime.get("ema20", current_price))
        
        # Entry is ALWAYS strictly the exact real-time live market price from TradingView
        entry = round(current_price, 2)
        
        if "SELL" in action or "BEARISH" in action:
            if symbol == "XAUUSD":
                sl_buf = 1.0 if is_scalping else 3.0
                min_risk = 3.5 if is_scalping else 12.0
                sl = round(max(recent_high + sl_buf, ema50 + sl_buf, current_price + min_risk), 2)
            else:
                sl_buf = 80.0 if is_scalping else 300.0
                min_risk = 250.0 if is_scalping else 1200.0
                sl = round(max(recent_high + sl_buf, ema50 + sl_buf, current_price + min_risk), 2)
            
            risk = round(sl - entry, 2)
            if risk <= 0:
                risk = 3.5 if symbol == "XAUUSD" else 250.0
                sl = round(entry + risk, 2)
                
            # EMA 200 is the market target (ទិសដៅផ្សារ)!
            if entry > ema200:
                dist_to_ema200 = entry - ema200
                if dist_to_ema200 >= risk:
                    tp1 = round(entry - (dist_to_ema200 * 0.5), 2)
                    tp2 = round(ema200, 2)  # Exact EMA 200 Destination!
                    tp3 = round(ema200 - (dist_to_ema200 * 0.5), 2)
                else:
                    tp1 = round(entry - (risk * 1.5), 2)
                    tp2 = round(ema200, 2)
                    tp3 = round(entry - (risk * 3.5), 2)
            else:
                tp1 = round(entry - (risk * 1.5), 2)
                tp2 = round(entry - (risk * 2.5), 2)
                tp3 = round(entry - (risk * 4.0), 2)

            rrr = round(abs(entry - tp2) / risk, 2) if risk > 0 else 2.5
            return {
                "current_live_price": entry,
                "entry": entry,
                "sl": sl,
                "tp1": tp1,
                "tp2": tp2,
                "tp3": tp3,
                "risk_pips_points": risk,
                "rrr": f"1:{rrr}",
                "target_type": "EMA 200 Destination" if entry > ema200 else "Standard Trend Run"
            }
            
        elif "BUY" in action or "BULLISH" in action:
            if symbol == "XAUUSD":
                sl_buf = 1.0 if is_scalping else 3.0
                min_risk = 3.5 if is_scalping else 12.0
                sl = round(min(recent_low - sl_buf, ema50 - sl_buf, current_price - min_risk), 2)
            else:
                sl_buf = 80.0 if is_scalping else 300.0
                min_risk = 250.0 if is_scalping else 1200.0
                sl = round(min(recent_low - sl_buf, ema50 - sl_buf, current_price - min_risk), 2)
            
            risk = round(entry - sl, 2)
            if risk <= 0:
                risk = 3.5 if symbol == "XAUUSD" else 250.0
                sl = round(entry - risk, 2)
                
            # EMA 200 is the market target (ទិសដៅផ្សារ)!
            if entry < ema200:
                dist_to_ema200 = ema200 - entry
                if dist_to_ema200 >= risk:
                    tp1 = round(entry + (dist_to_ema200 * 0.5), 2)
                    tp2 = round(ema200, 2)  # Exact EMA 200 Destination!
                    tp3 = round(ema200 + (dist_to_ema200 * 0.5), 2)
                else:
                    tp1 = round(entry + (risk * 1.5), 2)
                    tp2 = round(ema200, 2)
                    tp3 = round(entry + (risk * 3.5), 2)
            else:
                tp1 = round(entry + (risk * 1.5), 2)
                tp2 = round(entry + (risk * 2.5), 2)
                tp3 = round(entry + (risk * 4.0), 2)

            rrr = round(abs(tp2 - entry) / risk, 2) if risk > 0 else 2.5
            return {
                "current_live_price": entry,
                "entry": entry,
                "sl": sl,
                "tp1": tp1,
                "tp2": tp2,
                "tp3": tp3,
                "risk_pips_points": risk,
                "rrr": f"1:{rrr}",
                "target_type": "EMA 200 Destination" if entry < ema200 else "Standard Trend Run"
            }
            
        else:
            # Neutral / Wait - Standby mode (No trade until multi-oscillators align)
            return {
                "current_live_price": entry,
                "entry": entry,
                "sl": 0.0,
                "tp1": 0.0,
                "tp2": 0.0,
                "tp3": 0.0,
                "risk_pips_points": 0.0,
                "rrr": "Standby"
            }

    def _generate_khmer_report(self, sym, tf, bias_km, score, plan, bulls, bears, ema, smc) -> str:
        dr = smc.get("dealing_range", {})
        kz = smc.get("killzone", {})
        
        md = f"""### 📊 របាយការណ៍វិភាគបច្ចេកទេសស្ថាប័ន (Institutional Analysis)
* **ឧបករណ៍ជួញដូរ:** `{sym}` | **Timeframe:** `{tf}`
* **តម្លៃបច្ចុប្បន្នលើ TradingView:** **`${plan.get('current_live_price')}`**
* **និន្នាការចម្បង (Bias):** **{bias_km}**
* **ពិន្ទុភាពជឿជាក់ (Confluence Score):** **{score}/100**

---

#### 🎯 ផែនការប្រតិបត្តិការជួញដូរជាក់ស្តែង (Real Live Execution Roadmap)
* **តម្លៃចូលជាក់ស្តែង (Live Entry):** `{plan['entry']}` (ចូលនៅតម្លៃទីផ្សារបច្ចុប្បន្ន ឬរង់ចាំ Pullback ប្រកៀក)
* **កម្រិតខាតបង់រចនាសម្ព័ន្ធ (Tight SL):** `{plan['sl']}` (កំណត់លើ/ក្រោមកំពូលទៀន 15m ចុងក្រោយ)
* **ទិសដៅចំណេញទី១ (TP1):** `{plan['tp1']}`
* **ទិសដៅចំណេញទី២ (TP2 - Target):** `{plan['tp2']}`
* **ទិសដៅចំណេញទី៣ (TP3):** `{plan['tp3']}`
* **សមាមាត្រហានិភ័យ/ផលចំណេញ (Risk:Reward):** `{plan['rrr']}` (ចំណុចហានិភ័យ {plan['risk_pips_points']} pts)

---

#### 🧠 សូចនាករបច្ចេកទេសជាក់ស្តែង (Live Telemetry):
* **ADX (14):** `{ema.get('adx')}` ➔ {ema.get('adx_strength')}
* **MACD (12, 26, 9):** {ema.get('macd_status')}
* **RSI (14):** `{ema.get('rsi')}` ➔ {ema.get('rsi_status')}
* **EMA 20/50/200:** 20:`{ema.get('ema20')}` | 50:`{ema.get('ema50')}` | 200:`{ema.get('ema200')}`
"""
        return md

    def _generate_english_report(self, sym, tf, bias, score, plan, bulls, bears, ema, smc) -> str:
        md = f"""### 📊 Live Market Execution Memo
* **Asset:** `{sym}` | **Timeframe:** `{tf}`
* **Current Live Price:** **`${plan.get('current_live_price')}`**
* **Bias:** **{bias}** | **Score:** **{score}/100**
* **Live Entry:** `{plan['entry']}` | **SL:** `{plan['sl']}` | **TP:** `{plan['tp2']}` (RRR {plan['rrr']})
"""
        return md
