"""
Auto-Scanner Daemon for Pheara Pro Trader AI
Continuously monitors FXCM:XAUUSD and BITSTAMP:BTCUSD on 15m.
Automatically drops signals into Telegram Bot on Grade A+ Setups.
"""

import time
import sys
import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import pytz
from rich.console import Console
from rich.panel import Panel
from rich.markup import escape

from config import load_config
from core.data_fetcher import fetch_market_data
from core.indicators import calculate_technical_indicators, analyze_indicator_telemetry
from core.smc_engine import (
    find_swings, detect_fvgs, detect_market_structure,
    detect_order_blocks, calculate_dealing_range, detect_liquidity_sweeps, check_ict_killzone
)
from core.ai_analyst import LocalAIAnalyst
from core.telegram_bot import TelegramSignalBot
from core.trade_tracker import monitor_trade_outcomes

console = Console()

# Keep track of dispatched signals to prevent duplicate spam
dispatched_signals = {}  # key: (symbol, candle_time), value: direction

class CloudHealthHandler(BaseHTTPRequestHandler):
    """Lightweight HTTP endpoint for Render / Cloud health probes"""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        body = {
            "status": "ONLINE",
            "service": "Pheara Pro Trader AI Cloud Scanner",
            "uptime_utc": datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
            "message": "Autonomous 24/7 scanning active for XAUUSD & BTCUSD"
        }
        self.wfile.write(json.dumps(body).encode('utf-8'))
        
    def log_message(self, format, *args):
        return

def start_cloud_health_server(port: int):
    try:
        server = HTTPServer(('0.0.0.0', port), CloudHealthHandler)
        console.print(f"[bold green]🌐 Cloud Health-Check HTTP server running on 0.0.0.0:{port}[/bold green]")
        server.serve_forever()
    except Exception as e:
        console.print(f"[yellow]Cloud HTTP server notice: {e}[/yellow]")

