"""
Pheara Pro Trader AI - CLI Terminal Mode
Instant terminal-based smart money market analysis with Rich formatting.
Powered by direct TradingView Live WebSocket Feed!
Integrated with: EMA 20/50/200, ADX(14), MACD(12,26,9), RSI(14) & SMC/ICT!
"""

import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from core.data_fetcher import fetch_market_data
from core.tradingview_stream import get_tradingview_official_ta
from core.indicators import calculate_technical_indicators, analyze_indicator_telemetry
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

console = Console()

def run_analysis(asset: str = "XAUUSD", timeframe: str = "15m"):
    console.print(f"\n[bold cyan]🦅 PHEARA PRO TRADER AI - INSTITUTIONAL AUDIT[/bold cyan]")
    feed_label = "FXCM:XAUUSD" if asset == "XAUUSD" else "BITSTAMP:BTCUSD"
    console.print(f"[bold green]🔴 LIVE TRADINGVIEW VERIFIED STREAM: {feed_label}[/bold green] [dim]({timeframe})[/dim]\n")
    
    with console.status("[bold green]Streaming live candles and computing ADX, MACD, RSI, SMC...[/bold green]"):
        raw_df = fetch_market_data(asset, timeframe)
        source_label = raw_df.attrs.get("source", "TradingView Live")
        
        tv_ta = get_tradingview_official_ta(asset, timeframe)
        
        df = calculate_technical_indicators(raw_df)
        indicators = analyze_indicator_telemetry(df)
        
        swing_highs, swing_lows = find_swings(df, window=3)
        fvgs = detect_fvgs(df)
        market_events = detect_market_structure(df, swing_highs, swing_lows)
        obs = detect_order_blocks(df)
        dealing_range = calculate_dealing_range(swing_highs, swing_lows, indicators["close"])
        sweeps = detect_liquidity_sweeps(df, swing_highs, swing_lows)
        killzone_info = check_ict_killzone()
        
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
        
        analyst = LocalAIAnalyst()
        res = analyst.analyze(asset, timeframe, df, indicators, smc_payload)
        plan = res["plan"]

    # Table of Core Metrics
    table = Table(title=f"Market Telemetry: {feed_label} ({timeframe})", border_style="cyan")
    table.add_column("Indicator / Metric", style="bold white")
    table.add_column("Current Value", style="bold yellow")
    table.add_column("Institutional Note & Status", style="green")

    table.add_row("Live Price", f"${indicators['close']:,.3f}" if asset == "XAUUSD" else f"${indicators['close']:,.2f}", f"Vs EMA20: {indicators['price_vs_ema20']}")
    table.add_row("EMA Stack (20/50/200)", f"20:{indicators['ema20']} | 50:{indicators['ema50']} | 200:{indicators['ema200']}", indicators['trend_status'])
    table.add_row("ADX (14) Trend Strength", f"{indicators['adx']:.1f} ({indicators['trend_grade']})", indicators['adx_strength'])
    table.add_row("DMI Directional Movement", f"+DI:{indicators['plus_di']} | -DI:{indicators['minus_di']}", indicators['dmi_leader'])
    table.add_row("MACD (12, 26, 9) Radar", f"MACD:{indicators['macd']} | Sig:{indicators['macd_signal']}", indicators['macd_status'])
    table.add_row("RSI (14) Momentum", f"{indicators['rsi']:.1f}", indicators['rsi_status'])
    table.add_row("Dealing Range", f"{dealing_range.get('zone')} ({dealing_range.get('relative_position_pct')}%)", dealing_range.get('zone_detail'))
    table.add_row("ICT Session", killzone_info['session'], killzone_info['name'])
    
    if tv_ta.get("status") == "SUCCESS":
        tv_summary = tv_ta["summary"]
        table.add_row("TradingView Official TA", f"{tv_summary.get('RECOMMENDATION')}", f"Buy:{tv_summary.get('BUY')} | Sell:{tv_summary.get('SELL')} | Neutral:{tv_summary.get('NEUTRAL')}")
        
    table.add_row("Pheara Institutional Bias", res['bias'], res['bias_km'])
    table.add_row("Confluence Rating", f"{res['confluence_score']}/100", f"Setup: {res['setup_action']}")
    
    console.print(table)
    
    # Trade Plan Panel
    plan_text = f"""
[bold yellow]ENTRY ZONE:[/bold yellow] {plan['entry']}
[bold red]STOP LOSS (Invalidation):[/bold red] {plan['sl']}
[bold green]TAKE PROFIT 1:[/bold green] {plan['tp1']}
[bold green]TAKE PROFIT 2 (Main Target):[/bold green] {plan['tp2']}
[bold green]TAKE PROFIT 3 (Runner):[/bold green] {plan['tp3']}
[bold cyan]RISK:REWARD RATIO:[/bold cyan] {plan['rrr']} (Risk: {plan['risk_pips_points']} pts)
"""
    console.print(Panel(plan_text, title="🎯 Trade Execution Roadmap", border_style="bold green"))
    
    # Khmer Analysis
    console.print(Panel(Markdown(res["report_km"]), title="🇰🇭 ការវិភាគបច្ចេកទេសលម្អិត", border_style="blue"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pheara Pro Trader AI")
    parser.add_argument("--asset", type=str, default="XAUUSD", choices=["XAUUSD", "BTCUSD"], help="Asset symbol")
    parser.add_argument("--timeframe", type=str, default="15m", choices=["15m", "1h", "4h", "1d"], help="Candle timeframe")
    args = parser.parse_args()
    
    run_analysis(args.asset, args.timeframe)
