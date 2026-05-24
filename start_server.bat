@echo off
setlocal

REM Model Gallery Server - Windows Startup Script

echo ===============================
echo   Model Gallery Server
echo ===============================
echo.

REM Move to script directory
cd /d "%~dp0"

set "VENV_DIR=%~dp0venv"

REM Check that Python is available
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Install Python 3 from https://www.python.org/ and try again.
    pause
    exit /b 1
)

REM Create venv if it doesn't exist yet
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [INFO] Virtual environment not found. Creating it...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
)

REM Activate venv
call "%VENV_DIR%\Scripts\activate.bat"

REM Install Pillow if missing
python -c "from PIL import Image" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Pillow not found, installing...
    pip install Pillow
    if errorlevel 1 (
        echo [ERROR] Failed to install Pillow.
        pause
        exit /b 1
    )
    echo [OK] Pillow installed.
)

REM Sanity check
if not exist "model_server.py" (
    echo [ERROR] model_server.py not found in this directory.
    pause
    exit /b 1
)

echo.
echo Server starting at http://localhost:8001/
echo Press Ctrl+C to stop.
echo.

REM Open the browser after a short delay so the server has time to bind
start "" /B cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8001/"

REM Run the server in the foreground (blocks until Ctrl+C)
python model_server.py

echo.
echo Server stopped.
pause
