#!/bin/bash

###############################################################################
# Windows AI Complete Starter
# Starts all components: Backend, GUI, and Tray
###############################################################################

set -e

echo "=========================================="
echo "🚀 Starting Windows AI - Complete System"
echo "=========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Make scripts executable
chmod +x start-backend.sh start-gui.sh start-tray.sh

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "Shutting down Windows AI..."
    kill $BACKEND_PID $GUI_PID $TRAY_PID 2>/dev/null || true
    wait
    echo "✓ All services stopped"
    exit 0
}

trap cleanup EXIT INT TERM

echo "Starting services..."
echo ""

# Start backend in background
echo "1️⃣  Starting Backend..."
./start-backend.sh > backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
echo "   Logs: backend.log"

# Wait for backend to be ready
echo "   Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8010/health &> /dev/null; then
        echo "   ✓ Backend is online"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "   ❌ Backend failed to start"
        cat backend.log
        exit 1
    fi
done

sleep 2

# Start tray in background
echo ""
echo "2️⃣  Starting System Tray..."
./start-tray.sh > tray.log 2>&1 &
TRAY_PID=$!
echo "   Tray PID: $TRAY_PID"
echo "   Logs: tray.log"

sleep 2

# Start GUI in background
echo ""
echo "3️⃣  Starting GUI..."
./start-gui.sh > gui.log 2>&1 &
GUI_PID=$!
echo "   GUI PID: $GUI_PID"
echo "   Logs: gui.log"

echo ""
echo "=========================================="
echo "✅ Windows AI is running!"
echo "=========================================="
echo ""
echo "Services:"
echo "  🔧 Backend:    http://localhost:8010"
echo "  💬 Chat GUI:   Opening in Electron..."
echo "  🔔 Tray:       Check system tray (bottom-right)"
echo ""
echo "Quick Actions:"
echo "  • Ctrl+Shift+Space : Quick command"
echo "  • Double-click tray: Open chat"
echo "  • Right-click tray : Menu"
echo ""
echo "Logs:"
echo "  • Backend: tail -f backend.log"
echo "  • GUI:     tail -f gui.log"
echo "  • Tray:    tail -f tray.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=========================================="
echo ""

# Wait for all background processes
wait
