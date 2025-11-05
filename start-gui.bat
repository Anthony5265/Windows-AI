@echo off
REM ============================================================================
REM Windows AI GUI Starter (Windows)
REM Starts the Electron chat GUI
REM ============================================================================

echo ==========================================
echo Starting Windows AI GUI
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

REM Display Node version
for /f "tokens=1" %%i in ('node --version') do set NODE_VERSION=%%i
echo ✓ Node version: %NODE_VERSION%

REM Navigate to GUI directory
cd apps\gui

REM Check if node_modules exists
if not exist "node_modules\" (
    echo ⚠ Installing GUI dependencies...
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Failed to install dependencies
        cd ..\..
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
    echo   Continuing anyway...
)

echo.
echo Starting Electron GUI...
echo ==========================================
echo.

REM Start the GUI
call npm start

cd ..\..
pause
