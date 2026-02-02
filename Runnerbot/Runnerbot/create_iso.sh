#!/bin/bash

echo "================================================"
echo "  Runnerbot ISO Creator"
echo "================================================"
echo
echo "This creates an ISO image containing Runnerbot"
echo "that can be burned to CD/DVD or mounted."
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISO_DIR="/tmp/runnerbot_iso_$$"
ISO_NAME="Runnerbot.iso"

read -p "Output ISO filename [$ISO_NAME]: " CUSTOM_NAME
if [ -n "$CUSTOM_NAME" ]; then
    ISO_NAME="$CUSTOM_NAME"
fi

if ! command -v genisoimage &> /dev/null && ! command -v mkisofs &> /dev/null; then
    echo
    echo "ERROR: genisoimage or mkisofs is required."
    echo
    echo "Install on Debian/Ubuntu: sudo apt install genisoimage"
    echo "Install on Fedora/RHEL:   sudo dnf install genisoimage"
    echo "Install on macOS:         brew install cdrtools"
    echo
    exit 1
fi

echo "Creating ISO directory structure..."
mkdir -p "$ISO_DIR/Runnerbot"

echo "Copying application files..."
cp "$SCRIPT_DIR/app.py" "$ISO_DIR/Runnerbot/" 2>/dev/null
cp "$SCRIPT_DIR/index.html" "$ISO_DIR/Runnerbot/" 2>/dev/null
cp "$SCRIPT_DIR/requirements.txt" "$ISO_DIR/Runnerbot/" 2>/dev/null

cp "$SCRIPT_DIR/install_linux.sh" "$ISO_DIR/Runnerbot/" 2>/dev/null
cp "$SCRIPT_DIR/run_linux.sh" "$ISO_DIR/Runnerbot/" 2>/dev/null
cp "$SCRIPT_DIR/install_mac.sh" "$ISO_DIR/Runnerbot/" 2>/dev/null
cp "$SCRIPT_DIR/run_mac.sh" "$ISO_DIR/Runnerbot/" 2>/dev/null
cp "$SCRIPT_DIR/install_windows.bat" "$ISO_DIR/Runnerbot/" 2>/dev/null
cp "$SCRIPT_DIR/run_windows.bat" "$ISO_DIR/Runnerbot/" 2>/dev/null

mkdir -p "$ISO_DIR/Runnerbot/models"
mkdir -p "$ISO_DIR/Runnerbot/library"
mkdir -p "$ISO_DIR/Runnerbot/data"
mkdir -p "$ISO_DIR/Runnerbot/static"

if [ -f "$SCRIPT_DIR/static/icon.png" ]; then
    cp "$SCRIPT_DIR/static/icon.png" "$ISO_DIR/Runnerbot/static/"
fi

if [ -f "$SCRIPT_DIR/README.md" ]; then
    cp "$SCRIPT_DIR/README.md" "$ISO_DIR/Runnerbot/"
fi

cat > "$ISO_DIR/README.txt" << 'EOF'
=====================================
     RUNNERBOT - AI MODEL RUNNER
=====================================

Copy the "Runnerbot" folder to your computer,
then follow the instructions in that folder.

QUICK START:
------------
1. Copy Runnerbot folder to your drive
2. Run the installer for your OS:
   - Linux: ./install_linux.sh
   - macOS: ./install_mac.sh
   - Windows: install_windows.bat
3. Run Runnerbot:
   - Linux: ./run_linux.sh
   - macOS: ./run_mac.sh
   - Windows: run_windows.bat
4. Open http://localhost:5000

REQUIREMENTS:
- Python 3.10+
- Internet for first-time setup

=====================================
EOF

cat > "$ISO_DIR/autorun.inf" << 'EOF'
[autorun]
label=Runnerbot
icon=Runnerbot\static\icon.ico
open=Runnerbot\run_windows.bat
EOF

chmod +x "$ISO_DIR/Runnerbot"/*.sh 2>/dev/null

echo "Creating ISO image..."
if command -v genisoimage &> /dev/null; then
    genisoimage -o "$SCRIPT_DIR/$ISO_NAME" -V "RUNNERBOT" -R -J "$ISO_DIR"
elif command -v mkisofs &> /dev/null; then
    mkisofs -o "$SCRIPT_DIR/$ISO_NAME" -V "RUNNERBOT" -R -J "$ISO_DIR"
fi

rm -rf "$ISO_DIR"

if [ -f "$SCRIPT_DIR/$ISO_NAME" ]; then
    SIZE=$(du -h "$SCRIPT_DIR/$ISO_NAME" | cut -f1)
    echo
    echo "================================================"
    echo "  ISO Created Successfully!"
    echo "================================================"
    echo
    echo "File: $SCRIPT_DIR/$ISO_NAME"
    echo "Size: $SIZE"
    echo
    echo "You can:"
    echo "  - Burn to CD/DVD"
    echo "  - Mount as virtual drive"
    echo "  - Write to USB with: dd if=$ISO_NAME of=/dev/sdX"
    echo
else
    echo
    echo "ERROR: Failed to create ISO"
    exit 1
fi
