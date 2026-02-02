#!/bin/bash

echo "============================================"
echo "  Runnerbot Portable Installer for macOS"
echo "============================================"
echo
echo "This will install Runnerbot to any location"
echo "(USB drive, external HDD/SSD, or local folder)"
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

read -p "Enter installation path (e.g., /Volumes/USB/Runnerbot): " INSTALL_PATH

if [ -z "$INSTALL_PATH" ]; then
    echo "Error: No path provided."
    exit 1
fi

if [ -d "$INSTALL_PATH" ]; then
    read -p "Directory exists. Overwrite? (y/n): " CONFIRM
    if [ "$CONFIRM" != "y" ]; then
        echo "Installation cancelled."
        exit 0
    fi
fi

echo
echo "Installing to: $INSTALL_PATH"
echo

mkdir -p "$INSTALL_PATH"

echo "Copying application files..."
cp "$SCRIPT_DIR/app.py" "$INSTALL_PATH/"
cp "$SCRIPT_DIR/index.html" "$INSTALL_PATH/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_PATH/"
cp "$SCRIPT_DIR/install_mac.sh" "$INSTALL_PATH/"
cp "$SCRIPT_DIR/run_mac.sh" "$INSTALL_PATH/"
cp "$SCRIPT_DIR/install_linux.sh" "$INSTALL_PATH/"
cp "$SCRIPT_DIR/run_linux.sh" "$INSTALL_PATH/"
cp "$SCRIPT_DIR/install_windows.bat" "$INSTALL_PATH/"
cp "$SCRIPT_DIR/run_windows.bat" "$INSTALL_PATH/"

mkdir -p "$INSTALL_PATH/models"
mkdir -p "$INSTALL_PATH/library"
mkdir -p "$INSTALL_PATH/data"
mkdir -p "$INSTALL_PATH/static"

if [ -f "$SCRIPT_DIR/static/icon.png" ]; then
    cp "$SCRIPT_DIR/static/icon.png" "$INSTALL_PATH/static/"
fi

if [ -f "$SCRIPT_DIR/README.md" ]; then
    cp "$SCRIPT_DIR/README.md" "$INSTALL_PATH/"
fi

chmod +x "$INSTALL_PATH/install_mac.sh"
chmod +x "$INSTALL_PATH/run_mac.sh"
chmod +x "$INSTALL_PATH/install_linux.sh"
chmod +x "$INSTALL_PATH/run_linux.sh"

echo
echo "Checking for Python..."
if command -v python3 &> /dev/null; then
    read -p "Set up Python environment now? (y/n): " SETUP_ENV
    if [ "$SETUP_ENV" = "y" ]; then
        echo "Creating virtual environment..."
        cd "$INSTALL_PATH"
        python3 -m venv venv
        source venv/bin/activate
        echo "Installing dependencies..."
        pip install --upgrade pip
        pip install -r requirements.txt
        deactivate
        echo "Environment ready!"
    fi
else
    echo "Python 3 not found. Run install_mac.sh on target system."
fi

echo
echo "============================================"
echo "  Installation Complete!"
echo "============================================"
echo
echo "Installed to: $INSTALL_PATH"
echo
echo "To run on any macOS system:"
echo "  1. cd $INSTALL_PATH"
echo "  2. ./run_mac.sh"
echo "  3. Open http://localhost:5000"
echo
echo "The folder is fully portable - copy it anywhere!"
echo
