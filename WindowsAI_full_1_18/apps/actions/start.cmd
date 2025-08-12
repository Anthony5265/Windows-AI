@echo off
setlocal
set RUNTIME_NODE="%~dp0..\..\runtime\node\node.exe"
if exist %RUNTIME_NODE% (
  %RUNTIME_NODE% "%~dp0server.js"
) else (
  node "%~dp0server.js"
)
