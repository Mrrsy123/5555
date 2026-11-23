@echo off
title Pheara Pro Trader AI Terminal
cd /d "%~dp0"
cls

echo ===================================================================
echo             PHEARA PRO TRADER AI - INSTITUTIONAL TERMINAL
echo        Live TradingView Stream • SMC / ICT • EMA 20/50/200
echo ===================================================================
echo.
echo [1/3] Configuring environment paths...
set PATH=%APPDATA%\Python\Python313\Scripts;C:\Program Files\Python313\Scripts;%PATH%

echo [2/3] Checking Python runtime...
python --version
if errorlevel 1 (
    echo.
    echo [ERROR] Python was not found in your system.
    pause
    exit /b
)

echo [3/3] Starting Live Streamlit Server on http://localhost:8501 ...
echo Opening your default browser automatically...
echo.
echo ===================================================================
echo (Leave this black window open while trading. Press Ctrl+C to stop)
echo ===================================================================
echo.

start "" http://localhost:8501
python -m streamlit run app.py --browser.gatherUsageStats false --browser.serverAddress localhost --server.port 8501

if errorlevel 1 (
    echo.
    echo [ERROR] Application stopped unexpectedly.
    pause
)
