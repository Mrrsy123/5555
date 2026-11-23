"""
Pheara Pro Trader AI Terminal
Professional Local Trading Analysis System for FXCM:XAUUSD & BITSTAMP:BTCUSD
Featuring:
- Institutional Live Trading Desk Signal Cards (Matching Pro UI)
- Official TradingView Real-Time Chart Embed
- Multi-EMA Stack (20, 50, 200)
- ADX (14) Trend Strength Meter
- MACD (12, 26, 9) Cross Radar
- RSI (14) Value Pullback Radar
- Algorithmic Smart Money Concepts (SMC) & ICT Engine
- Automated Telegram Bot Signal Dispatcher
"""

import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz
import importlib

import core.indicators as indicators_mod
importlib.reload(indicators_mod)

import core.ui_components as ui_mod
importlib.reload(ui_mod)

import core.ai_analyst as analyst_mod
importlib.reload(analyst_mod)

import core.data_fetcher as fetcher_mod
importlib.reload(fetcher_mod)

import core.tradingview_stream as stream_mod
importlib.reload(stream_mod)

import core.telegram_bot as bot_mod
importlib.reload(bot_mod)

import core.trade_tracker as tracker_mod
importlib.reload(tracker_mod)
from core.trade_tracker import monitor_trade_outcomes, load_trades, clear_closed_trades, clear_all_trades

from streamlit_autorefresh import st_autorefresh
from core.ui_components import generate_signal_card_html
from config import load_config, save_config
from core.data_fetcher import fetch_market_data
from core.tradingview_stream import get_tradingview_official_ta
from core.indicators import calculate_technical_indicators, analyze_indicator_telemetry
from core.ai_analyst import LocalAIAnalyst
from core.smc_engine import (
    find_swings,
    detect_fvgs,
    detect_market_structure,
    detect_order_blocks,
    calculate_dealing_range,
    detect_liquidity_sweeps,
    check_ict_killzone
)
from core.ai_analyst import LocalAIAnalyst
from core.telegram_bot import TelegramSignalBot
from core.ui_components import generate_signal_card_html

