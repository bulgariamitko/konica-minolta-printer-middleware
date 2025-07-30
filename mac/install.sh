#!/bin/bash
# Konica Minolta Printer Middleware - macOS Installer
# Run this script to install the middleware service

set -e  # Exit on any error

echo "========================================================="
echo "  KONICA MINOLTA PRINTER MIDDLEWARE - macOS INSTALLER"
echo "========================================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 is not installed"
    echo
    echo "Please install Python 3.8+ from:"
    echo "  - https://python.org"
    echo "  - Or use Homebrew: brew install python"
    echo
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" 2>/dev/null; then
    echo "❌ ERROR: Python 3.8+ is required"
    echo "Your Python version: $python_version"
    echo
    exit 1
fi

echo "✅ [1/4] Python $python_version found"

# Change to the project root directory (parent of mac/)
cd "$(dirname "$0")/.."

echo "📂 Working directory: $(pwd)"

# Install dependencies
echo
echo "📦 [2/4] Installing Python dependencies..."
python3 -m pip install -r requirements.txt

# Install the service
echo
echo "🔧 [3/4] Installing middleware service..."
python3 lib/install_service.py install

# Set up system tray
echo
echo "🖥️ [4/4] Setting up system tray..."
python3 lib/system_tray.py --add-startup

echo
echo "========================================================="
echo "  🎉 INSTALLATION COMPLETED SUCCESSFULLY!"
echo "========================================================="
echo
echo "What's installed:"
echo "  🔧 LaunchAgent: com.konicaminolta.middleware"
echo "  🖥️ Menu Bar App: Auto-starts with macOS"
echo "  🌐 Web Interface: http://localhost:8000"
echo
echo "🚀 Starting menu bar application..."
python3 lib/system_tray.py &

echo
echo "👀 Look for the printer icon in your menu bar!"
echo "✅ Installation complete!"