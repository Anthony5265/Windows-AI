@echo off
REM Start Windows AI Watchdog Service
REM This script starts the watchdog service that monitors and auto-restarts the backend

echo ========================================
echo Windows AI Watchdog Service
echo ========================================
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if watchdog.py exists
if not exist "watchdog.py" (
    echo ERROR: watchdog.py not found in %SCRIPT_DIR%
    pause
    exit /b 1
)

REM Install required dependencies if needed
echo Checking dependencies...
python -c "import psutil, aiohttp" 2>nul
if errorlevel 1 (
    echo Installing watchdog dependencies...
    python -m pip install psutil aiohttp
)

echo Starting watchdog service...
echo Logs will be written to watchdog.log
echo Press Ctrl+C to stop
echo.

REM Start watchdog
python watchdog.py
