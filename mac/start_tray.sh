#!/bin/bash
# Start the Konica Minolta Middleware Menu Bar Application

echo "🚀 Starting Konica Minolta Middleware Menu Bar App..."
echo "👀 Look for the printer icon in your menu bar!"

# Change to the project root directory (parent of mac/)
cd "$(dirname "$0")/.."

# Start the menu bar application
python3 lib/system_tray.py

# If we get here, the menu bar app exited
echo
echo "Menu bar application has stopped."