@echo off
title Pheara Pro Trader AI - CLI Terminal Audit
cd /d "%~dp0"
cls

echo ===================================================================
echo               PHEARA PRO TRADER AI - RAPID CLI AUDIT
echo                   Live TradingView WebSocket Feed
echo ===================================================================
echo.
set PATH=%APPDATA%\Python\Python313\Scripts;C:\Program Files\Python313\Scripts;%PATH%

echo Streaming Real-Time Institutional Audit for Gold (XAUUSD 1h)...
echo.
python cli_analyst.py --asset XAUUSD --timeframe 1h
echo.
echo ===================================================================
echo To analyze Bitcoin (BTCUSD 15m), run:
echo   python cli_analyst.py --asset BTCUSD --timeframe 15m
echo ===================================================================
echo.
pause
