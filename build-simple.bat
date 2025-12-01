@echo off
REM Simple Windows AI Build Script
REM This script creates a portable build without full installer

echo ========================================
echo Building Windows AI - Simple Build
echo ========================================

REM Step 1: Build Python Backend
echo.
echo [1/2] Building Python backend...
cd /d "%~dp0"
python build_exe.py
if errorlevel 1 (
    echo ERROR: Python backend build failed!
    pause
    exit /b 1
)

REM Step 2: Package Electron App
echo.
echo [2/2] Packaging Electron app...
cd apps\gui
call npx electron-packager . WindowsAI --platform=win32 --arch=x64 --out=../../dist-simple --overwrite --icon=build/icon.ico --asar

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Python Backend: dist\WindowsAI\
echo Electron GUI: dist-simple\WindowsAI-win32-x64\
echo.
echo To create a portable package, compress the contents of both directories together.
echo.
pause