def run_scanner_loop():
    cfg = load_config()
    token = cfg.get("telegram_bot_token", "").strip()
    chat_id = cfg.get("telegram_chat_id", "").strip()
    min_score = cfg.get("min_confluence_score", 70)
    interval = cfg.get("scan_interval_seconds", 60)
    assets = ["BTCUSD", "XAUUSD"]
    timeframe = cfg.get("timeframe", "15m")
    
    # Render / Cloud Port Binding
    port_env = os.environ.get("PORT")
    if port_env:
        try:
            http_port = int(port_env)
            t = threading.Thread(target=start_cloud_health_server, args=(http_port,), daemon=True)
            t.start()
        except Exception as e:
            console.print(f"[yellow]Notice starting port listener: {e}[/yellow]")
    
    bot = TelegramSignalBot(token, chat_id)
    
    bot_color = "green" if bot.is_configured() else "red"
    bot_label = "Configured" if bot.is_configured() else "Missing Token or Chat ID"
    
    console.print(Panel(
        f"[bold cyan]🦅 PHEARA PRO TRADER AI - AUTO SIGNAL SCANNER[/bold cyan]\n"
        f"• Assets: [yellow]{', '.join(assets)}[/yellow] | Timeframe: [green]{timeframe}[/green]\n"
        f"• Min Confluence Score: [magenta]{min_score}/100[/magenta]\n"
        f"• Scan Interval: [white]{interval} seconds[/white]\n"
        f"• Telegram Bot Status: [{bot_color}]{bot_label}[/{bot_color}]",
        title="🤖 Autonomous Daemon Active",
        border_style="cyan"
    ))
    
    if not bot.is_configured():
        console.print("[yellow]⚠️ Warning: Telegram Bot credentials are not set in telegram_config.json.[/yellow]")
        console.print("[yellow]Signals will be logged to console only until configured.[/yellow]\n")
        
    analyst = LocalAIAnalyst()
    
    while True:
        try:
            now_str = datetime.now(pytz.timezone('Asia/Phnom_Penh')).strftime('%H:%M:%S')
            console.print(f"[dim]─── [{now_str} UTC+7] Scanning market order flow ───[/dim]")
            
            for asset in assets:
                try:
                    raw_df = fetch_market_data(asset, timeframe)
                    df = calculate_technical_indicators(raw_df)
                    indicators = analyze_indicator_telemetry(df)
                    
                    # 🎯 Monitor open trade lifecycle (Automated TP / SL Alerting)
                    try:
                        latest_candle = df.iloc[-1].to_dict()
                        tp_sl_events = monitor_trade_outcomes(asset, timeframe, latest_candle, bot)
                        for ev in tp_sl_events:
                            if "TP" in ev["type"]:
                                console.print(f"[bold green]🎯 {ev['type']} HIT ALERT DISPATCHED FOR {asset} at {ev['hit_price']}![/bold green]")
                            elif "SL" in ev["type"]:
                                console.print(f"[bold red]🛑 SL HIT ALERT DISPATCHED FOR {asset} at {ev['hit_price']}![/bold red]")
                            elif "BE" in ev["type"]:
                                console.print(f"[bold cyan]🛡️ BREAK-EVEN (BE) HIT ALERT DISPATCHED FOR {asset} at {ev['hit_price']}![/bold cyan]")
                    except Exception as trk_err:
                        console.print(f"[dim]Tracking check notice: {trk_err}[/dim]")
                    
                    sh, sl = find_swings(df, window=3)
                    fvgs = detect_fvgs(df)
                    events = detect_market_structure(df, sh, sl)
                    obs = detect_order_blocks(df)
                    dr = calculate_dealing_range(sh, sl, indicators["close"])
                    sweeps = detect_liquidity_sweeps(df, sh, sl)
                    kz = check_ict_killzone()
                    
                    smc_payload = {
                        "swing_highs": sh,
                        "swing_lows": sl,
                        "fvgs": fvgs,
                        "structure_events": events,
                        "order_blocks": obs,
                        "dealing_range": dr,
                        "sweeps": sweeps,
                        "killzone": kz
                    }
                    
                    analysis = analyst.analyze(asset, timeframe, df, indicators, smc_payload)
                    score = analysis["confluence_score"]
                    bias = analysis["bias"]
                    last_candle_time = str(df.index[-1])
                    
                    sig_key = (asset, last_candle_time)
                    
                    # Check if Setup meets criteria (Strict Multi-Oscillator Confluence Required)
                    action = analysis.get("setup_action", "WAIT / NO TRADE")
                    if action in ["BUY / LONG", "SELL / SHORT"] and score >= min_score:
                        # Anti-Duplicate Guard 1: Suppress if an active trade is already RUNNING
                        from core.trade_tracker import has_active_trade, get_active_trade
                        if has_active_trade(asset, timeframe):
                            act = get_active_trade(asset, timeframe)
                            console.print(f"[dim]{asset}: Position is already RUNNING ({act.get('action')} @ {act.get('entry'):,.2f}). Suppressing duplicate signal until TP/SL outcome.[/dim]")
                            continue

                        # Anti-Duplicate Guard 2: Send ONLY ONCE per setup direction
                        if dispatched_signals.get(asset) == action:
                            console.print(f"[dim]{asset}: Signal ({action}) already sent once. Suppressing duplicate.[/dim]")
                            continue

                        console.print(f"[bold green]🚨 GRADE A+ CONFLUENCE SETUP DETECTED FOR {asset} ({score}/100)![/bold green]")
                        console.print(f"Action: [bold yellow]{action}[/bold yellow] | Entry: {analysis['plan']['entry']} | SL: {analysis['plan']['sl']}")
                        
                        if bot.is_configured():
                            res = bot.dispatch_trade_signal(asset, timeframe, analysis, indicators)
                            if res.get("status") == "SUCCESS":
                                console.print(f"[bold green]✅ Single confluent signal dropped into Telegram for {asset}![/bold green]")
                                dispatched_signals[asset] = action
                            else:
                                console.print(f"[bold yellow]⚠️ Blocked from Telegram: {escape(str(res.get('message')))}[/bold yellow]")
                        else:
                            dispatched_signals[asset] = action
                    else:
                        conflict = analysis.get("conflict_note", "Oscillators mixed")
                        console.print(f"[dim]{asset}: Standing by (Score {score}/100) — {escape(str(conflict))}[/dim]")
                        
                except Exception as asset_err:
                    console.print(f"[red]Error analyzing {asset}: {asset_err}[/red]")
                    
            time.sleep(interval)
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Scanner paused by user.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Loop error: {e}[/red]")
            time.sleep(10)

if __name__ == "__main__":
    run_scanner_loop()
