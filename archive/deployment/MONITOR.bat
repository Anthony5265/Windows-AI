@echo off
title PLUGIN GENERATION MONITOR
color 0A

:monitor
cls
echo ============================================================
echo            MASSIVE PLUGIN GENERATION IN PROGRESS
echo ============================================================
echo.
echo Time: %TIME%
echo.

cd /d C:\Users\antho\Windows-AI\plugins

echo Counting plugins in each category...
echo.

set total=0

for /d %%d in (*) do (
    if exist "%%d\*.py" (
        for /f %%c in ('dir /b "%%d\*.py" 2^>nul ^| find /c /v ""') do (
            set /a total+=%%c
            echo [%%d] %%c plugins
        )
    )
)

echo.
echo ============================================================
echo TOTAL PLUGINS: %total% / 1,520
set /a percent=(%total%*100)/1520
echo PROGRESS: %percent%%%
echo ============================================================
echo.
echo Refreshing in 30 seconds...
timeout /t 30 /nobreak >nul
goto monitor