# Page configuration
st.set_page_config(
    page_title="Pheara Pro Trader AI - Institutional Desk Terminal",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Dark Institutional Feel
st.markdown("""
<style>
    .main {
        background-color: #0b0e14;
        color: #e2e8f0;
    }
    .metric-card {
        background: linear-gradient(135deg, #161b22, #0d1117);
        padding: 14px 18px;
        border-radius: 8px;
        border: 1px solid #30363d;
        margin-bottom: 10px;
    }
    .indicator-card {
        background: #111827;
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 4px solid #1f6feb;
        margin-bottom: 8px;
    }
    .plan-card {
        background: linear-gradient(135deg, #0d1f2d, #0d1117);
        border: 1px solid #1f6feb;
        padding: 16px 20px;
        border-radius: 8px;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    .feed-badge {
        display: inline-block;
        background: #238636;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .badge-cross-bull {
        display: inline-block;
        background: rgba(46, 204, 113, 0.2);
        color: #2ecc71;
        border: 1px solid #2ecc71;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .badge-cross-bear {
        display: inline-block;
        background: rgba(231, 76, 60, 0.2);
        color: #e74c3c;
        border: 1px solid #e74c3c;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .badge-adx-strong {
        display: inline-block;
        background: rgba(0, 210, 255, 0.2);
        color: #00d2ff;
        border: 1px solid #00d2ff;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .badge-adx-weak {
        display: inline-block;
        background: rgba(210, 153, 34, 0.2);
        color: #d29922;
        border: 1px solid #d29922;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Load System Config
app_cfg = load_config()
bot = TelegramSignalBot(app_cfg.get("telegram_bot_token"), app_cfg.get("telegram_chat_id"))

# Sidebar Controls
st.sidebar.image("https://img.icons8.com/fluency/96/bullish.png", width=64)
st.sidebar.title("🦅 PHEARA PRO TRADER")
st.sidebar.caption("TradingView Live • Telegram Bot Signal Auto-Drop")

# Asset & Timeframe Selection
asset = st.sidebar.selectbox("ឧបករណ៍ជួញដូរ (Asset):", ["BTCUSD", "XAUUSD"], index=0)
timeframe = st.sidebar.selectbox("ពេលវេលា (Timeframe):", ["15m", "1h", "4h", "1d"], index=0)

tv_symbol_code = "BITSTAMP:BTCUSD" if asset == "BTCUSD" else "FX:XAUUSD"
tv_display_name = "BITSTAMP:BTCUSD (Spot Bitcoin)" if asset == "BTCUSD" else "FXCM:XAUUSD (Spot Gold)"
tv_interval_code = {"15m": "15", "1h": "60", "4h": "240", "1d": "D"}.get(timeframe, "15")

st.sidebar.success(f"📡 Verified Feed: **{tv_display_name}**")

# Telegram Bot Status in Sidebar
if bot.is_configured():
    st.sidebar.markdown("🤖 Telegram Bot: **🟢 CONNECTED**")
else:
    st.sidebar.markdown("🤖 Telegram Bot: **🔴 NOT CONFIGURED**")

with st.sidebar.expander("⚙️ Telegram Bot Settings", expanded=not bot.is_configured()):
    sb_token = st.text_input("Bot Token (ពី @BotFather):", value=app_cfg.get("telegram_bot_token", ""), type="password", key="sb_token")
    sb_chat_id = st.text_input("Chat ID (ពី @userinfobot):", value=app_cfg.get("telegram_chat_id", ""), key="sb_chat")
    if st.button("💾 Save Telegram Credentials", key="sb_save_tg", use_container_width=True):
        app_cfg["telegram_bot_token"] = sb_token.strip()
        app_cfg["telegram_chat_id"] = sb_chat_id.strip()
        if save_config(app_cfg):
            st.success("✅ បានរក្សាទុកជោគជ័យ!")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("⚡ Telegram Auto-Pilot")
auto_drop_enabled = st.sidebar.toggle("🤖 Auto-Drop Signals ចូល Telegram", value=True, help="ស្កេន និងទម្លាក់ Signal ចូល Telegram ដោយស្វ័យប្រវត្តិតែម្តង")
if auto_drop_enabled:
    st.sidebar.caption("🟢 ម៉ាស៊ីនស្កេនស្វ័យប្រវត្តិ: ៦០ វិនាទីម្តង (Auto-Drop Active)")
    st_autorefresh(interval=60 * 1000, key="tg_auto_pilot_refresh")

st.sidebar.markdown("---")
chart_view_mode = st.sidebar.radio(
    "📊 ជម្រើសក្រាហ្វ (Chart View):",
    ["TradingView Official Live Chart (Full Interactive)", "Institutional Multi-Oscillator (EMA+MACD+RSI+ADX)", "Side-by-Side (ទាំងពីរ)"],
    index=0
)

st.sidebar.markdown("---")
killzone_info = check_ict_killzone()
st.sidebar.markdown(f"**🕒 ICT Session:** `{killzone_info['name']}`")
st.sidebar.markdown(f"**🌐 Local Time:** `{datetime.now().strftime('%H:%M:%S')} (UTC+7)`")

refresh_btn = st.sidebar.button("🔄 Refresh Data & Recalculate", use_container_width=True)

# Main Terminal Header
col_title, col_time = st.columns([3, 1])
with col_title:
    st.markdown('<div class="feed-badge">🔴 LIVE VERIFIED TRADINGVIEW ENGINE</div>', unsafe_allow_html=True)
    st.title(f"📈 {asset} ({tv_display_name})")
    st.caption("Complete institutional suite: Desk Signal Cards, EMA 20/50/200, ADX, MACD, RSI & Telegram Bot")

# Run Backend Calculation Pipeline for Primary Asset
analyst = LocalAIAnalyst()

with st.spinner(f"ទាញយក និងវិភាគទិន្នន័យពី TradingView សម្រាប់ {asset} ({timeframe})..."):
    try:
        raw_df = fetch_market_data(asset, timeframe)
    except Exception as e:
        st.error(f"Error fetching TradingView data: {str(e)}")
        raw_df = None
        st.stop()

if raw_df is None or raw_df.empty:
    st.warning("⚠️ មិនអាចទាញទិន្នន័យទីផ្សារបានទេ សូមរង់ចាំបន្តិច ឬ Refresh ទំព័រឡើងវិញ។")
    st.stop()

# Primary Indicator and SMC Calculations
df = calculate_technical_indicators(raw_df)
indicator_regime = analyze_indicator_telemetry(df)

# Monitor open trade lifecycle (Automated TP / SL Alerting)
try:
    tp_sl_events = monitor_trade_outcomes(asset, timeframe, raw_df.iloc[-1].to_dict(), bot)
    for ev in tp_sl_events:
        if "TP" in ev["type"]:
            st.toast(f"🎯 TAKE PROFIT {ev['type']} HIT សម្រាប់ {asset} ({ev['hit_price']:,.2f})! បានបាញ់ចូល Telegram រួចរាល់!", icon="💰")
        elif "SL" in ev["type"]:
            st.toast(f"🛑 STOP LOSS HIT សម្រាប់ {asset} ({ev['hit_price']:,.2f})! បានបាញ់ចូល Telegram រួចរាល់!", icon="🛡️")
except Exception as trk_err:
    pass

tv_ta = get_tradingview_official_ta(asset, timeframe)

swing_highs, swing_lows = find_swings(df, window=3)
fvgs = detect_fvgs(df)
market_events = detect_market_structure(df, swing_highs, swing_lows)
obs = detect_order_blocks(df)
dealing_range = calculate_dealing_range(swing_highs, swing_lows, indicator_regime["close"])
sweeps = detect_liquidity_sweeps(df, swing_highs, swing_lows)

smc_payload = {
    "swing_highs": swing_highs,
    "swing_lows": swing_lows,
    "fvgs": fvgs,
    "structure_events": market_events,
    "order_blocks": obs,
    "dealing_range": dealing_range,
    "sweeps": sweeps,
    "killzone": killzone_info
}

analysis_result = analyst.analyze(asset, timeframe, df, indicator_regime, smc_payload)
plan = analysis_result["plan"]

# -------------------------------------------------------------
# 🚨 SECTION: LIVE TRADING DESK SIGNAL CARDS (MATCHING PRO UI)
# -------------------------------------------------------------
st.markdown("### 🚨 ផ្ទាំងសញ្ញាជួញដូរស្ថាប័ន Live Desk Signals")
st.caption("សញ្ញាស្កេន Real-Time កម្រិតស្ថាប័ន សម្រាប់ XAUUSD និង BTCUSD ជាមួយនឹងចំណុច Entry, Target និង Stop Loss")

# Helper to compute secondary card data quickly
@st.cache_data(ttl=10)
def get_card_data(sym: str, tf: str):
    try:
        r_df = fetch_market_data(sym, tf, 100)
        c_df = calculate_technical_indicators(r_df)
        c_ind = analyze_indicator_telemetry(c_df)
        try:
            monitor_trade_outcomes(sym, tf, r_df.iloc[-1].to_dict(), bot)
        except Exception:
            pass
        c_sh, c_sl = find_swings(c_df, 3)
        c_fvgs = detect_fvgs(c_df)
        c_ev = detect_market_structure(c_df, c_sh, c_sl)
        c_obs = detect_order_blocks(c_df)
        c_dr = calculate_dealing_range(c_sh, c_sl, c_ind["close"])
        c_sw = detect_liquidity_sweeps(c_df, c_sh, c_sl)
        c_kz = check_ict_killzone()
        c_smc = {
            "swing_highs": c_sh, "swing_lows": c_sl, "fvgs": c_fvgs,
            "structure_events": c_ev, "order_blocks": c_obs,
            "dealing_range": c_dr, "sweeps": c_sw, "killzone": c_kz
        }
        c_ana = analyst.analyze(sym, tf, c_df, c_ind, c_smc)
        return c_ana, c_ind
    except Exception as err:
        print(f"[Error] get_card_data({sym}, {tf}): {err}")
        return None, None

# Compute for the 2 primary assets: BTCUSD 15m & XAUUSD 15m
card_cols = st.columns(2)

# Card 1: BTCUSD 15m Scalping
with card_cols[0]:
    if asset == "BTCUSD" and timeframe == "15m":
        btc_ana, btc_ind = analysis_result, indicator_regime
    else:
        btc_ana, btc_ind = get_card_data("BTCUSD", "15m")
    if btc_ana and btc_ind:
        st.markdown(generate_signal_card_html("BTCUSD", "15m", btc_ana, btc_ind, "LIVE ACTIVE"), unsafe_allow_html=True)
        if st.button("✈️ Drop BTCUSD to Telegram", key="drop_btc_btn", use_container_width=True):
            if bot.is_configured():
                res = bot.dispatch_trade_signal("BTCUSD", "15m", btc_ana, btc_ind)
                if res.get("status") == "SUCCESS":
                    st.success("🎉 សញ្ញា BTCUSD ត្រូវបានទម្លាក់ចូល Telegram Bot ជោគជ័យ!")
                elif res.get("status") == "BLOCKED":
                    st.warning(f"⚠️ {res.get('message')}")
                else:
                    st.error(f"❌ បរាជ័យ: {res.get('message')}")
            else:
                st.warning("⚠️ សូមបញ្ចូល Bot Token & Chat ID នៅ Sidebar ខាងឆ្វេងជាមុនសិន!")
    else:
        st.info("Loading BTCUSD Signal Card...")

# Card 2: XAUUSD 15m Scalping
with card_cols[1]:
    if asset == "XAUUSD" and timeframe == "15m":
        xau_ana, xau_ind = analysis_result, indicator_regime
    else:
        xau_ana, xau_ind = get_card_data("XAUUSD", "15m")
    if xau_ana and xau_ind:
        st.markdown(generate_signal_card_html("XAUUSD", "15m", xau_ana, xau_ind, "LIVE ACTIVE"), unsafe_allow_html=True)
        if st.button("✈️ Drop XAUUSD to Telegram", key="drop_xau_btn", use_container_width=True):
            if bot.is_configured():
                res = bot.dispatch_trade_signal("XAUUSD", "15m", xau_ana, xau_ind)
                if res.get("status") == "SUCCESS":
                    st.success("🎉 សញ្ញា XAUUSD ត្រូវបានទម្លាក់ចូល Telegram Bot ជោគជ័យ!")
                elif res.get("status") == "BLOCKED":
                    st.warning(f"⚠️ {res.get('message')}")
                else:
                    st.error(f"❌ បរាជ័យ: {res.get('message')}")
            else:
                st.warning("⚠️ សូមបញ្ចូល Bot Token & Chat ID នៅ Sidebar ខាងឆ្វេងជាមុនសិន!")
    else:
        st.info("Loading XAUUSD Signal Card...")

# -------------------------------------------------------------
# 🤖 AUTO-DISPATCH CONFLUENT SIGNALS DIRECTLY TO TELEGRAM
# -------------------------------------------------------------
if bot.is_configured() and auto_drop_enabled:
    auto_items = [
        ("BTCUSD", "15m", btc_ana, btc_ind),
        ("XAUUSD", "15m", xau_ana, xau_ind)
    ]
    for c_sym, c_tf, c_ana, c_ind in auto_items:
        if c_ana and c_ind:
            auto_res = bot.auto_dispatch_if_confluent(c_sym, c_tf, c_ana, c_ind)
            if auto_res.get("status") == "AUTO_DISPATCHED":
                st.toast(f"⚡ [AUTO-DROP] សញ្ញា {c_sym} {c_tf} ({auto_res.get('action')}) ត្រូវបានបាញ់ចូល Telegram ដោយជោគជ័យ!", icon="🚀")

st.markdown("---")

# -------------------------------------------------------------
# 📋 SECTION: LIVE TRADE LIFECYCLE & OUTCOME TRACKER
# -------------------------------------------------------------
with st.expander("📋 កំណត់ត្រាសញ្ញាជួញដូរ & ការតាមដានលទ្ធផល (Live Trade Lifecycle Tracker — TP/SL)", expanded=False):
    tracked_trades = load_trades()
    if tracked_trades:
        import pandas as pd
        rows = []
        for trk in reversed(tracked_trades[-15:]):
            st_badge = "🟢 RUNNING"
            outcome = trk.get("outcome", "RUNNING")
            if outcome == "BE_CLOSED":
                st_badge = "🛡️ BE CLOSED (+70% TP1)"
            elif trk.get("sl_hit") or outcome == "SL_HIT":
                st_badge = "🛑 SL HIT"
            elif trk.get("tp3_hit") or outcome == "TP3_FULL_HIT":
                st_badge = "🚀 TP3 HIT (+100%)"
            elif trk.get("tp2_hit"):
                st_badge = "🎯 TP2 HIT"
            elif trk.get("tp1_hit"):
                st_badge = "✅ TP1 HIT (+BE)"
                
            rows.append({
                "Asset": trk.get("asset"),
                "Timeframe": trk.get("timeframe"),
                "Action": trk.get("action"),
                "Entry": f"{trk.get('entry'):,.2f}",
                "TP1": f"{trk.get('tp1'):,.2f}",
                "TP2": f"{trk.get('tp2'):,.2f}",
                "TP3": f"{trk.get('tp3'):,.2f}",
                "Stop Loss": f"{trk.get('sl'):,.2f}",
                "Status": st_badge,
                "Time": trk.get("opened_at")
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
        
        c_tr1, c_tr2, _ = st.columns([1.5, 1.5, 5])
        with c_tr1:
            if st.button("🗑️ សម្អាត Closed Trades", key="clear_closed_btn"):
                c_del = clear_closed_trades()
                st.toast(f"បានសម្អាត {c_del} closed trades រួចរាល់!")
                st.rerun()
        with c_tr2:
            if st.button("🔄 Refresh Data", key="refresh_trades_btn"):
                st.rerun()
    else:
        st.caption("មិនទាន់មានសញ្ញាដែលកំពុងដំណើរការនៅឡើយទេ។ នៅពេលមាន Signal បាញ់ចូល Telegram វានឹងមកបង្ហាញនៅទីនេះដោយស្វ័យប្រវត្តិ។")

st.markdown("---")

# Row 1: Core Macro Metrics
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.caption("តម្លៃបច្ចុប្បន្នលើ TradingView (Live Spot)")
    price_format = f"${indicator_regime['close']:,.3f}" if asset == "XAUUSD" else f"${indicator_regime['close']:,.2f}"
    st.subheader(price_format)
    st.write(f"Vs EMA20: **{indicator_regime['price_vs_ema20']}**")
    st.markdown('</div>', unsafe_allow_html=True)

with m2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.caption("និន្នាការស្ថាប័ន (Pheara Institutional Bias)")
    st.markdown(f'<div style="font-weight:bold; font-size:1.15rem;">{analysis_result["bias_km"]}</div>', unsafe_allow_html=True)
    st.write(f"Action: **{analysis_result['setup_action']}**")
    st.markdown('</div>', unsafe_allow_html=True)

with m3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.caption("ពិន្ទុភាពជឿជាក់ (Confluence Score)")
    st.subheader(f"{analysis_result['confluence_score']} / 100")
    st.progress(analysis_result['confluence_score'] / 100)
    st.markdown('</div>', unsafe_allow_html=True)

with m4:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.caption("TradingView Official Technical Rating")
    if tv_ta.get("status") == "SUCCESS":
        tv_rec = tv_ta["summary"].get("RECOMMENDATION", "N/A")
        st.subheader(tv_rec)
        st.write(f"Buy: `{tv_ta['summary'].get('BUY')}` | Sell: `{tv_ta['summary'].get('SELL')}`")
    else:
        st.write("Active")
    st.markdown('</div>', unsafe_allow_html=True)

# Row 2: The Holy Trinity Indicators (ADX, MACD Cross, RSI)
ind1, ind2, ind3 = st.columns(3)
with ind1:
    st.markdown('<div class="indicator-card">', unsafe_allow_html=True)
    st.caption("📊 ADX (14) Trend Strength Meter")
    adx_val = indicator_regime['adx']
    adx_badge = "badge-adx-strong" if adx_val >= 25 else "badge-adx-weak"
    st.markdown(f"<span style='font-size:1.4rem; font-weight:bold;'>{adx_val:.1f}</span> <span class='{adx_badge}'>{indicator_regime['trend_grade']}</span>", unsafe_allow_html=True)
    st.write(f"DMI: **{indicator_regime['dmi_leader']}** (+DI:{indicator_regime['plus_di']} | -DI:{indicator_regime['minus_di']})")
    st.markdown('</div>', unsafe_allow_html=True)

with ind2:
    st.markdown('<div class="indicator-card">', unsafe_allow_html=True)
    st.caption("⚡ MACD (12, 26, 9) Cross Radar")
    macd_val = indicator_regime['macd']
    sig_val = indicator_regime['macd_signal']
    if indicator_regime.get('macd_bullish_cross'):
        cross_badge = "<span class='badge-cross-bull'>🚀 FRESH BULLISH CROSS</span>"
    elif indicator_regime.get('macd_bearish_cross'):
        cross_badge = "<span class='badge-cross-bear'>🔻 FRESH BEARISH CROSS</span>"
    elif macd_val > sig_val:
        cross_badge = "<span class='badge-cross-bull'>BULLISH MOMENTUM</span>"
    else:
        cross_badge = "<span class='badge-cross-bear'>BEARISH MOMENTUM</span>"
    st.markdown(f"<span style='font-size:1.2rem; font-weight:bold;'>{macd_val:.2f} / {sig_val:.2f}</span> {cross_badge}", unsafe_allow_html=True)
    st.write(f"Histogram: **{indicator_regime['macd_hist']:.2f}**")
    st.markdown('</div>', unsafe_allow_html=True)

with ind3:
    st.markdown('<div class="indicator-card">', unsafe_allow_html=True)
    st.caption("🌊 RSI (14) Pullback & Exhaustion")
    rsi_val = indicator_regime['rsi']
    if rsi_val >= 70:
        rsi_badge = "<span class='badge-cross-bear'>OVERBOUGHT</span>"
    elif rsi_val <= 30:
        rsi_badge = "<span class='badge-cross-bull'>OVERSOLD</span>"
    elif 40 <= rsi_val <= 60:
        rsi_badge = "<span class='badge-adx-strong'>VALUE PULLBACK ZONE</span>"
    else:
        rsi_badge = "<span>NEUTRAL</span>"
    st.markdown(f"<span style='font-size:1.4rem; font-weight:bold;'>{rsi_val:.1f}</span> {rsi_badge}", unsafe_allow_html=True)
    st.write(f"Status: **{indicator_regime['rsi_status'][:30]}**")
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------
# TRADINGVIEW ADVANCED REAL-TIME INTERACTIVE CHART WIDGET
# -------------------------------------------------------------
tv_widget_html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      background-color: #0b0e14;
      overflow: hidden;
    }}
  </style>
</head>
<body>
  <div class="tradingview-widget-container" style="height:100%;width:100%">
    <div id="tradingview_interactive_chart" style="height:100%;width:100%"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
    new TradingView.widget(
    {{
      "autosize": true,
      "symbol": "{tv_symbol_code}",
      "interval": "{tv_interval_code}",
      "timezone": "Asia/Bangkok",
      "theme": "dark",
      "style": "1",
      "locale": "en",
      "toolbar_bg": "#0b0e14",
      "enable_publishing": false,
      "withdateranges": true,
      "hide_side_toolbar": false,
      "allow_symbol_change": true,
      "save_image": true,
      "studies": [
        "STD;EMA",
        "STD;EMA",
        "STD;EMA",
        "STD;MACD",
        "STD;RSI"
      ],
      "container_id": "tradingview_interactive_chart"
    }}
    );
    </script>
  </div>
</body>
</html>
"""

# Render Views
if "TradingView Official Live Chart" in chart_view_mode:
    st.subheader(f"📺 ផ្ទាំងក្រាហ្វ TradingView ផ្ទាល់ ({tv_display_name})")
    components.html(tv_widget_html, height=680, scrolling=False)

elif "Institutional Multi-Oscillator" in chart_view_mode:
    st.subheader("🔍 ផ្ទាំងវិភាគស្ថាប័ន Multi-Pane (Candlestick + MACD + RSI + ADX)")
    plot_df = df.tail(100)
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])
    fig.add_trace(go.Candlestick(x=plot_df.index, open=plot_df['Open'], high=plot_df['High'], low=plot_df['Low'], close=plot_df['Close'], name="Price", increasing_line_color='#26a69a', decreasing_line_color='#ef5350'), row=1, col=1)
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['EMA20'], mode='lines', name='EMA 20', line=dict(color='#00d2ff', width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['EMA50'], mode='lines', name='EMA 50', line=dict(color='#ffa726', width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['EMA200'], mode='lines', name='EMA 200', line=dict(color='#b388ff', width=2.0)), row=1, col=1)
    
    hist_colors = ['#26a69a' if val >= 0 else '#ef5350' for val in plot_df['MACD_HIST']]
    fig.add_trace(go.Bar(x=plot_df.index, y=plot_df['MACD_HIST'], name='MACD Hist', marker_color=hist_colors), row=2, col=1)
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MACD'], name='MACD', line=dict(color='#2196f3', width=1.5)), row=2, col=1)
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MACD_SIGNAL'], name='Signal', line=dict(color='#ff9800', width=1.5)), row=2, col=1)
    
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['RSI'], name='RSI (14)', line=dict(color='#e040fb', width=1.8)), row=3, col=1)
    fig.add_hline(y=70, line=dict(color='#ef5350', width=1, dash='dot'), row=3, col=1)
    fig.add_hline(y=50, line=dict(color='#ffffff', width=1, dash='dash'), row=3, col=1)
    fig.add_hline(y=30, line=dict(color='#26a69a', width=1, dash='dot'), row=3, col=1)
    
    fig.update_layout(height=720, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

else:
    c_tv, c_pane = st.columns(2)
    with c_tv:
        st.subheader("📺 TradingView Live")
        components.html(tv_widget_html, height=620, scrolling=False)
    with c_pane:
        st.subheader("🔍 Technical Structure")
        plot_df = df.tail(80)
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=plot_df.index, open=plot_df['Open'], high=plot_df['High'], low=plot_df['Low'], close=plot_df['Close'], name="Price"))
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['EMA20'], mode='lines', name='EMA20', line=dict(color='#00d2ff', width=1.5)))
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['EMA50'], mode='lines', name='EMA50', line=dict(color='#ffa726', width=1.5)))
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['EMA200'], mode='lines', name='EMA200', line=dict(color='#b388ff', width=2)))
        fig.update_layout(height=620, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

# Tabs Section
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🇰🇭 ការវិភាគស៊ីជម្រៅ (Khmer Report)",
    "🇬🇧 English Analysis Memo",
    "🤖 Telegram Signal Bot Config & Drop",
    "📊 TradingView Official Metrics",
    "📚 SMC / ICT & Technical Indicators Guide"
])

