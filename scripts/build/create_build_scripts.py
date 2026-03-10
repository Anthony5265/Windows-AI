#!/usr/bin/env python3
"""
Create build scripts for Windows AI
"""

from pathlib import Path

# Create scripts/build directory
scripts_dir = Path(__file__).parent / "scripts" / "build"
scripts_dir.mkdir(parents=True, exist_ok=True)

# Build installer script
installer_script = scripts_dir / "build-installer.bat"
installer_script.write_text(r"""@echo off
REM ============================================================================
REM Windows AI - Installer Build Script
REM Creates the NSIS installer
REM ============================================================================

echo.
echo ============================================================================
echo   WINDOWS AI - INSTALLER BUILD
echo ============================================================================
echo.

cd /d "%~dp0\..\..\"

REM Check if dist\WindowsAI.exe exists
if not exist "dist\WindowsAI.exe" (
    echo [ERROR] WindowsAI.exe not found in dist\
    echo Please build the executable first:
    echo   python build_exe.py
    pause
    exit /b 1
)

REM Check if NSIS is installed
where makensis >nul 2>&1
if errorlevel 1 (
    echo [ERROR] NSIS not found in PATH
    echo.
    echo Please install NSIS from: https://nsis.sourceforge.io/Download
    echo And add it to your PATH, or run from NSIS directory
    pause
    exit /b 1
)

echo [*] Building installer...
echo.

REM Build the installer
cd installer
makensis windows_ai.nsi

if errorlevel 1 (
    echo.
    echo [ERROR] Installer build failed!
    pause
    exit /b 1
)

cd ..

echo.
echo ============================================================================
echo   INSTALLER BUILD COMPLETE!
echo ============================================================================
echo.

if exist "dist\WindowsAI-Setup-2.0.0.exe" (
    echo [SUCCESS] Installer created: dist\WindowsAI-Setup-2.0.0.exe
    echo.
    echo Next steps:
    echo   1. Test the installer on a clean Windows system
    echo   2. Sign the installer: scripts\build\sign-installer.bat
    echo   3. Upload to GitHub Releases
) else (
    echo [ERROR] Installer not found after build
)

echo.
pause
""")

# Build portable script
portable_script = scripts_dir / "create-portable-package.bat"
portable_script.write_text(r"""@echo off
setlocal enabledelayedexpansion

REM ============================================================================
REM Windows AI - Portable Package Creation Script
REM Creates a portable ZIP distribution
REM ============================================================================

echo.
echo ============================================================================
echo   WINDOWS AI - PORTABLE PACKAGE BUILD
echo ============================================================================
echo.

cd /d "%~dp0\..\..\"

REM Check if dist\WindowsAI.exe exists
if not exist "dist\WindowsAI.exe" (
    echo [ERROR] WindowsAI.exe not found in dist\
    echo Please build the executable first:
    echo   python build_exe.py
    pause
    exit /b 1
)

REM Create portable directory
set PORTABLE_DIR=dist\WindowsAI-Portable
set VERSION=2.0.0

echo [*] Creating portable package structure...

REM Clean previous portable build
if exist "%PORTABLE_DIR%" rmdir /s /q "%PORTABLE_DIR%"
mkdir "%PORTABLE_DIR%"

REM Copy executable
echo [*] Copying executable...
copy "dist\WindowsAI.exe" "%PORTABLE_DIR%\"

REM Copy documentation
echo [*] Copying documentation...
copy "README.md" "%PORTABLE_DIR%\"
copy "LICENSE" "%PORTABLE_DIR%\"

REM Copy checksums
if exist "dist\WindowsAI.sha256" copy "dist\WindowsAI.sha256" "%PORTABLE_DIR%\"

REM Create portable config
echo [*] Creating portable configuration...
mkdir "%PORTABLE_DIR%\config"
mkdir "%PORTABLE_DIR%\data"
mkdir "%PORTABLE_DIR%\logs"
mkdir "%PORTABLE_DIR%\plugins"
mkdir "%PORTABLE_DIR%\models"

echo PORTABLE=true > "%PORTABLE_DIR%\portable.txt"

echo [*] Creating ZIP archive...

REM Try 7-Zip first
where 7z >nul 2>&1
if not errorlevel 1 (
    echo [*] Using 7-Zip...
    7z a -tzip -mx=9 "dist\WindowsAI-v%VERSION%-Portable.zip" ".\%PORTABLE_DIR%\*"
    goto :check_result
)

REM Try PowerShell
echo [*] Using PowerShell...
powershell -Command "Compress-Archive -Path '%PORTABLE_DIR%\*' -DestinationPath 'dist\WindowsAI-v%VERSION%-Portable.zip' -Force"

:check_result
if exist "dist\WindowsAI-v%VERSION%-Portable.zip" (
    echo.
    echo ============================================================================
    echo   PORTABLE PACKAGE BUILD COMPLETE!
    echo ============================================================================
    echo.
    echo [SUCCESS] Portable package created
    echo.
) else (
    echo [ERROR] ZIP archive creation failed!
)

pause
""")

print(f"Created: {installer_script}")
print(f"Created: {portable_script}")

print("\nBuild scripts created successfully!")
