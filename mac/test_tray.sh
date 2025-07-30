#!/bin/bash
# Test the Konica Minolta Middleware Menu Bar Application

echo "========================================================="
echo "  KONICA MINOLTA MIDDLEWARE - MENU BAR TEST"
echo "========================================================="
echo
echo "This will test the menu bar application for 10 seconds."
echo "👀 Look for the printer icon in your menu bar!"
echo
read -p "Press Enter to start the test..."

# Change to the project root directory (parent of mac/)
cd "$(dirname "$0")/.."

# Run the tray test
python3 lib/test_tray.py

echo
echo "✅ Test completed!"