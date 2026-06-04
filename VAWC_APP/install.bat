@echo off
echo ======================================================
echo    VAWC Case Logging System - Installation
echo ======================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from python.org
    pause
    exit /b
)

echo [1/3] Installing required packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo [2/3] Setting up application folder...
if not exist "logo" mkdir logo
if not exist "attachments" mkdir attachments
if not exist "backups" mkdir backups

echo.
echo [3/3] Creating Desktop Shortcut...
set SCRIPT="%TEMP%\%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") >> %SCRIPT%
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\VAWC System.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "pythonw" >> %SCRIPT%
echo oLink.Arguments = "\"%CD%\main.py\"" >> %SCRIPT%
echo oLink.WorkingDirectory = "%CD%" >> %SCRIPT%
echo oLink.Description = "VAWC Case Logging System" >> %SCRIPT%
echo oLink.IconLocation = "%CD%\logo\shield.ico" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%

echo.
echo [SUCCESS] Installation complete!
echo You can now use the 'VAWC System' shortcut on your Desktop.
echo.
pause