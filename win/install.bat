@echo off
REM Konica Minolta Printer Middleware - Windows Installer
REM Double-click this file to install the middleware service

title Konica Minolta Middleware - Windows Installer

echo =========================================================
echo   KONICA MINOLTA PRINTER MIDDLEWARE - WINDOWS INSTALLER
echo =========================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo [1/4] Python found. Checking version...
python -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" 2>nul
if errorlevel 1 (
    echo ERROR: Python 3.8+ is required
    echo Your Python version:
    python --version
    echo.
    pause
    exit /b 1
)

echo [2/4] Python version OK. Starting installation...
echo.

REM Change to the project root directory (parent of win/)
cd /d "%~dp0\.."

REM Run the Python installer
echo [3/4] Installing middleware service...
python lib\install_service.py install
if errorlevel 1 (
    echo.
    echo ERROR: Service installation failed
    echo Check the error messages above
    pause
    exit /b 1
)

echo.
echo [4/4] Setting up system tray...
python lib\system_tray.py --add-startup
if errorlevel 1 (
    echo.
    echo WARNING: System tray setup had issues
    echo The service is installed but tray app may need manual setup
)

echo.
echo =========================================================
echo   INSTALLATION COMPLETED SUCCESSFULLY!
echo =========================================================
echo.
echo What's installed:
echo   - Windows Service: "konica-minolta-middleware"
echo   - System Tray App: Auto-starts with Windows
echo   - Web Interface: http://localhost:8000
echo.
echo Starting system tray application...
start "" python lib\system_tray.py

echo.
echo Look for the printer icon in your system tray!
echo.
pause