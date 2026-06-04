@echo off
echo Starting VAWC Case Logging System...
pythonw "%~dp0main.py"
if %errorlevel% neq 0 (
    echo.
    echo [CRASH] The application has stopped unexpectedly.
    echo.
    echo Possible causes:
    echo 1. Missing dependencies (Run install.bat)
    echo 2. Python version mismatch
    echo 3. Database file is locked
    echo.
    pause
)