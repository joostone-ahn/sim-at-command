#!/bin/bash
# SIM AT Command Tool - One-click launcher (macOS/Linux)
set -e

echo ""
echo "╔══════════════════════════════════════╗"
echo "║  SIM AT Command Tool -- Web UI       ║"
echo "╚══════════════════════════════════════╝"
echo ""

DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/.venv"
PORT=8083
URL="http://127.0.0.1:$PORT"
PYTHON="$VENV/bin/python"
PIP="$VENV/bin/pip"
REQ="$DIR/requirements.txt"
REQ_HASH_FILE="$VENV/.req_hash"

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Python3 not found. Please install Python 3.10+"
    exit 1
fi

# Create venv if needed
if [ ! -f "$PYTHON" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV"
fi

# Install/update dependencies if requirements.txt changed
CURRENT_HASH=$(md5 -q "$REQ" 2>/dev/null || md5sum "$REQ" | cut -d' ' -f1)
SAVED_HASH=""
if [ -f "$REQ_HASH_FILE" ]; then
    SAVED_HASH=$(cat "$REQ_HASH_FILE")
fi
if [ "$CURRENT_HASH" != "$SAVED_HASH" ]; then
    echo "📦 Installing dependencies..."
    cd "$DIR"
    "$PIP" install -q --disable-pip-version-check -r "$REQ"
    echo "$CURRENT_HASH" > "$REQ_HASH_FILE"
fi

# Kill existing process on port
EXISTING=$(lsof -ti:$PORT 2>/dev/null || true)
if [ -n "$EXISTING" ]; then
    echo "[INIT] Killing existing process on port $PORT (PID $EXISTING)"
    kill -9 $EXISTING 2>/dev/null || true
    sleep 1
fi

# Open browser after short delay
(sleep 2 && open "$URL" 2>/dev/null || xdg-open "$URL" 2>/dev/null || echo "🌐 Open $URL in your browser") &

# Start server
echo "🚀 Starting SIM AT Command Tool at $URL"
PYTHONDONTWRITEBYTECODE=1 "$PYTHON" "$DIR/src/app.py"
