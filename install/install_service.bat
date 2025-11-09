@echo off
REM Install Windows AI as a Windows Service
REM This enables auto-start on Windows boot

echo ========================================
echo Windows AI Service Installer
echo ========================================
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Administrator rights required
    echo Please run this script as Administrator
    echo.
    pause
    exit /b 1
)

REM Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%\.."

echo Installing Windows AI Service...
echo.

REM Install pywin32 if needed
echo Checking dependencies...
python -c "import win32serviceutil" 2>nul
if errorlevel 1 (
    echo Installing pywin32...
    python -m pip install pywin32
    if errorlevel 1 (
        echo ERROR: Failed to install pywin32
        pause
        exit /b 1
    )
)

REM Install service
echo.
echo Installing service...
python install\windows_service.py install
if errorlevel 1 (
    echo.
    echo ERROR: Service installation failed
    pause
    exit /b 1
)

REM Start service
echo.
echo Starting service...
net start WindowsAI
if errorlevel 1 (
    echo.
    echo WARNING: Service installed but failed to start
    echo Check logs\windows_service.log for details
) else (
    echo.
    echo ========================================
    echo SUCCESS!
    echo ========================================
    echo.
    echo Windows AI is now running as a service
    echo It will auto-start on Windows boot
    echo.
    echo Service Status:
    sc query WindowsAI
    echo.
    echo Backend URL: http://localhost:8010
    echo Logs: logs\windows_service.log
    echo.
)

echo.
pause
