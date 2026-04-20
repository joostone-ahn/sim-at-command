#!/bin/bash
# SIM AT Command Tool - One-click launcher (macOS/Linux)
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/.venv"
PORT=8083
URL="http://127.0.0.1:$PORT"
PYTHON="$VENV/bin/python"
PIP="$VENV/bin/pip"

# Kill existing process on port
EXISTING=$(lsof -ti:$PORT 2>/dev/null || true)
if [ -n "$EXISTING" ]; then
    echo "[INIT] Killing existing process on port $PORT (PID $EXISTING)"
    kill -9 $EXISTING 2>/dev/null || true
    sleep 1
fi

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

# Install dependencies
if ! "$PYTHON" -c "import flask, serial, pySim" &>/dev/null; then
    echo "📦 Installing dependencies..."
    "$PIP" install -q --disable-pip-version-check -r "$DIR/requirements.txt"
    "$PIP" install -q --disable-pip-version-check -e "$DIR/pysim"
fi

# Open browser after short delay
(sleep 2 && open "$URL" 2>/dev/null || xdg-open "$URL" 2>/dev/null || echo "🌐 Open $URL in your browser") &

# Start server
echo "🚀 Starting SIM AT Command Tool at $URL"
PYTHONDONTWRITEBYTECODE=1 "$PYTHON" "$DIR/src/app.py"
