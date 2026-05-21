@echo off
cd /d "%~dp0"
echo ============================================================
echo   Radar Web Dashboard
echo   Installing/checking dependencies...
echo ============================================================
python -m pip install -r requirements.txt --quiet
echo.
echo Starting server...  Open http://127.0.0.1:5000 in your browser.
echo Press Ctrl+C to stop.
echo.
python app.py
pause
