@echo off
echo ========================================
echo EMERGENCY CLEANUP AND RESTART
echo ========================================
echo.

echo Killing all PowerShell background jobs...
taskkill /F /IM powershell.exe /T >nul 2>&1

echo Waiting 3 seconds...
timeout /t 3 /nobreak >nul

echo.
echo Starting supervised swarm (10 agents max)...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\antho\Windows-AI\SUPERVISED_SWARM.ps1"

echo.
echo Done!
pause
