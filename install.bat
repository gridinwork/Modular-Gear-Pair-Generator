@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ========================================
echo  Modular Gear Pair Generator - install
echo ========================================
echo.

set "PY_CMD="
where py >nul 2>nul && set "PY_CMD=py -3.11"
if not defined PY_CMD (
  where python >nul 2>nul && set "PY_CMD=python"
)
if not defined PY_CMD (
  echo [ERROR] Python 3.11+ was not found in PATH.
  echo Install Python from python.org and enable "Add Python to PATH".
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  %PY_CMD% -m venv .venv
  if errorlevel 1 goto :fail
)

set "PY=.venv\Scripts\python.exe"
"%PY%" -m pip install --upgrade pip
if errorlevel 1 goto :fail
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo.
echo Installation completed successfully.
echo Run start.bat to launch the application.
pause
exit /b 0

:fail
echo.
echo [ERROR] Installation failed.
pause
exit /b 1