with tab1:
    st.markdown(analysis_result["report_km"])

with tab2:
    st.markdown(analysis_result["report_en"])

with tab3:
    st.subheader("🤖 Telegram Signal Bot Integration")
    st.caption("ភ្ជាប់ Telegram Bot ផ្ទាល់ខ្លួនរបស់អ្នកដើម្បីឱ្យ AI បាញ់បញ្ជូនសញ្ញា Scalping 15M និងដំណឹង Hit TP/SL ដោយស្វ័យប្រវត្តិ")
    
    col_cfg1, col_cfg2 = st.columns([1, 1.2])
    with col_cfg1:
        st.markdown("#### ⚙️ ការកំណត់អត្តសញ្ញាណ Bot (Bot Credentials)")
        new_token = st.text_input("🔑 Telegram Bot Token (ពី @BotFather):", value=app_cfg.get("telegram_bot_token", ""), type="password")
        new_chat_id = st.text_input("💬 Telegram Chat ID (របស់អ្នក ឬ Channel ID):", value=app_cfg.get("telegram_chat_id", ""))
        
        if st.button("💾 រក្សាទុកការកំណត់ (Save Telegram Config)", use_container_width=True):
            app_cfg["telegram_bot_token"] = new_token.strip()
            app_cfg["telegram_chat_id"] = new_chat_id.strip()
            if save_config(app_cfg):
                st.success("✅ បានរក្សាទុកការកំណត់ Telegram ដោយជោគជ័យ!")
                st.rerun()
            else:
                st.error("❌ មិនអាចរក្សាទុកឯកសារ config បានទេ។")
                
        st.markdown("---")
        st.markdown("#### ℹ️ ការណែនាំដំឡើង Bot ងាយៗ:")
        st.info("""
1. ចូលទៅកាន់ Telegram ហើយ Search រក **`@BotFather`**
2. ផ្ញើពាក្យ **`/newbot`** ➔ បង្កើតឈ្មោះ Bot របស់អ្នក នោះបងនឹងទទួលបាន **Bot Token**
3. ដើម្បីដឹង Chat ID របស់បង គ្រាន់តែ Search រក **`@userinfobot`** ក្នុង Telegram នោះវានឹងបង្ហាញ **Id**
4. ប្រសិនបើចង់ឱ្យ Bot បាញ់ចូល **Telegram Channel / Group**: សូម Add Bot របស់អ្នកចូលជា **Administrator** ក្នុង Channel នោះ!
""")
                
    with col_cfg2:
        st.markdown("#### 🚀 សាកល្បង & បាញ់បញ្ជូនសញ្ញា (Test & Live Drop)")
        if bot.is_configured():
            st.success("🟢 Bot Status: Ready to dispatch signals & alerts")
            
            # Button 1: Send Test Ping
            if st.button("📡 ផ្ញើសារសាកល្បងការតភ្ជាប់ (Send Test Ping to Telegram)", use_container_width=True):
                with st.spinner("កំពុងផ្ញើសារសាកល្បង..."):
                    res = bot.send_test_signal()
                    if res.get("status") == "SUCCESS":
                        st.success("🎉 សារសាកល្បងត្រូវបានផ្ញើចូល Telegram របស់បងជោគជ័យហើយ!")
                    else:
                        st.error(f"❌ បរាជ័យ: {res.get('message')}")
                        
            st.markdown("---")
            st.markdown("##### 🧪 ធ្វើតេស្តបាញ់ Signal គំរូ & ដំណឹង Hit TP / Hit SL:")
            
            c_test1, c_test2 = st.columns(2)
            with c_test1:
                if st.button("🚀 តេស្ត Signal Entry ពេញលេញ", use_container_width=True):
                    with st.spinner("កំពុងបាញ់សញ្ញាគំរូ..."):
                        res = bot.simulate_test_trade_signal(asset, timeframe, "BUY / LONG")
                        if res.get("status") == "SUCCESS":
                            st.success("🎉 សញ្ញាគំរូ Entry + TP1/TP2/TP3 + SL ត្រូវបានបាញ់ចូល Telegram ជោគជ័យ!")
                        else:
                            st.error(f"❌ បរាជ័យ: {res.get('message')}")

                if st.button("🎯 តេស្តដំណឹង Hit TP1 Alert", use_container_width=True):
                    with st.spinner("កំពុងបាញ់ដំណឹង Hit TP1..."):
                        res = bot.simulate_tp_hit(asset, timeframe, tp_level=1)
                        if res.get("status") == "SUCCESS":
                            st.success("🎉 ដំណឹង Hit TP1 + Move SL to BE ត្រូវបានបាញ់ចូល Telegram ជោគជ័យ!")
                        else:
                            st.error(f"❌ បរាជ័យ: {res.get('message')}")

                if st.button("💰 តេស្តដំណឹង Hit TP2 Alert", use_container_width=True):
                    with st.spinner("កំពុងបាញ់ដំណឹង Hit TP2..."):
                        res = bot.simulate_tp_hit(asset, timeframe, tp_level=2)
                        if res.get("status") == "SUCCESS":
                            st.success("🎉 ដំណឹង Hit TP2 (Main Target) ត្រូវបានបាញ់ចូល Telegram ជោគជ័យ!")
                        else:
                            st.error(f"❌ បរាជ័យ: {res.get('message')}")

            with c_test2:
                if st.button("🚀 តេស្តដំណឹង Hit TP3 Alert", use_container_width=True):
                    with st.spinner("កំពុងបាញ់ដំណឹង Hit TP3..."):
                        res = bot.simulate_tp_hit(asset, timeframe, tp_level=3)
                        if res.get("status") == "SUCCESS":
                            st.success("🎉 ដំណឹង Hit TP3 (Runner Full Hit) ត្រូវបានបាញ់ចូល Telegram ជោគជ័យ!")
                        else:
                            st.error(f"❌ បរាជ័យ: {res.get('message')}")

                if st.button("🛑 តេស្តដំណឹង Hit SL Alert", use_container_width=True):
                    with st.spinner("កំពុងបាញ់ដំណឹង Hit SL..."):
                        res = bot.simulate_sl_hit(asset, timeframe)
                        if res.get("status") == "SUCCESS":
                            st.success("🎉 ដំណឹង Hit Stop Loss (SL) ត្រូវបានបាញ់ចូល Telegram ជោគជ័យ!")
                        else:
                            st.error(f"❌ បរាជ័យ: {res.get('message')}")

                if st.button("🛡️ តេស្តដំណឹង Break-Even (BE)", use_container_width=True):
                    with st.spinner("កំពុងបាញ់ដំណឹង BE..."):
                        sim_trade = {"entry": 3526.19 if asset == "XAUUSD" else 60050.00, "action": "BUY / LONG"}
                        res = bot.send_be_hit_alert(asset, timeframe, sim_trade, hit_price=sim_trade["entry"])
                        if res.get("status") == "SUCCESS":
                            st.success("🎉 ដំណឹង Break-Even Closed ត្រូវបានបាញ់ចូល Telegram ជោគជ័យ!")
                        else:
                            st.error(f"❌ បរាជ័យ: {res.get('message')}")

            st.markdown("---")
            # Button: Blast Current Live Signal
            if st.button(f"🚨 បាញ់បញ្ជូនសញ្ញា {asset} ({timeframe}) ពេលនេះភ្លាមៗ (Drop Live Signal)", use_container_width=True):
                with st.spinner(f"កំពុងបាញ់បញ្ជូនសញ្ញា {asset} ចូល Telegram..."):
                    res = bot.dispatch_trade_signal(asset, timeframe, analysis_result, indicator_regime)
                    if res.get("status") == "SUCCESS":
                        st.success(f"🎉 សញ្ញា {asset} ({analysis_result['setup_action']}) ត្រូវបានទម្លាក់ចូល Telegram ជោគជ័យ!")
                    elif res.get("status") == "BLOCKED":
                        st.warning(f"⚠️ {res.get('message')}")
                    else:
                        st.error(f"❌ បរាជ័យ: {res.get('message')}")
        else:
            st.warning("⚠️ សូមបញ្ចូល **Bot Token** និង **Chat ID** របស់អ្នកនៅខាងឆ្វេងដៃ ហើយចុច 'Save' សិន ដើម្បីបើកដំណើរការមុខងារនេះ។")
            st.info("""
**របៀបបង្កើត Bot Token & Chat ID ងាយៗក្នុងរយៈពេល ១ នាទី៖**
1. ចូលទៅកាន់ Telegram ហើយ Search រក **`@BotFather`**
2. ចុច Start ហើយផ្ញើពាក្យ **`/newbot`** ➔ បង្កើតឈ្មោះ Bot របស់អ្នក នោះបងនឹងទទួលបាន **Bot Token** មួយខ្សែវែង។
3. ដើម្បីដឹង Chat ID របស់បង គ្រាន់តែ Search រក **`@userinfobot`** ក្នុង Telegram នោះវានឹងប្រាប់ **Id** របស់បងភ្លាមៗ!
""")

