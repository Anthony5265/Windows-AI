@echo off
REM Build Windows AI Installer - Temporarily disables Windows Defender

REM Change to the script's directory
pushd "%~dp0"

echo ============================================
echo Windows AI Installer Build Script
echo ============================================
echo.
echo Script location: %~dp0
echo Current directory: %CD%
echo.
echo This will temporarily disable Windows Defender Real-Time Protection
echo to allow electron-builder to create the installer.
echo.
echo Windows Defender will re-enable automatically on next reboot.
echo.
pause

echo.
echo [1/3] Disabling Windows Defender...
PowerShell -Command "Set-MpPreference -DisableRealtimeMonitoring $true" 2>nul
if errorlevel 1 (
    echo ERROR: Failed to disable Windows Defender
    echo Please run this script as Administrator
    pause
    popd
    exit /b 1
)
echo   ✓ Windows Defender temporarily disabled

echo.
echo [2/3] Building installer...
echo Checking paths...
if not exist "apps\gui" (
    echo ERROR: apps\gui directory not found!
    echo Current directory: %CD%
    echo.
    dir
    pause
    PowerShell -Command "Set-MpPreference -DisableRealtimeMonitoring $false" 2>nul
    popd
    exit /b 1
)

echo Changing to apps\gui...
pushd apps\gui
echo Now in: %CD%

if not exist "package.json" (
    echo ERROR: package.json not found in %CD%
    pause
    popd
    PowerShell -Command "Set-MpPreference -DisableRealtimeMonitoring $false" 2>nul
    popd
    exit /b 1
)

echo Running npm run build:win...
call npm run build:win
set BUILD_RESULT=%errorlevel%
popd

echo.
echo [3/3] Re-enabling Windows Defender...
PowerShell -Command "Set-MpPreference -DisableRealtimeMonitoring $false" 2>nul
echo   ✓ Windows Defender re-enabled

echo.
if %BUILD_RESULT%==0 (
    echo ============================================
    echo BUILD SUCCESS!
    echo ============================================
    echo.
    echo Your installer is ready at:
    echo   %~dp0apps\gui\dist\WindowsAI-0.2.0-x64.exe
    echo.
    echo This is the ONE file you distribute to users.
    echo.
    dir "%~dp0apps\gui\dist\*.exe" 2>nul
    echo.
) else (
    echo ============================================
    echo BUILD FAILED (Error code: %BUILD_RESULT%)
    echo ============================================
    echo Check the errors above
    echo.
)

popd
pause
