@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   Runnerbot Portable Installer for Windows
echo ============================================
echo.
echo This will install Runnerbot to any location
echo (USB drive, external HDD/SSD, or local folder)
echo.

set "SCRIPT_DIR=%~dp0"

set /p INSTALL_PATH="Enter installation path (e.g., E:\Runnerbot): "

if "%INSTALL_PATH%"=="" (
    echo Error: No path provided.
    pause
    exit /b 1
)

if exist "%INSTALL_PATH%" (
    set /p CONFIRM="Directory exists. Overwrite? (y/n): "
    if /i not "!CONFIRM!"=="y" (
        echo Installation cancelled.
        pause
        exit /b 0
    )
)

echo.
echo Installing to: %INSTALL_PATH%
echo.

mkdir "%INSTALL_PATH%" 2>nul

echo Copying application files...
copy "%SCRIPT_DIR%app.py" "%INSTALL_PATH%\" >nul
copy "%SCRIPT_DIR%index.html" "%INSTALL_PATH%\" >nul
copy "%SCRIPT_DIR%requirements.txt" "%INSTALL_PATH%\" >nul
copy "%SCRIPT_DIR%install_linux.sh" "%INSTALL_PATH%\" >nul
copy "%SCRIPT_DIR%run_linux.sh" "%INSTALL_PATH%\" >nul
copy "%SCRIPT_DIR%install_windows.bat" "%INSTALL_PATH%\" >nul
copy "%SCRIPT_DIR%run_windows.bat" "%INSTALL_PATH%\" >nul

mkdir "%INSTALL_PATH%\models" 2>nul
mkdir "%INSTALL_PATH%\library" 2>nul
mkdir "%INSTALL_PATH%\data" 2>nul
mkdir "%INSTALL_PATH%\static" 2>nul

if exist "%SCRIPT_DIR%static\icon.png" (
    copy "%SCRIPT_DIR%static\icon.png" "%INSTALL_PATH%\static\" >nul
)

if exist "%SCRIPT_DIR%README.md" (
    copy "%SCRIPT_DIR%README.md" "%INSTALL_PATH%\" >nul
)

echo.
echo Checking for Python...
where python >nul 2>nul
if %errorlevel% equ 0 (
    set /p SETUP_ENV="Set up Python environment now? (y/n): "
    if /i "!SETUP_ENV!"=="y" (
        echo Creating virtual environment...
        cd /d "%INSTALL_PATH%"
        python -m venv venv
        call venv\Scripts\activate.bat
        echo Installing dependencies...
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        call deactivate
        echo Environment ready!
    )
) else (
    echo Python not found. Run install_windows.bat on target system.
)

echo.
echo ============================================
echo   Installation Complete!
echo ============================================
echo.
echo Installed to: %INSTALL_PATH%
echo.
echo To run on any Windows system:
echo   1. Navigate to %INSTALL_PATH%
echo   2. Double-click run_windows.bat
echo   3. Open http://localhost:5000
echo.
echo The folder is fully portable - copy it anywhere!
echo.
pause
