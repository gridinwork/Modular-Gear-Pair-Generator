@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Virtual environment not found.
  echo Run install.bat first.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" main.py
if errorlevel 1 (
  echo.
  echo [ERROR] The application exited with an error.
  pause
  exit /b 1
)
