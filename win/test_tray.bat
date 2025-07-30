@echo off
REM Test the Konica Minolta Middleware System Tray Application

title Konica Minolta Middleware - Tray Test

echo =========================================================
echo   KONICA MINOLTA MIDDLEWARE - SYSTEM TRAY TEST
echo =========================================================
echo.
echo This will test the system tray application for 10 seconds.
echo Look for the printer icon in your system tray!
echo.
pause

REM Change to the project root directory (parent of win/)
cd /d "%~dp0\.."

REM Run the tray test
python lib\test_tray.py

echo.
echo Test completed!
pause