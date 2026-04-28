@echo off
REM ============================================================
REM  SIM AT Command Tool - Build standalone exe (Windows)
REM  Requires: Python 3.10+ installed on the build machine
REM  Output:   installer\dist\SIM-AT-Command.exe
REM ============================================================
setlocal enabledelayedexpansion

set DIR=%~dp0
set PROJECT_ROOT=%DIR%..
set VENV=%DIR%.build_venv
set PYTHON=%VENV%\Scripts\python.exe

echo.
echo  +========================================+
echo  ^|  SIM AT Command Tool -- Build EXE      ^|
echo  +========================================+
echo.

REM ── Check Python ──────────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM ── Create build venv ─────────────────────────────────────
if not exist "%PYTHON%" (
    echo [1/4] Creating build virtual environment...
    python -m venv "%VENV%"
)

REM ── Install dependencies ──────────────────────────────────
echo [2/4] Installing dependencies...

"%PYTHON%" -m pip install --disable-pip-version-check -q ^
    flask pyserial pyscard

if errorlevel 1 (
    echo [ERROR] Failed to install core dependencies.
    pause
    exit /b 1
)

REM Install pySim from local source (editable not needed for build)
"%PYTHON%" -m pip install --disable-pip-version-check -q "%PROJECT_ROOT%\pysim"

if errorlevel 1 (
    echo [ERROR] Failed to install pySim.
    pause
    exit /b 1
)

"%PYTHON%" -m pip install --disable-pip-version-check -q pyinstaller

if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)

REM ── Clean previous build ──────────────────────────────────
echo [3/4] Cleaning previous build...
if exist "%DIR%dist" rmdir /s /q "%DIR%dist"
if exist "%DIR%build" rmdir /s /q "%DIR%build"

REM ── Build exe ─────────────────────────────────────────────
echo [4/4] Building standalone exe (this may take a few minutes)...
cd /d "%DIR%"
"%PYTHON%" -m PyInstaller --clean --noconfirm sim-at-command.spec

if exist "%DIR%dist\SIM-AT-Command.exe" (
    echo.
    echo  [SUCCESS] Build complete!
    echo  Output: %DIR%dist\SIM-AT-Command.exe
    echo.
    for %%F in ("%DIR%dist\SIM-AT-Command.exe") do echo  Size: %%~zF bytes
    echo.
) else (
    echo.
    echo  [ERROR] Build failed. Check output above for errors.
    echo.
)

pause
