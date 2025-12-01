@echo off
REM Create a portable Windows AI package

echo Creating portable Windows AI package...

REM Create output directory
mkdir "WindowsAI-Portable" 2>nul

REM Copy Electron GUI
echo Copying Electron GUI...
xcopy /E /I /Y "apps\gui\dist-packaged\WindowsAI-win32-x64" "WindowsAI-Portable\GUI"

REM Copy Python Backend
echo Copying Python Backend...
xcopy /E /I /Y "dist\WindowsAI" "WindowsAI-Portable\Backend"

REM Create launcher script
echo Creating launcher...
(
echo @echo off
echo echo Starting Windows AI...
echo start "" "GUI\WindowsAI.exe"
echo start "" "Backend\WindowsAI.exe"
) > "WindowsAI-Portable\Launch-WindowsAI.bat"

echo.
echo ========================================
echo Portable package created!
echo ========================================
echo.
echo Location: WindowsAI-Portable\
echo.
echo To distribute:
echo 1. Compress the "WindowsAI-Portable" folder to a ZIP file
echo 2. Share the ZIP file
echo.
echo To run: Double-click Launch-WindowsAI.bat
echo.
pause
