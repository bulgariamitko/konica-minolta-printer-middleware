#!/bin/bash
# Konica Minolta Printer Middleware - macOS Uninstaller
# Run this script to uninstall the middleware service

set -e  # Exit on any error

echo "==========================================================="
echo "  KONICA MINOLTA PRINTER MIDDLEWARE - macOS UNINSTALLER"
echo "==========================================================="
echo
echo "This will completely remove:"
echo "  🔧 LaunchAgent service"
echo "  🖥️ Menu bar application"
echo "  🚀 Startup entries"
echo

read -p "Are you sure you want to uninstall? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "⚠️ WARNING: Python 3 is not installed"
    echo
    echo "Manual removal required:"
    echo "1. Remove: ~/Library/LaunchAgents/com.konicaminolta.middleware.plist"
    echo "2. Remove: ~/Library/LaunchAgents/com.konicaminolta.middleware.tray.plist"
    echo "3. Run: launchctl unload ~/Library/LaunchAgents/com.konicaminolta.middleware*.plist"
    echo
    exit 1
fi

# Change to the project root directory (parent of mac/)
cd "$(dirname "$0")/.."

echo "🗑️ [1/2] Removing menu bar app from startup..."
python3 lib/system_tray.py --remove-startup || true

echo
echo "🗑️ [2/2] Uninstalling LaunchAgent service..."
python3 lib/install_service.py uninstall || true

echo
echo "==========================================================="
echo "  ✅ UNINSTALLATION COMPLETED"
echo "==========================================================="
echo
echo "The Konica Minolta Middleware has been removed from your system."