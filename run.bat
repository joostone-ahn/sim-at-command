@echo off
REM SIM AT Command Tool - One-click launcher (Windows)
setlocal

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
    echo [SETUP] Creating virtual environment...
    python -m venv "%VENV%"
)

REM Install dependencies
"%PYTHON%" -c "import flask, serial" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing dependencies...
    "%PIP%" install -q --disable-pip-version-check -r "%DIR%requirements.txt"
    "%PIP%" install -q --disable-pip-version-check -e "%DIR%pysim"
    echo [SETUP] Done.
)

REM Open browser
start "" "%URL%"

REM Start server
echo [START] SIM AT Command Tool at %URL%
set PYTHONDONTWRITEBYTECODE=1
"%PYTHON%" -u "%DIR%src\app.py"
pause
