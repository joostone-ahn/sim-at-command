@echo off
REM SIM AT Command Tool - One-click launcher (Windows)
setlocal

echo.
echo ========================================
echo   SIM AT Command Tool -- Web UI
echo ========================================
echo.

set DIR=%~dp0
set VENV=%DIR%.venv
set PORT=8083
set URL=http://127.0.0.1:%PORT%
set PYTHON=%VENV%\Scripts\python.exe
set PIP=%VENV%\Scripts\pip.exe

REM Kill existing process on port
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
    echo [INIT] Killing existing process PID %%a on port %PORT%
    taskkill /F /PID %%a >nul 2>&1
)

REM Check Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM Create venv if needed
if not exist "%PYTHON%" (
    if exist "%VENV%" (
        echo [SETUP] Removing broken virtual environment...
        rmdir /s /q "%VENV%" >nul 2>&1
    )
    echo [SETUP] Creating virtual environment...
    python -m venv "%VENV%"
    if not exist "%PYTHON%" (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Install dependencies
"%PYTHON%" -c "import flask, serial, pySim" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing dependencies...
    "%PYTHON%" -m pip install -q --disable-pip-version-check -r "%DIR%requirements.txt"
    echo [SETUP] Done.
)

REM Open browser
start "" "%URL%"

REM Start server
echo [START] SIM AT Command Tool at %URL%
set PYTHONDONTWRITEBYTECODE=1
"%PYTHON%" -u "%DIR%src\app.py"
pause
