#!/bin/bash

echo "================================================"
echo "  Runnerbot Bootable USB Creator"
echo "================================================"
echo
echo "WARNING: This will create a bootable USB drive"
echo "         with a minimal Linux + Runnerbot"
echo
echo "CAUTION: This will ERASE ALL DATA on the USB!"
echo

if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root (sudo)."
    echo "Usage: sudo ./create_bootable_usb.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Detecting USB drives..."
echo

lsblk -d -o NAME,SIZE,MODEL,TRAN | grep usb || echo "No USB drives detected"

echo
read -p "Enter USB device (e.g., sdb, NOT sdb1): " USB_DEV

if [ -z "$USB_DEV" ]; then
    echo "No device specified. Aborting."
    exit 1
fi

USB_PATH="/dev/$USB_DEV"

if [ ! -b "$USB_PATH" ]; then
    echo "Device $USB_PATH not found!"
    exit 1
fi

echo
echo "WARNING: All data on $USB_PATH will be DESTROYED!"
echo
read -p "Type 'YES' to confirm: " CONFIRM

if [ "$CONFIRM" != "YES" ]; then
    echo "Aborted."
    exit 0
fi

echo
echo "Creating partition table..."
parted -s "$USB_PATH" mklabel msdos
parted -s "$USB_PATH" mkpart primary fat32 1MiB 100%
parted -s "$USB_PATH" set 1 boot on

sleep 2

PART="${USB_PATH}1"
if [ ! -b "$PART" ]; then
    PART="${USB_PATH}p1"
fi

echo "Formatting as FAT32..."
mkfs.vfat -F 32 -n "RUNNERBOT" "$PART"

MOUNT_POINT="/mnt/runnerbot_usb_$$"
mkdir -p "$MOUNT_POINT"
mount "$PART" "$MOUNT_POINT"

echo "Copying Runnerbot files..."
mkdir -p "$MOUNT_POINT/Runnerbot"

cp "$SCRIPT_DIR/app.py" "$MOUNT_POINT/Runnerbot/" 2>/dev/null
cp "$SCRIPT_DIR/index.html" "$MOUNT_POINT/Runnerbot/" 2>/dev/null
cp "$SCRIPT_DIR/requirements.txt" "$MOUNT_POINT/Runnerbot/" 2>/dev/null

cp "$SCRIPT_DIR/install_linux.sh" "$MOUNT_POINT/Runnerbot/" 2>/dev/null
cp "$SCRIPT_DIR/run_linux.sh" "$MOUNT_POINT/Runnerbot/" 2>/dev/null
cp "$SCRIPT_DIR/install_mac.sh" "$MOUNT_POINT/Runnerbot/" 2>/dev/null
cp "$SCRIPT_DIR/run_mac.sh" "$MOUNT_POINT/Runnerbot/" 2>/dev/null
cp "$SCRIPT_DIR/install_windows.bat" "$MOUNT_POINT/Runnerbot/" 2>/dev/null
cp "$SCRIPT_DIR/run_windows.bat" "$MOUNT_POINT/Runnerbot/" 2>/dev/null

mkdir -p "$MOUNT_POINT/Runnerbot/models"
mkdir -p "$MOUNT_POINT/Runnerbot/library"
mkdir -p "$MOUNT_POINT/Runnerbot/data"
mkdir -p "$MOUNT_POINT/Runnerbot/static"

if [ -f "$SCRIPT_DIR/static/icon.png" ]; then
    cp "$SCRIPT_DIR/static/icon.png" "$MOUNT_POINT/Runnerbot/static/"
fi

if [ -f "$SCRIPT_DIR/README.md" ]; then
    cp "$SCRIPT_DIR/README.md" "$MOUNT_POINT/Runnerbot/"
fi

cat > "$MOUNT_POINT/README.txt" << 'EOF'
=====================================
     RUNNERBOT USB DRIVE
=====================================

This USB contains a portable Runnerbot installation.

TO USE:
1. Open the Runnerbot folder
2. Run the installer for your OS:
   - Linux: ./install_linux.sh
   - macOS: ./install_mac.sh
   - Windows: install_windows.bat
3. Then run Runnerbot:
   - Linux: ./run_linux.sh
   - macOS: ./run_mac.sh  
   - Windows: run_windows.bat
4. Open http://localhost:5000

Your models and data stay on this USB!
=====================================
EOF

cat > "$MOUNT_POINT/autorun.inf" << 'EOF'
[autorun]
label=Runnerbot
open=Runnerbot\run_windows.bat
EOF

sync
umount "$MOUNT_POINT"
rmdir "$MOUNT_POINT"

echo
echo "================================================"
echo "  USB Drive Created Successfully!"
echo "================================================"
echo
echo "Your USB drive is ready."
echo "Insert it into any computer and run Runnerbot!"
echo
echo "Note: This is a DATA USB, not a bootable OS."
echo "The computer must have Python 3.10+ installed."
echo
