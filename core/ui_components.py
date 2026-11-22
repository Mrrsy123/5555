"""
UI Components Module:
Generates custom institutional HTML/CSS Signal Cards matching professional trading desk UI.
Formatted cleanly without Markdown codeblock indentation.
"""

from datetime import datetime
import pytz
import textwrap

def generate_signal_card_html(
    asset: str,
    timeframe: str,
    analysis: dict,
    indicator_regime: dict,
    status_label: str = "LIVE ACTIVE"
) -> str:
    """
    Renders an institutional trading signal card matching the dark-mode desk aesthetic.
    Guarantees no leading whitespace so Streamlit/Markdown parses raw HTML correctly.
    """
    plan = analysis.get("plan", {})
    bias = analysis.get("bias", "NEUTRAL")
    score = analysis.get("confluence_score", 70)
    
    is_buy = "BUY" in bias or "BULLISH" in bias
    is_sell = "SELL" in bias or "BEARISH" in bias
    
    # Border & Pill Colors
    if is_buy:
        border_color = "#238636"
        glow = "rgba(46, 204, 113, 0.15)"
        pill_bg = "rgba(46, 204, 113, 0.15)"
        pill_color = "#2ecc71"
        pill_border = "rgba(46, 204, 113, 0.4)"
        action_text = "● BUY"
    elif is_sell:
        border_color = "#da3633"
        glow = "rgba(231, 76, 60, 0.15)"
        pill_bg = "rgba(231, 76, 60, 0.15)"
        pill_color = "#e74c3c"
        pill_border = "rgba(231, 76, 60, 0.4)"
        action_text = "● SELL"
    else:
        border_color = "#d29922"
        glow = "rgba(210, 153, 34, 0.15)"
        pill_bg = "rgba(210, 153, 34, 0.15)"
        pill_color = "#d29922"
        pill_border = "rgba(210, 153, 34, 0.4)"
        action_text = "● WAIT"
        status_label = "AWAITING CONFLUENCE"

    action_pill = f"""<div style="display:flex; flex-direction:column; align-items:center; gap:4px;"><span style="background:{pill_bg}; color:{pill_color}; border:1px solid {pill_border}; padding:3px 14px; border-radius:14px; font-size:0.75rem; font-weight:700;">{action_text}</span><span style="background:#161b22; color:#8b949e; border:1px solid #30363d; padding:2px 8px; border-radius:10px; font-size:0.65rem; font-weight:600;">DESK</span></div>"""

    # Asset specific icon & subtext
    if asset == "XAUUSD":
        icon_html = """<div style="width:36px; height:36px; border-radius:50%; background:#d97706; display:flex; align-items:center; justify-content:center; font-size:1.1rem; box-shadow:0 0 10px rgba(217, 119, 6, 0.3);">🧈</div>"""
        symbol_text = "XAUUSD"
        sub_text = f"FXCM Gold · {timeframe}"
    else:
        icon_html = """<div style="width:36px; height:36px; border-radius:50%; background:#f7931a; display:flex; align-items:center; justify-content:center; font-weight:bold; color:white; font-size:1.1rem; box-shadow:0 0 10px rgba(247, 147, 26, 0.3);">₿</div>"""
        symbol_text = "BTCUSD"
        sub_text = f"Bitstamp BTC · {timeframe}"

    # Timeframe header badge
    tf_badge = "INTRADAY (15M)" if timeframe == "15m" else ("SWING (4H)" if timeframe == "4h" else f"TIMEFRAME ({timeframe})")
    
    # Values
    live_price = plan.get('current_live_price', plan.get('entry', 0))
    entry_val = f"{plan.get('entry', 0):,.2f}"
    
    if action_text == "● WAIT":
        target_val = "Standby (No Signal)"
        stop_val = "Standby (No Signal)"
        conviction_text = "● Awaiting Confluence (Oscillators Mixed)"
        conviction_bg = "rgba(210, 153, 34, 0.1)"
        conviction_color = "#d29922"
        conviction_border = "rgba(210, 153, 34, 0.3)"
    else:
        target_val = f"{plan.get('tp2', plan.get('tp1', 0)):,.2f}"
        stop_val = f"{plan.get('sl', 0):,.2f}"
        conviction_text = f"● High conviction setup ({score}/100)" if score >= 75 else f"● Moderate setup ({score}/100)"
        conviction_bg = "rgba(46, 204, 113, 0.08)"
        conviction_color = "#2ecc71"
        conviction_border = "rgba(46, 204, 113, 0.3)"
    
    # Opened time
    now_utc_str = datetime.now(pytz.utc).strftime("%b %d, %Y · %H:%M UTC")
    
    # Trend & Conflict tags
    conflict_note = analysis.get("conflict_note", "")
    adx_grade = indicator_regime.get("trend_grade", "NORMAL")
    tag_trending = f"⚠️ {conflict_note}" if (action_text == "● WAIT" and conflict_note) else ("Trending" if adx_grade in ["STRONG", "VERY_STRONG"] else "Consolidation")
    rrr_text = f"RRR {plan.get('rrr', 'Standby')}"

    # Single-line HTML blocks to prevent Markdown code-block interpretation
    card_html = f"""<div style="background:#0d1117; border:1.5px solid {border_color}; box-shadow:0 4px 20px {glow}; border-radius:14px; padding:16px 18px; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color:#e6edf3; margin-bottom:15px;"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;"><div style="display:flex; align-items:center; gap:10px;">{icon_html}<div><div style="font-weight:700; font-size:1.1rem; color:#ffffff; letter-spacing:0.5px;">{symbol_text}</div><div style="font-size:0.75rem; color:#8b949e;">{sub_text}</div></div></div><div style="background:#161b22; color:#8b949e; border:1px solid #30363d; padding:3px 10px; border-radius:12px; font-size:0.7rem; font-weight:600; letter-spacing:0.5px;">{tf_badge}</div></div><div style="display:flex; justify-content:center; margin-bottom:14px;">{action_pill}</div><div style="border-top:1px solid #21262d; border-bottom:1px solid #21262d; padding:10px 0; margin-bottom:12px;"><div style="display:flex; justify-content:space-between; margin-bottom:6px;"><span style="color:#8b949e; font-size:0.85rem;">Entry (Market)</span><span style="font-weight:700; font-size:0.95rem; color:#e6edf3;">{entry_val}</span></div><div style="display:flex; justify-content:space-between; margin-bottom:6px;"><span style="color:#8b949e; font-size:0.85rem;">Target</span><span style="font-weight:700; font-size:0.95rem; color:{'#8b949e' if action_text == '● WAIT' else '#2ecc71'};">{target_val}</span></div><div style="display:flex; justify-content:space-between;"><span style="color:#8b949e; font-size:0.85rem;">Stop</span><span style="font-weight:700; font-size:0.95rem; color:{'#8b949e' if action_text == '● WAIT' else '#e74c3c'};">{stop_val}</span></div></div><div style="margin-bottom:10px;"><span style="background:{conviction_bg}; color:{conviction_color}; border:1px solid {conviction_border}; padding:3px 10px; border-radius:12px; font-size:0.72rem; font-weight:600; display:inline-block;">{conviction_text} ⌄</span></div><div style="font-size:0.75rem; color:#8b949e; margin-bottom:12px;"><div style="display:flex; justify-content:space-between; margin-bottom:4px;"><span>Opened</span><span style="color:#c9d1d9;">{now_utc_str}</span></div><div style="display:flex; justify-content:space-between;"><span>Status</span><span style="color:#58a6ff; font-weight:600;">{status_label}</span></div></div><div style="display:flex; flex-wrap:wrap; gap:6px; align-items:center;"><span style="background:#161b22; color:#d29922; border:1px solid #30363d; padding:3px 8px; border-radius:12px; font-size:0.68rem;">{tag_trending}</span><span style="background:#161b22; color:#c9d1d9; border:1px solid #30363d; padding:3px 8px; border-radius:12px; font-size:0.68rem; font-weight:600;">Auto (Multi-Oscillator Confluence)</span><span style="font-size:0.68rem; color:#8b949e; margin-left:auto;">{rrr_text}</span></div></div>"""
    return card_html
