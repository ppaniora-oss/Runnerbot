@echo off
echo ===================================
echo   Runnerbot - Windows Setup
echo ===================================
echo.

cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python 3.10+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing dependencies...
pip install -r requirements.txt

echo Creating data directories...
if not exist models mkdir models
if not exist library mkdir library
if not exist data mkdir data

echo.
echo ===================================
echo   Installation Complete!
echo ===================================
echo.
echo All data stays within this folder.
echo Safe to run from SSD, HDD, or USB.
echo.
echo To run: Double-click run_windows.bat
echo.
pause
