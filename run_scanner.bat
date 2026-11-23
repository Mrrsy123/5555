@echo off
title Pheara Pro Trader AI - Auto Telegram Signal Scanner
cd /d "%~dp0"
cls

echo ===================================================================
echo           PHEARA PRO TRADER AI - AUTO TELEGRAM SCANNER
echo    Autonomous 15M Scalp Signal Generator for FXCM & Bitstamp
echo ===================================================================
echo.
set PATH=%APPDATA%\Python\Python313\Scripts;C:\Program Files\Python313\Scripts;%PATH%

echo Starting background scanner daemon...
echo Signals will automatically drop into your Telegram bot!
echo (Press Ctrl+C to stop scanning)
echo.
python scanner_daemon.py
pause
