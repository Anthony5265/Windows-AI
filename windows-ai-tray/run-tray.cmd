@echo off
setlocal
cd /d "%~dp0"
set "ELECTRON_DISABLE_GPU=1"
set "ELECTRON_ENABLE_LOGGING=1"
set "ELECTRON_ENABLE_STACK_DUMPING=1"
echo [%date% %time%] starting>>"%~dp0tray-task.log"
set "NODE=C:\Program Files\nodejs\node.exe"
set "CLI=C:\Users\antho\Documents\GitHub\Windows-AI\windows-ai-tray\node_modules\electron\cli.js"
"%NODE%" "%CLI%" . >> "%~dp0tray-task.log" 2>&1
