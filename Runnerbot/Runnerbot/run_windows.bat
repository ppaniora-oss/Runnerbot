@echo off
echo ===================================
echo   Runnerbot - Self-Contained Mode
echo ===================================
echo.

cd /d "%~dp0"

if not exist venv (
    echo Virtual environment not found. Running installer first...
    call install_windows.bat
)

call venv\Scripts\activate.bat

set RUNNERBOT_HOME=%~dp0

echo Running from: %~dp0
echo All data stored in this folder only.
echo.
echo Server starting at http://localhost:5000
echo Press Ctrl+C to stop
echo.

python app.py