with tab4:
    st.subheader(f"📊 TradingView Official Technical Breakdown ({asset})")
    if tv_ta.get("status") == "SUCCESS":
        c_osc, c_ma = st.columns(2)
        with c_osc:
            st.markdown("#### 🌊 Oscillators")
            osc = tv_ta["oscillators"]
            st.write(f"Recommendation: **{osc.get('RECOMMENDATION')}**")
            st.write(f"Buy: `{osc.get('BUY')}` | Sell: `{osc.get('SELL')}` | Neutral: `{osc.get('NEUTRAL')}`")
            st.json(osc.get("COMPUTE", {}))
        with c_ma:
            st.markdown("#### 📈 Moving Averages")
            ma = tv_ta["moving_averages"]
            st.write(f"Recommendation: **{ma.get('RECOMMENDATION')}**")
            st.write(f"Buy: `{ma.get('BUY')}` | Sell: `{ma.get('SELL')}` | Neutral: `{ma.get('NEUTRAL')}`")
            st.json(ma.get("COMPUTE", {}))

with tab5:
    st.subheader("📚 បណ្តុំចំណេះដឹង & ក្បួនជួញដូរអាជីព SMC / ICT / EMA / ADX / MACD / RSI")
    st.markdown("""
### 1. សូចនាករ Exponential Moving Average (EMA 20, 50, 200)
- **EMA 20 (Cyan Line):** តំណាងឱ្យកម្លាំងចលកររយៈពេលខ្លី (Short-term Momentum)។
- **EMA 50 (Orange Line):** ខ្សែបន្ទាត់ទប់ទល់ពេលតម្លៃទាញថយក្រោយ (Dynamic Pullback Support/Resistance)។
- **EMA 200 (Purple Line):** ខ្សែបន្ទាត់កាត់សេចក្តីម៉ាក្រូ (Macro Trend Divider)។
- **Golden Alignment:** EMA 20 > EMA 50 > EMA 200 = **Strong Bullish Stack**

---

### 2. រង្វាស់កម្លាំងនិន្នាការ ADX (14) & DMI
- **ADX < 20:** ទីផ្សារដើរស្មើ (Sideways/Choppy) - ហាមជួញដូរដាច់ខាត!
- **ADX 25 - 40:** តំបន់មាសរកលុយ (Strong Trend) - ល្អបំផុតសម្រាប់ EMA Pullback Scalping!
- **+DI > -DI:** អ្នកទិញកំពុងគ្រប់គ្រងទីផ្សារ | **-DI > +DI:** អ្នកលក់កំពុងគ្រប់គ្រងទីផ្សារ។

---

### 3. សន្ទុះចលករ MACD (12, 26, 9) & Cross
- **Fresh Bullish Cross:** MACD Line កាត់ឡើងលើ Signal Line = សញ្ញា Trigger បញ្ជាក់ការទិញផ្ទុះឡើង។
- **Fresh Bearish Cross:** MACD Line កាត់ចុះក្រោម Signal Line = សញ្ញា Trigger បញ្ជាក់ការលក់រុញទម្លាក់។

---

### 4. រ៉ាដា RSI (14) Pullback & Exhaustion
- **40 - 60 Zone:** តំបន់ទាញថយក្រោយប្រកបដោយសុវត្ថិភាព (Value Pullback Zone) សម្រាប់ Trend Continuation។
- **> 70:** Overbought (ប្រយ័ត្នការកែប្រែទិសដៅធ្លាក់ចុះ) | **< 30:** Oversold (ប្រយ័ត្នការស្ទុះងើបឡើង)។
""")
