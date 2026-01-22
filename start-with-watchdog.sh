#!/bin/bash
# Startup script for nutrition-pad with watchdog monitoring

# Configuration
HOST="${NUTRITION_HOST:-0.0.0.0}"
PORT="${NUTRITION_PORT:-5001}"
PIDFILE="/tmp/nutrition-pad.pid"
WATCHDOG_LOG="/tmp/nutrition-pad-watchdog.log"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
if [ -d "$SCRIPT_DIR/.venv-release" ]; then
    source "$SCRIPT_DIR/.venv-release/bin/activate"
    echo "Using virtual environment: .venv-release"
elif [ -d "$SCRIPT_DIR/.venv" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
    echo "Using virtual environment: .venv"
else
    echo "Warning: No virtual environment found, using system Python"
fi

echo "Starting Nutrition Pad with watchdog..."
echo "Host: $HOST"
echo "Port: $PORT"
echo "PID file: $PIDFILE"
echo "Watchdog log: $WATCHDOG_LOG"

# Stop any existing instances
if [ -f "$PIDFILE" ]; then
    OLD_PID=$(cat "$PIDFILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Stopping existing server (PID: $OLD_PID)"
        kill "$OLD_PID"
        sleep 2
    fi
    rm -f "$PIDFILE"
fi

# Kill any existing watchdog
pkill -f "python.*watchdog.py" || true
sleep 1

# Start the server in the background
echo "Starting nutrition-pad server..."
cd "$SCRIPT_DIR"
python3 -m nutrition_pad.main --host "$HOST" --port "$PORT" --pidfile "$PIDFILE" > /tmp/nutrition-pad.log 2>&1 &
SERVER_PID=$!

# Wait a bit for server to start
sleep 3

# Check if server started successfully
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "ERROR: Server failed to start. Check /tmp/nutrition-pad.log"
    exit 1
fi

echo "Server started with PID: $SERVER_PID"

# Start the watchdog
echo "Starting watchdog..."
python3 "$SCRIPT_DIR/watchdog.py" \
    --url "http://localhost:$PORT/heartbeat" \
    --timeout 60 \
    --check-interval 15 \
    --pidfile "$PIDFILE" \
    > "$WATCHDOG_LOG" 2>&1 &

WATCHDOG_PID=$!
echo "Watchdog started with PID: $WATCHDOG_PID"

echo ""
echo "Nutrition Pad is running!"
echo "  Server URL: http://$HOST:$PORT"
echo "  Server PID: $SERVER_PID"
echo "  Watchdog PID: $WATCHDOG_PID"
echo "  Server log: /tmp/nutrition-pad.log"
echo "  Watchdog log: $WATCHDOG_LOG"
echo ""
echo "To stop:"
echo "  kill $SERVER_PID $WATCHDOG_PID"
echo "  # or"
echo "  pkill -f 'nutrition_pad.main' && pkill -f 'watchdog.py'"
