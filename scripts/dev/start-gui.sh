#!/bin/bash

###############################################################################
# Windows AI GUI Starter
# Starts the Electron chat GUI
###############################################################################

set -e

echo "=========================================="
echo "Starting Windows AI GUI"
echo "=========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
GUI_DIR="$SCRIPT_DIR/apps/gui"

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    echo "Please install Node.js 18 or higher"
    exit 1
fi

# Check Node version
NODE_VERSION=$(node --version)
echo "✓ Node version: $NODE_VERSION"

# Navigate to GUI directory
cd "$GUI_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "⚠ Installing GUI dependencies..."
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
    echo "  Continuing anyway..."
fi

echo ""
echo "Starting Electron GUI..."
echo "=========================================="
echo ""

# Start the GUI
npm start
