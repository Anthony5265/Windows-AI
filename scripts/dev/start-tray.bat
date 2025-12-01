@echo off
REM ============================================================================
REM Windows AI Tray Starter (Windows)
REM Starts the system tray application
REM ============================================================================

echo ==========================================
echo Starting Windows AI Tray
echo ==========================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Error: Node.js is not installed
    echo Please install Node.js 18 or higher
    pause
    exit /b 1
)

REM Navigate to tray directory
cd windows-ai-tray

REM Check if node_modules exists
if not exist "node_modules\" (
    echo ⚠ Installing tray dependencies...
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Failed to install dependencies
        cd ..
        pause
        exit /b 1
    )
)

echo ✓ Dependencies installed
echo.

REM Check if backend is running
curl -s http://localhost:8010/health >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ Backend is online
) else (
    echo ⚠ Warning: Backend is not responding
    echo   Start the backend first with: start-backend.bat
    echo   Tray will show offline until backend starts
)

echo.
echo Starting System Tray...
echo Global shortcut: Ctrl+Shift+Space for quick command
echo ==========================================
echo.

REM Start the tray
call npm start

cd ..
pause
