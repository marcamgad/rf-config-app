@echo off
REM RF Config Sender - Windows Python Bootstrap Installer

echo ============================================================
echo Checking System Requirements...
echo ============================================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [*] Python is already installed.
    goto :RUN_INSTALLER
)

echo [!] Python is NOT installed.
echo [*] Attempting to download and install Python automatically...
echo     This may take a few minutes. Please wait...

REM Download Python Installer using PowerShell
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.1/python-3.12.1-amd64.exe' -OutFile 'python_installer.exe'"

if not exist python_installer.exe (
    echo [X] Failed to download Python installer.
    echo     Please install Python manually from https://www.python.org/
    pause
    exit /b 1
)

REM Install Python silently
echo [*] Installing Python...
python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

REM Clean up installer
del python_installer.exe

REM Verify installation
REM Refresh environment variables (simple way is to just restart cmd, but here we try to call it directly)
set "PATH=%PATH%;C:\Program Files\Python312\;C:\Program Files\Python312\Scripts\"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python installation finished but could not be found in PATH.
    echo     Please restart this script or install Python manually.
    pause
    exit /b 1
)

echo [*] Python installed successfully!

:RUN_INSTALLER
echo.
echo ============================================================
echo Launching RF Config Installer...
echo ============================================================
python install.py

pause
