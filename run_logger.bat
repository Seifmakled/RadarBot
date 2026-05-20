@echo off
cd /d "%~dp0"
echo Starting Radar Logger...
echo Press Ctrl+C to stop.
echo.
python logger.py
pause
