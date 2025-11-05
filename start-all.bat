@echo off
REM ============================================================================
REM Windows AI Complete Starter (Windows)
REM Starts all components: Backend, GUI, and Tray
REM ============================================================================

echo ==========================================
echo 🚀 Starting Windows AI - Complete System
echo ==========================================
echo.

echo Starting services...
echo.

REM Start backend in new window
echo 1️⃣  Starting Backend...
start "Windows AI Backend" /MIN cmd /c "start-backend.bat"
echo    Backend starting in separate window...

REM Wait for backend to be ready
echo    Waiting for backend to start...
timeout /t 5 /nobreak >nul

:wait_backend
curl -s http://localhost:8010/health >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    timeout /t 1 /nobreak >nul
    goto wait_backend
)
echo    ✓ Backend is online

timeout /t 2 /nobreak >nul

REM Start tray in new window
echo.
echo 2️⃣  Starting System Tray...
start "Windows AI Tray" /MIN cmd /c "start-tray.bat"
echo    Tray starting in separate window...

timeout /t 2 /nobreak >nul

REM Start GUI in new window
echo.
echo 3️⃣  Starting GUI...
start "Windows AI GUI" cmd /c "start-gui.bat"
echo    GUI starting in separate window...

echo.
echo ==========================================
echo ✅ Windows AI is starting!
echo ==========================================
echo.
echo Services:
echo   🔧 Backend:    http://localhost:8010
echo   💬 Chat GUI:   Opening in Electron...
echo   🔔 Tray:       Check system tray (bottom-right)
echo.
echo Quick Actions:
echo   • Ctrl+Shift+Space : Quick command
echo   • Double-click tray: Open chat
echo   • Right-click tray : Menu
echo.
echo All services are running in separate windows.
echo Close each window to stop that service.
echo.
pause
