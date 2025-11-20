@echo off
REM ============================================================================
REM Windows AI Backend Starter (Windows)
REM Starts the FastAPI backend service
REM ============================================================================

echo ==========================================
echo Starting Windows AI Backend
echo ==========================================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed
    echo Please install Python 3.11 or higher
    pause
    exit /b 1
)

REM Display Python version
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✓ Python version: %PYTHON_VERSION%

REM Check if dependencies are installed
python -c "import fastapi" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ⚠ Installing dependencies...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
)

echo ✓ Dependencies installed
echo.

REM Check for API keys
if "%OPENAI_API_KEY%"=="" if "%ANTHROPIC_API_KEY%"=="" (
    echo ⚠ Warning: No API keys detected
    echo   Set OPENAI_API_KEY or ANTHROPIC_API_KEY to use cloud models
    echo   Or install Ollama for local models
    echo.
)

REM Set default host and port
if "%HOST%"=="" set HOST=0.0.0.0
if "%PORT%"=="" set PORT=8010

echo Starting backend on %HOST%:%PORT%
echo.
echo Backend will be available at:
echo   http://localhost:%PORT%
echo   http://127.0.0.1:%PORT%
echo.
echo Press Ctrl+C to stop
echo ==========================================
echo.

REM Start with uvicorn
python -m uvicorn windows_ai.main:app --host %HOST% --port %PORT% --reload --log-level info

pause
