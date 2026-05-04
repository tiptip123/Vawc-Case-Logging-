@echo off
setlocal enabledelayedexpansion

echo Installing VAWC Case Logging System...
echo.

echo Step 1: Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python was not found on your PATH.
    echo Please install Python 3.10+ and rerun install.bat.
    pause
    exit /b 1
)

echo Step 2: Installing required packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install Python dependencies.
    pause
    exit /b 1
)

echo.
echo Step 3: Creating desktop shortcut...
set "SCRIPT_DIR=%~dp0"
set "SHORTCUT_NAME=VAWC Case Logging System.lnk"
set "DESKTOP=%USERPROFILE%\Desktop"
set "TARGET=%SCRIPT_DIR%run.bat"
set "ICON=%SCRIPT_DIR%app.ico"
set "WORKDIR=%SCRIPT_DIR%"

powershell -NoProfile -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\\%SHORTCUT_NAME%'); $Shortcut.TargetPath = '%TARGET%'; $Shortcut.WorkingDirectory = '%WORKDIR%'; $Shortcut.IconLocation = '%ICON%'; $Shortcut.Save();"

if exist "%DESKTOP%\%SHORTCUT_NAME%" (
    echo Shortcut created on your desktop.
) else (
    echo Failed to create desktop shortcut. Please create one manually.
)

echo.
echo Installation complete. Run the app via the desktop shortcut or by double-clicking run.bat.
pause