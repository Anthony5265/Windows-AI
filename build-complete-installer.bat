@echo off
REM ============================================================================
REM Windows AI Complete All-in-One Installer Builder
REM Builds a single .exe that installs everything: Backend + GUI + Service
REM ============================================================================

echo ==========================================
echo  Building Windows AI All-in-One Installer
echo ==========================================
echo.

REM Step 1: Build backend executable
echo [1/3] Building backend executable with PyInstaller...
echo.
python -m PyInstaller backend_bundle_simple.spec --clean --noconfirm
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Backend build failed!
    pause
    exit /b 1
)
echo Backend build complete!
echo.

REM Step 2: Build GUI installer with backend included
echo [2/3] Building complete installer with electron-builder...
echo.
cd apps\gui
call npm run build:win:x64
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Installer build failed!
    cd ..\..
    pause
    exit /b 1
)
cd ..\..
echo Installer build complete!
echo.

REM Step 3: Show results
echo [3/3] Build complete!
echo.
echo ==========================================
echo  All-in-One Installer Created!
echo ==========================================
echo.
echo Location: apps\gui\dist\WindowsAI-0.2.0-x64.exe
echo.
echo This installer includes:
echo   - Windows AI Backend (FastAPI server)
echo   - Windows AI GUI (Electron app)
echo   - Windows Service setup (NSSM)
echo   - All 6 built-in plugins
echo   - Mesh networking
echo   - Integration layer
echo.
echo Installation will:
echo   1. Install GUI to Program Files
echo   2. Install backend as Windows Service
echo   3. Auto-start backend on boot
echo   4. Create desktop + Start Menu shortcuts
echo   5. Configure Windows Firewall
echo.
echo Ready to distribute!
echo ==========================================
echo.

REM Open dist folder
explorer apps\gui\dist

pause
