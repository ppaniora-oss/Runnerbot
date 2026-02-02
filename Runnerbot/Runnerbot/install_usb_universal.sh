#!/bin/bash

echo "================================================"
echo "  Runnerbot Universal USB/Portable Installer"
echo "================================================"
echo
echo "This creates a portable Runnerbot that works on:"
echo "  - Linux (any distro)"
echo "  - macOS"
echo "  - Windows (via included .bat files)"
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Detected USB/External drives:"
echo

if [[ "$OSTYPE" == "darwin"* ]]; then
    ls -1 /Volumes/ 2>/dev/null | grep -v "Macintosh HD" | while read drive; do
        echo "  /Volumes/$drive"
    done
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    ls -1 /media/$USER/ 2>/dev/null | while read drive; do
        echo "  /media/$USER/$drive"
    done
    ls -1 /mnt/ 2>/dev/null | while read drive; do
        echo "  /mnt/$drive"
    done
fi

echo
read -p "Enter installation path: " INSTALL_PATH

if [ -z "$INSTALL_PATH" ]; then
    echo "Error: No path provided."
    exit 1
fi

INSTALL_PATH="${INSTALL_PATH}/Runnerbot"

if [ -d "$INSTALL_PATH" ]; then
    read -p "Directory exists. Overwrite? (y/n): " CONFIRM
    if [ "$CONFIRM" != "y" ]; then
        echo "Installation cancelled."
        exit 0
    fi
    rm -rf "$INSTALL_PATH"
fi

echo
echo "Installing to: $INSTALL_PATH"
echo

mkdir -p "$INSTALL_PATH"

echo "Copying application files..."
cp "$SCRIPT_DIR/app.py" "$INSTALL_PATH/" 2>/dev/null || echo "  app.py not found"
cp "$SCRIPT_DIR/index.html" "$INSTALL_PATH/" 2>/dev/null || echo "  index.html not found"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_PATH/" 2>/dev/null || echo "  requirements.txt not found"

cp "$SCRIPT_DIR/install_linux.sh" "$INSTALL_PATH/" 2>/dev/null
cp "$SCRIPT_DIR/run_linux.sh" "$INSTALL_PATH/" 2>/dev/null
cp "$SCRIPT_DIR/install_mac.sh" "$INSTALL_PATH/" 2>/dev/null
cp "$SCRIPT_DIR/run_mac.sh" "$INSTALL_PATH/" 2>/dev/null
cp "$SCRIPT_DIR/install_windows.bat" "$INSTALL_PATH/" 2>/dev/null
cp "$SCRIPT_DIR/run_windows.bat" "$INSTALL_PATH/" 2>/dev/null

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

chmod +x "$INSTALL_PATH"/*.sh 2>/dev/null

cat > "$INSTALL_PATH/PORTABLE_README.txt" << 'EOF'
=====================================
  RUNNERBOT PORTABLE INSTALLATION
=====================================

This is a portable installation of Runnerbot.
It works on Linux, macOS, and Windows.

FIRST TIME SETUP:
-----------------
Linux:   ./install_linux.sh
macOS:   ./install_mac.sh  
Windows: install_windows.bat

RUNNING:
--------
Linux:   ./run_linux.sh
macOS:   ./run_mac.sh
Windows: run_windows.bat

Then open: http://localhost:5000

REQUIREMENTS:
-------------
- Python 3.10 or higher
- Internet connection for first install (downloads packages)

PORTABLE DATA:
--------------
All your data is stored in these folders:
- models/   - Your AI models
- library/  - Your documents
- data/     - Settings, memory, skills

Copy this entire folder to move everything!
EOF

echo
echo "================================================"
echo "  Installation Complete!"
echo "================================================"
echo
echo "Installed to: $INSTALL_PATH"
echo
echo "USAGE:"
echo "  Linux:   cd $INSTALL_PATH && ./run_linux.sh"
echo "  macOS:   cd $INSTALL_PATH && ./run_mac.sh"
echo "  Windows: Open folder, run run_windows.bat"
echo
echo "This USB/drive is now portable across all systems!"
echo
