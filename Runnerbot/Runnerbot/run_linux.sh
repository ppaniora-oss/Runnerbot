#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==================================="
echo "  Runnerbot - Self-Contained Mode"
echo "==================================="
echo

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running installer first..."
    bash install_linux.sh
fi

source venv/bin/activate

export RUNNERBOT_HOME="$SCRIPT_DIR"

echo "Running from: $SCRIPT_DIR"
echo "All data stored in this folder only."
echo
echo "Server starting at http://localhost:5000"
echo "Press Ctrl+C to stop"
echo

python app.py
