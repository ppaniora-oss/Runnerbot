#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running installer..."
    ./install_mac.sh
fi

echo "Starting Runnerbot..."
source venv/bin/activate
python app.py
