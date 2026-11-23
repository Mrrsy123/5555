"""
Local AI Analyst & Institutional Smart Money (SMC / ICT) Reasoning Engine.
Synthesizes:
1. Smart Money Concepts (SMC): Break of Structure (BOS), Change of Character (MSS),
   Order Blocks (OB), Fair Value Gaps (FVG), Liquidity Sweeps (Turtle Soup), Dealing Range (Premium/Discount).
2. Dynamic Trend Confluence: EMA 20, 50, 200 alignment and dynamic retests.
3. Multi-Oscillator Audit: ADX (Trend Strength), MACD (Momentum), RSI (Value Reload Zone).
4. High-Precision Institutional Execution: Tight Structural Invalidation (SL), 1:3 to 1:5 R:R Targets.
"""

import requests
import json

class LocalAIAnalyst:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url

    def analyze(self, symbol: str, timeframe: str, df, ema_regime: dict, smc_data: dict, htf_context: dict = None) -> dict:
        current_price = float(ema_regime["close"])
        atr = float(ema_regime.get("atr", current_price * 0.003))
        
        # 1. Multi-Oscillator Telemetry
        is_bullish_stack = ema_regime.get("is_bullish_stack", False)
        is_bearish_stack = ema_regime.get("is_bearish_stack", False)
        ema20 = float(ema_regime.get("ema20", current_price))
        ema50 = float(ema_regime.get("ema50", current_price))
        ema200 = float(ema_regime.get("ema200", current_price))
        
        ema20_above_ema50 = ema_regime.get("ema20_above_ema50", (ema20 > ema50))
        ema20_below_ema50 = ema_regime.get("ema20_below_ema50", (ema20 < ema50))
        touches_ema_entry = ema_regime.get("touches_ema_entry_zone", False)
        ema_touch_label = ema_regime.get("ema_touch_label", "")
        
        adx = float(ema_regime.get("adx", 20.0))
        plus_di = float(ema_regime.get("plus_di", 20.0))
        minus_di = float(ema_regime.get("minus_di", 20.0))
        trend_grade = ema_regime.get("trend_grade", "NORMAL")
        
        macd = float(ema_regime.get("macd", 0.0))
        macd_signal = float(ema_regime.get("macd_signal", 0.0))
        macd_hist = float(ema_regime.get("macd_hist", 0.0))
        macd_bull_cross = bool(ema_regime.get("macd_bullish_cross", False))
        macd_bear_cross = bool(ema_regime.get("macd_bearish_cross", False))
        
        rsi = float(ema_regime.get("rsi", 50.0))
        
        # 2. Institutional SMC Telemetry
        dr = smc_data.get("dealing_range", {})
        dr_pct = float(dr.get("relative_position_pct", 50.0))
        dr_zone = dr.get("zone", "EQUILIBRIUM")
        
        structure_events = smc_data.get("structure_events", [])
        recent_events = structure_events[-4:] if structure_events else []
        has_bullish_bos = any("BULLISH" in e.get("type", "") for e in recent_events)
        has_bearish_bos = any("BEARISH" in e.get("type", "") for e in recent_events)
        
        sweeps = smc_data.get("sweeps", [])
        has_ssl_sweep = any("SSL_SWEEP" in s.get("type", "") for s in sweeps)
        has_bsl_sweep = any("BSL_SWEEP" in s.get("type", "") for s in sweeps)
        
        obs = [ob for ob in smc_data.get("order_blocks", []) if ob.get("active", False)]
        fvgs = [f for f in smc_data.get("fvgs", []) if f.get("active", False)]
        
        # Check active institutional POI reaction
        in_bullish_poi = False
        poi_label_buy = ""
        for ob in obs:
            if ob.get("type") == "BULLISH_OB" and (ob.get("bottom") * 0.998 <= current_price <= ob.get("top") * 1.002):
                in_bullish_poi = True
                poi_label_buy = f"Unmitigated Bullish Order Block (${ob.get('bottom'):,.2f} - ${ob.get('top'):,.2f})"
                break
        if not in_bullish_poi:
            for fvg in fvgs:
                if fvg.get("type") == "BULLISH_FVG" and (fvg.get("bottom") * 0.998 <= current_price <= fvg.get("top") * 1.002):
                    in_bullish_poi = True
                    poi_label_buy = f"Bullish Fair Value Gap (${fvg.get('bottom'):,.2f} - ${fvg.get('top'):,.2f})"
                    break
        if not in_bullish_poi and has_ssl_sweep:
            in_bullish_poi = True
            poi_label_buy = "SSL Liquidity Sweep (Turtle Soup Bear Trap)"

        in_bearish_poi = False
        poi_label_sell = ""
        for ob in obs:
            if ob.get("type") == "BEARISH_OB" and (ob.get("bottom") * 0.998 <= current_price <= ob.get("top") * 1.002):
                in_bearish_poi = True
                poi_label_sell = f"Unmitigated Bearish Order Block (${ob.get('bottom'):,.2f} - ${ob.get('top'):,.2f})"
                break
        if not in_bearish_poi:
            for fvg in fvgs:
                if fvg.get("type") == "BEARISH_FVG" and (fvg.get("bottom") * 0.998 <= current_price <= fvg.get("top") * 1.002):
                    in_bearish_poi = True
                    poi_label_sell = f"Bearish Fair Value Gap (${fvg.get('bottom'):,.2f} - ${fvg.get('top'):,.2f})"
                    break
        if not in_bearish_poi and has_bsl_sweep:
            in_bearish_poi = True
            poi_label_sell = "BSL Liquidity Sweep (Turtle Soup Bull Trap)"

        # 3. Institutional Conflict & Veto Engine (Filtering out Low-Quality / Trap Signals)
        conflicts = []
        
        # Veto A: Dealing Range Pricing Rule (Never buy in Deep Premium / Never sell in Deep Discount)
        if dr_pct > 66.0:
            conflicts.append(f"Dealing Range: តម្លៃស្ថិតក្នុង Deep Premium ({dr_pct:.1f}%) ថ្លៃពេក (ហាម BUY ព្រោះប្រឈម Smart Money Dump / Retail Trap)")
        if dr_pct < 34.0:
            conflicts.append(f"Dealing Range: តម្លៃស្ថិតក្នុង Deep Discount ({dr_pct:.1f}%) ថោកពេក (ហាម SELL ព្រោះប្រឈម Smart Money Accumulation Bounce)")
            
        # Veto B: ADX Trend Strength Filter (No choppy low-volume sideways markets)
        if adx < 20.0:
            conflicts.append(f"ADX={adx:.1f} < 20 (ទីផ្សារ Sideways គ្មានកម្លាំង Trend ច្បាស់លាស់)")
            
        # Veto C: Momentum vs Trend Conflict
        if (macd_bull_cross or (macd > macd_signal and macd_hist > 0)) and ema20_below_ema50:
            conflicts.append("MACD Bullish Momentum ផ្ទុយនឹង EMA Bearish Trend (20 < 50)")
        if (macd_bear_cross or (macd < macd_signal and macd_hist < 0)) and ema20_above_ema50:
            conflicts.append("MACD Bearish Momentum ផ្ទុយនឹង EMA Bullish Trend (20 > 50)")
            
        # Veto D: Directional Index Conflict
        if plus_di > minus_di and (macd < macd_signal and macd_hist < 0):
            conflicts.append("+DI កម្លាំងទិញ ផ្ទុយនឹង MACD Momentum អវិជ្ជមាន")
        if minus_di > plus_di and (macd > macd_signal and macd_hist > 0):
            conflicts.append("-DI កម្លាំងលក់ ផ្ទុយនឹង MACD Momentum វិជ្ជមាន")
            
        # Veto E: RSI Extremes (Anti-Climax / Anti-Exhaustion)
        if rsi >= 68.0:
            conflicts.append(f"RSI={rsi:.1f} Overbought ខ្ពស់ពេក (ប្រឈមនឹងការទាញទម្លាក់ - ហាម BUY)")
        if rsi <= 32.0:
            conflicts.append(f"RSI={rsi:.1f} Oversold ជ្រៅពេក (ប្រឈមនឹងការងើបឡើងវិញ - ហាម SELL)")

        # Veto F: EMA Retest Confirmation
        if ema20_above_ema50 and not (touches_ema_entry or in_bullish_poi):
            conflicts.append("រង់ចាំតម្លៃទាញថយក្រោយមកប៉ះ EMA 20/50 ឬ Bullish POI (Awaiting Pullback)")
        if ema20_below_ema50 and not (touches_ema_entry or in_bearish_poi):
            conflicts.append("រង់ចាំតម្លៃងើបឡើងមកប៉ះ EMA 20/50 ឬ Bearish POI (Awaiting Pullback)")

        # Veto G: Higher Timeframe (HTF) Alignment (Strictly Prevents Scalp fighting the Swing Trend)
        if htf_context and timeframe == "15m":
            htf_bias = htf_context.get("bias", "NEUTRAL")
            htf_pct = float(htf_context.get("dr_pct", 50.0))
            if ema20_above_ema50:
                if "BEARISH" in htf_bias:
                    conflicts.append("HTF Macro Veto: Timeframe ធំ (1H) កំពុងស្ថិតក្នុង Bearish Trend - ហាម Scalp BUY បញ្ច្រាសរលកធំ!")
                if htf_pct > 65.0:
                    conflicts.append(f"HTF Macro Veto: Timeframe ធំ (1H) ស្ថិតក្នុង Deep Premium ({htf_pct:.1f}%) - ហាម Scalp BUY!")
            if ema20_below_ema50:
                if "BULLISH" in htf_bias:
                    conflicts.append("HTF Macro Veto: Timeframe ធំ (1H) កំពុងស្ថិតក្នុង Bullish Trend - ហាម Scalp SELL បញ្ច្រាសរលកធំ!")
                if htf_pct < 35.0:
                    conflicts.append(f"HTF Macro Veto: Timeframe ធំ (1H) ស្ថិតក្នុង Deep Discount ({htf_pct:.1f}%) - ហាម Scalp SELL!")

        # 4. Smart Money Institutional Confluence Evaluation
        # A True Grade A+ BUY requires:
        # 1. EMA 20 > EMA 50
        # 2. Price in Discount or Equilibrium (dr_pct <= 66%)
        # 3. Pullback to EMA 20/50 OR reacting at Bullish POI (OB/FVG/SSL Sweep)
        # 4. ADX >= 20 & +DI > -DI & MACD Bullish
        # 5. RSI in healthy reload zone (38 <= RSI <= 66)
        is_true_bullish = (
            ema20_above_ema50 and
            (dr_pct <= 66.0) and
            (touches_ema_entry or in_bullish_poi) and
            (adx >= 20.0 and plus_di > minus_di) and
            (macd > macd_signal and (macd_hist > 0 or macd_bull_cross)) and
            (38.0 <= rsi <= 66.0) and
            not any("Deep Premium" in c or "Bearish" in c or "Overbought" in c or "HTF Macro Veto" in c for c in conflicts if "Awaiting" not in c)
        )

        # A True Grade A+ SELL requires:
        # 1. EMA 20 < EMA 50
        # 2. Price in Premium or Equilibrium (dr_pct >= 34%)
        # 3. Pullback to EMA 20/50 OR reacting at Bearish POI (OB/FVG/BSL Sweep)
        # 4. ADX >= 20 & -DI > +DI & MACD Bearish
        # 5. RSI in healthy reload zone (34 <= RSI <= 62)
        is_true_bearish = (
            ema20_below_ema50 and
            (dr_pct >= 34.0) and
            (touches_ema_entry or in_bearish_poi) and
            (adx >= 20.0 and minus_di > plus_di) and
            (macd < macd_signal and (macd_hist < 0 or macd_bear_cross)) and
            (34.0 <= rsi <= 62.0) and
            not any("Deep Discount" in c or "Bullish" in c or "Oversold" in c or "HTF Macro Veto" in c for c in conflicts if "Awaiting" not in c)
        )

        bullish_reasons = []
        bearish_reasons = []

        if is_true_bullish:
            bias = "STRONG_BULLISH"
            bias_km = "🟢 សញ្ញា BUY: Smart Money Confluence + EMA 20/50 Reload (ទិសដៅ EMA 200)"
            setup_action = "BUY / LONG"
            
            # Dynamic Confluence Score Calculation
            score = 80
            if in_bullish_poi: score += 8
            if dr_pct <= 45.0: score += 5  # Discount bonus
            if has_bullish_bos: score += 4
            if adx >= 28.0: score += 3
            confluence_score = min(98, score)
            
            conflict_note = f"SMC Discount ({dr_pct:.1f}%) + EMA 20/50 Retest + Bullish Momentum"
            bullish_reasons.append("Trend Alignment: EMA 20 > EMA 50 (Bullish Institutional Bias)")
            bullish_reasons.append(f"Institutional Pricing: តម្លៃក្នុងតំបន់ {dr_zone} ({dr_pct:.1f}%) - អំណោយផលដល់ការទិញថោក (Discount)")
            if in_bullish_poi:
                bullish_reasons.append(f"Institutional POI: មានវត្តមាន {poi_label_buy}")
            bullish_reasons.append(f"Entry Confirmation: តម្លៃទាញថយក្រោយមកប៉ះ {ema_touch_label}")
            if current_price < ema200:
                bullish_reasons.append(f"Destination Target: EMA 200 (${ema200:,.2f}) ជាទិសដៅផ្សារចម្បង")
            else:
                bullish_reasons.append(f"Trend Expansion: តម្លៃនៅលើ EMA 200 (${ema200:,.2f}) កំពុងរត់តាមនិន្នាការឡើង")
            bullish_reasons.append(f"ADX={adx:.1f} ({trend_grade}) + MACD Bullish Momentum")
            
        elif is_true_bearish:
            bias = "STRONG_BEARISH"
            bias_km = "🔴 សញ្ញា SELL: Smart Money Confluence + EMA 20/50 Reload (ទិសដៅ EMA 200)"
            setup_action = "SELL / SHORT"
            
            score = 80
            if in_bearish_poi: score += 8
            if dr_pct >= 55.0: score += 5  # Premium bonus
            if has_bearish_bos: score += 4
            if adx >= 28.0: score += 3
            confluence_score = min(98, score)
            
            conflict_note = f"SMC Premium ({dr_pct:.1f}%) + EMA 20/50 Retest + Bearish Momentum"
            bearish_reasons.append("Trend Alignment: EMA 20 < EMA 50 (Bearish Institutional Bias)")
            bearish_reasons.append(f"Institutional Pricing: តម្លៃក្នុងតំបន់ {dr_zone} ({dr_pct:.1f}%) - អំណោយផលដល់ការលក់ថ្លៃ (Premium)")
            if in_bearish_poi:
                bearish_reasons.append(f"Institutional POI: មានវត្តមាន {poi_label_sell}")
            bearish_reasons.append(f"Entry Confirmation: តម្លៃងើបឡើងមកប៉ះ {ema_touch_label}")
            if current_price > ema200:
                bearish_reasons.append(f"Destination Target: EMA 200 (${ema200:,.2f}) ជាទិសដៅផ្សារចម្បង")
            else:
                bearish_reasons.append(f"Trend Expansion: តម្លៃនៅក្រោម EMA 200 (${ema200:,.2f}) កំពុងរត់តាមនិន្នាការធ្លាក់")
            bearish_reasons.append(f"ADX={adx:.1f} ({trend_grade}) + MACD Bearish Momentum")
            
        else:
            bias = "NEUTRAL"
            bias_km = "⚪ រង់ចាំ Smart Money Confluence (Awaiting Clean Setup)"
            setup_action = "WAIT / NO TRADE"
            confluence_score = 45
            conflict_note = conflicts[0] if conflicts else "Oscillators Mixed / Dealing Range Neutral (No Trade Zone)"
            bearish_reasons.append(f"⚠️ {conflict_note}")
            bullish_reasons.append(f"⚠️ {conflict_note}")

        # 5. Precision Institutional Execution Plan (Tight SL, 1:3 to 1:5 R:R)
        plan = self._calculate_real_execution_plan(symbol, timeframe, setup_action, current_price, df, atr, ema_regime, smc_data)
        plan["conflict_note"] = conflict_note
        plan["in_poi"] = in_bullish_poi if "BUY" in setup_action else (in_bearish_poi if "SELL" in setup_action else False)
        plan["poi_label"] = poi_label_buy if "BUY" in setup_action else poi_label_sell
        plan["dealing_range_pct"] = dr_pct
        plan["dealing_range_zone"] = dr_zone
        
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

    def _calculate_real_execution_plan(self, symbol: str, timeframe: str, action: str, current_price: float, df, atr: float, ema_regime: dict, smc_data: dict) -> dict:
        """
        Calculates Institutional-Grade Execution:
        - Entry: Live market price.
        - Stop Loss: Tight structural invalidation behind Order Block, FVG, or recent pullback swing low/high.
        - Take Profits:
          - TP1: 1:2.0 R:R (Lock in 70% partial & Move SL to Entry for 100% Risk-Free trade).
          - TP2: EMA 200 Destination OR 1:3.5 R:R (Main institutional target).
          - TP3: 1:5.0 R:R (Runner extension).
        """
        is_scalping = (timeframe == "15m")
        recent = df.tail(5) if is_scalping else df.tail(10)
        recent_high = float(recent['High'].max())
        recent_low = float(recent['Low'].min())
        
        ema200 = float(ema_regime.get("ema200", current_price))
        ema50 = float(ema_regime.get("ema50", current_price))
        entry = round(current_price, 2)
        
        if "SELL" in action or "BEARISH" in action:
            # Structural Invalidation for SELL
            if symbol == "XAUUSD":
                risk_buf = 1.0 if is_scalping else 2.5
                structural_high = max(recent_high, ema50) if abs(current_price - ema50) < 8.0 else recent_high
                sl = round(structural_high + risk_buf, 2)
                risk = round(sl - entry, 2)
                # Institutional risk bounds for Gold: $2.50 - $5.50 for 15M; $5.00 - $10.00 for 1H
                min_risk = 2.5 if is_scalping else 5.0
                max_risk = 5.5 if is_scalping else 10.0
                if risk < min_risk:
                    risk = min_risk
                    sl = round(entry + risk, 2)
                elif risk > max_risk:
                    risk = max_risk
                    sl = round(entry + risk, 2)
            else:
                # BTCUSD
                risk_buf = 60.0 if is_scalping else 150.0
                structural_high = max(recent_high, ema50) if abs(current_price - ema50) < 600.0 else recent_high
                sl = round(structural_high + risk_buf, 2)
                risk = round(sl - entry, 2)
                # Institutional risk bounds for BTC: $180 - $350 for 15M; $350 - $700 for 1H
                min_risk = 180.0 if is_scalping else 350.0
                max_risk = 350.0 if is_scalping else 700.0
                if risk < min_risk:
                    risk = min_risk
                    sl = round(entry + risk, 2)
                elif risk > max_risk:
                    risk = max_risk
                    sl = round(entry + risk, 2)

            tp1 = round(entry - (risk * 2.0), 2)
            # EMA 200 Destination Check
            if entry > ema200 and (entry - ema200) >= (risk * 2.5):
                tp2 = round(ema200, 2)
                target_type = "🎯 EMA 200 Destination Target"
            else:
                tp2 = round(entry - (risk * 3.5), 2)
                target_type = "🎯 Institutional 1:3.5 Target"
            tp3 = round(entry - (risk * 5.0), 2)
            rrr = round(abs(entry - tp2) / risk, 2) if risk > 0 else 3.5

            return {
                "current_live_price": entry,
                "entry": entry,
                "sl": sl,
                "tp1": tp1,
                "tp2": tp2,
                "tp3": tp3,
                "risk_pips_points": risk,
                "rrr": f"1:{rrr}",
                "target_type": target_type
            }

        elif "BUY" in action or "BULLISH" in action:
            # Structural Invalidation for BUY
            if symbol == "XAUUSD":
                risk_buf = 1.0 if is_scalping else 2.5
                structural_low = min(recent_low, ema50) if abs(current_price - ema50) < 8.0 else recent_low
                sl = round(structural_low - risk_buf, 2)
                risk = round(entry - sl, 2)
                min_risk = 2.5 if is_scalping else 5.0
                max_risk = 5.5 if is_scalping else 10.0
                if risk < min_risk:
                    risk = min_risk
                    sl = round(entry - risk, 2)
                elif risk > max_risk:
                    risk = max_risk
                    sl = round(entry - risk, 2)
            else:
                # BTCUSD
                risk_buf = 60.0 if is_scalping else 150.0
                structural_low = min(recent_low, ema50) if abs(current_price - ema50) < 600.0 else recent_low
                sl = round(structural_low - risk_buf, 2)
                risk = round(entry - sl, 2)
                min_risk = 180.0 if is_scalping else 350.0
                max_risk = 350.0 if is_scalping else 700.0
                if risk < min_risk:
                    risk = min_risk
                    sl = round(entry - risk, 2)
                elif risk > max_risk:
                    risk = max_risk
                    sl = round(entry - risk, 2)

            tp1 = round(entry + (risk * 2.0), 2)
            if entry < ema200 and (ema200 - entry) >= (risk * 2.5):
                tp2 = round(ema200, 2)
                target_type = "🎯 EMA 200 Destination Target"
            else:
                tp2 = round(entry + (risk * 3.5), 2)
                target_type = "🎯 Institutional 1:3.5 Target"
            tp3 = round(entry + (risk * 5.0), 2)
            rrr = round(abs(tp2 - entry) / risk, 2) if risk > 0 else 3.5

            return {
                "current_live_price": entry,
                "entry": entry,
                "sl": sl,
                "tp1": tp1,
                "tp2": tp2,
                "tp3": tp3,
                "risk_pips_points": risk,
                "rrr": f"1:{rrr}",
                "target_type": target_type
            }

        else:
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
        
        md = f"""### 📊 របាយការណ៍វិភាគបច្ចេកទេសស្ថាប័ន (Smart Money & Confluence Analysis)
* **ឧបករណ៍ជួញដូរ:** `{sym}` | **Timeframe:** `{tf}`
* **តម្លៃបច្ចុប្បន្នលើ TradingView:** **`${plan.get('current_live_price')}`**
* **និន្នាការស្ថាប័ន (Institutional Bias):** **{bias_km}**
* **ពិន្ទុភាពជឿជាក់ (Confluence Score):** **{score}/100**
* **Dealing Range:** តំបន់ **{dr.get('zone', 'N/A')}** ({dr.get('relative_position_pct', 0)}%)
* **ICT Killzone:** {kz.get('name', 'Standard Flow')}

---

#### 🎯 ផែនការប្រតិបត្តិការជួញដូរស្ថាប័ន (Smart Execution Roadmap)
* **ចំណុចចូល (Live Entry):** `{plan['entry']}` (Dynamic Pullback & POI Confirmation)
* **កម្រិតខាតបង់រចនាសម្ព័ន្ធ (Tight Structural SL):** `{plan['sl']}` (ហានិភ័យត្រឹមតែ {plan['risk_pips_points']} pts)
* **ទិសដៅចំណេញទី១ (TP1 - 1:2.0 R:R):** `{plan['tp1']}` (ដកចំណេញ ៧០% & រំកិល SL ទៅ Entry ធានា Risk-Free)
* **ទិសដៅចំណេញទី២ (TP2 - 1:3.5 R:R):** `{plan['tp2']}` ({plan.get('target_type', 'Main Target')})
* **ទិសដៅចំណេញទី៣ (TP3 - 1:5.0 R:R):** `{plan['tp3']}` (Runner Extension)
* **សមាមាត្រហានិភ័យ/ផលចំណេញ (Risk:Reward):** **{plan['rrr']}**

---

#### 🧠 សូចនាករស្ថាប័នរួមផ្សំ (Institutional Telemetry):
* **ADX (14):** `{ema.get('adx')}` ➔ {ema.get('adx_strength')}
* **MACD (12, 26, 9):** {ema.get('macd_status')}
* **RSI (14):** `{ema.get('rsi')}` ➔ {ema.get('rsi_status')}
* **EMA 20/50/200:** 20:`{ema.get('ema20')}` | 50:`{ema.get('ema50')}` | 200:`{ema.get('ema200')}`
"""
        return md

    def _generate_english_report(self, sym, tf, bias, score, plan, bulls, bears, ema, smc) -> str:
        md = f"""### 📊 Institutional Smart Money Memo
* **Asset:** `{sym}` | **Timeframe:** `{tf}`
* **Current Live Price:** **`${plan.get('current_live_price')}`**
* **Bias:** **{bias}** | **Score:** **{score}/100**
* **Live Entry:** `{plan['entry']}` | **Tight SL:** `{plan['sl']}` | **TP2:** `{plan['tp2']}` (RRR {plan['rrr']})
"""
        return md
