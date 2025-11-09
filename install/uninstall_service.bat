@echo off
REM Uninstall Windows AI Windows Service

echo ========================================
echo Windows AI Service Uninstaller
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

echo Uninstalling Windows AI Service...
echo.

REM Stop service
echo Stopping service...
net stop WindowsAI 2>nul

REM Remove service
python install\windows_service.py remove
if errorlevel 1 (
    echo.
    echo ERROR: Service removal failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS!
echo ========================================
echo.
echo Windows AI Service has been removed
echo.

pause
