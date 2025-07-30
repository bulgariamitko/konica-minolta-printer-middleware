@echo off
REM Konica Minolta Printer Middleware - Windows Uninstaller
REM Double-click this file to uninstall the middleware service

title Konica Minolta Middleware - Windows Uninstaller

echo ===========================================================
echo   KONICA MINOLTA PRINTER MIDDLEWARE - WINDOWS UNINSTALLER
echo ===========================================================
echo.
echo This will completely remove:
echo   - Windows Service
echo   - System Tray Application
echo   - Startup entries
echo.
set /p confirm="Are you sure you want to uninstall? (y/N): "
if /i not "%confirm%"=="y" (
    echo Uninstallation cancelled.
    pause
    exit /b 0
)

echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Cannot run uninstaller scripts
    echo.
    echo Manual removal required:
    echo 1. Open Services.msc
    echo 2. Stop and delete "konica-minolta-middleware" service
    echo 3. Remove startup entries from Task Manager
    echo.
    pause
    exit /b 1
)

REM Change to the project root directory (parent of win/)
cd /d "%~dp0\.."

echo [1/2] Removing system tray from startup...
python lib\system_tray.py --remove-startup

echo.
echo [2/2] Uninstalling Windows service...
python lib\install_service.py uninstall
if errorlevel 1 (
    echo.
    echo WARNING: Service uninstall had issues
    echo You may need to manually remove the service
)

echo.
echo ===========================================================
echo   UNINSTALLATION COMPLETED
echo ===========================================================
echo.
echo The Konica Minolta Middleware has been removed from your system.
echo.
pause