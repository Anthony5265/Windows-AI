#!/bin/bash

###############################################################################
# Windows AI Tray Starter
# Starts the system tray application
###############################################################################

set -e

echo "=========================================="
echo "Starting Windows AI Tray"
echo "=========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TRAY_DIR="$SCRIPT_DIR/windows-ai-tray"

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    echo "Please install Node.js 18 or higher"
    exit 1
fi

# Navigate to tray directory
cd "$TRAY_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "⚠ Installing tray dependencies..."
    npm install || {
        echo "❌ Failed to install dependencies"
        exit 1
    }
fi

echo "✓ Dependencies installed"
echo ""

# Check if backend is running
echo "Checking backend connection..."
if curl -s http://localhost:8010/health &> /dev/null; then
    echo "✓ Backend is online"
else
    echo "⚠ Warning: Backend is not responding"
    echo "  Start the backend first with: ./start-backend.sh"
    echo "  Tray will show offline until backend starts"
fi

echo ""
echo "Starting System Tray..."
echo "Global shortcut: Ctrl+Shift+Space for quick command"
echo "=========================================="
echo ""

# Start the tray
npm start
