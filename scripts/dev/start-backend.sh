#!/bin/bash

###############################################################################
# Windows AI Backend Starter
# Starts the FastAPI backend service
###############################################################################

set -e

echo "=========================================="
echo "Starting Windows AI Backend"
echo "=========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Check if requirements are installed
echo "Checking dependencies..."
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "⚠ Installing dependencies..."
    pip install -r requirements.txt || {
        echo "❌ Failed to install dependencies"
        exit 1
    }
fi

echo "✓ Dependencies installed"
echo ""

# Set environment variables if needed
# export OPENAI_API_KEY="your-key-here"
# export ANTHROPIC_API_KEY="your-key-here"

# Check for API keys
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠ Warning: No API keys detected"
    echo "  Set OPENAI_API_KEY or ANTHROPIC_API_KEY to use cloud models"
    echo "  Or install Ollama for local models"
    echo ""
fi

# Start the backend
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8010}"

echo "Starting backend on $HOST:$PORT"
echo ""
echo "Backend will be available at:"
echo "  http://localhost:$PORT"
echo "  http://127.0.0.1:$PORT"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

# Start with uvicorn
python3 -m uvicorn windows_ai.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --reload \
    --log-level info
