@echo off
setlocal
set RUNTIME_NODE="%~dp0..\..\runtime\node\node.exe"
if exist %RUNTIME_NODE% (
  %RUNTIME_NODE% "%~dp0proxy.js"
) else (
  node "%~dp0proxy.js"
)
