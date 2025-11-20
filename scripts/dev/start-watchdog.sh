#!/bin/bash
# Start Windows AI Watchdog Service
# This script starts the watchdog service that monitors and auto-restarts the backend

set -e

echo "========================================"
echo "Windows AI Watchdog Service"
echo "========================================"
echo

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is not installed or not in PATH"
    exit 1
fi

# Check if watchdog.py exists
if [ ! -f "watchdog.py" ]; then
    echo "ERROR: watchdog.py not found in $SCRIPT_DIR"
    exit 1
fi

# Install required dependencies if needed
echo "Checking dependencies..."
python3 -c "import psutil, aiohttp" 2>/dev/null || {
    echo "Installing watchdog dependencies..."
    python3 -m pip install psutil aiohttp
}

echo "Starting watchdog service..."
echo "Logs will be written to watchdog.log"
echo "Press Ctrl+C to stop"
echo

# Start watchdog
python3 watchdog.py
