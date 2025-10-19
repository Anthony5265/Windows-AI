@echo off
setlocal
set RUNTIME_PY="%~dp0..\..\runtime\python\python.exe"
if exist %RUNTIME_PY% (
  %RUNTIME_PY% "%~dp0main.py"
) else (
  python "%~dp0main.py"
)
