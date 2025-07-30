@echo off
REM Start the Konica Minolta Middleware System Tray Application

title Konica Minolta Middleware - System Tray

echo =========================================================
echo   KONICA MINOLTA MIDDLEWARE - SYSTEM TRAY LAUNCHER
echo =========================================================
echo.
echo Starting Konica Minolta Middleware System Tray...
echo.

REM Change to the project root directory (parent of win/)
cd /d "%~dp0\.."

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and make sure it's in your PATH
    echo.
    pause
    exit /b 1
)

echo ^🚀 Starting Konica Minolta Middleware Menu Bar App...
echo ^👀 Look for the printer icon in your system tray!
echo.

REM Start the system tray application
python lib\system_tray.py

REM If we get here, the tray app exited
echo.
echo ^👋 System tray application has stopped.
pause