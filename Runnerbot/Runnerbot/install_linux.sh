#!/bin/bash

echo "==================================="
echo "  Runnerbot - Linux Setup"
echo "==================================="
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.10+ first."
    exit 1
fi

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Creating data directories..."
mkdir -p models
mkdir -p library
mkdir -p data

echo
echo "==================================="
echo "  Installation Complete!"
echo "==================================="
echo
echo "All data stays within this folder."
echo "Safe to run from SSD, HDD, or USB."
echo
echo "To run: ./run_linux.sh"
echo
