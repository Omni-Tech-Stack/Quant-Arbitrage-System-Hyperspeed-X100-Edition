#!/bin/bash

# Stop script for live operations

set -e

PID_DIR="./pids"

echo "Stopping Quant Arbitrage System..."

# Stop backend
if [ -f "$PID_DIR/backend.pid" ]; then
    pid=$(cat "$PID_DIR/backend.pid")
    if ps -p $pid > /dev/null 2>&1; then
        echo "Stopping backend (PID: $pid)..."
        kill $pid 2>/dev/null || true
        sleep 2
        # Force kill if still running
        if ps -p $pid > /dev/null 2>&1; then
            kill -9 $pid 2>/dev/null || true
        fi
        echo "✓ Backend stopped"
    fi
    rm "$PID_DIR/backend.pid"
fi

# Stop frontend
if [ -f "$PID_DIR/frontend.pid" ]; then
    pid=$(cat "$PID_DIR/frontend.pid")
    if ps -p $pid > /dev/null 2>&1; then
        echo "Stopping frontend (PID: $pid)..."
        kill $pid 2>/dev/null || true
        sleep 2
        # Force kill if still running
        if ps -p $pid > /dev/null 2>&1; then
            kill -9 $pid 2>/dev/null || true
        fi
        echo "✓ Frontend stopped"
    fi
    rm "$PID_DIR/frontend.pid"
fi

echo ""
echo "✓ System stopped successfully"
