@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo  Modular Gear Pair Generator - install
echo ========================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
  set "PY=py -3"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo ERROR: Python 3.11+ was not found.
    echo Install Python from https://www.python.org/ and enable "Add Python to PATH".
    pause
    exit /b 1
  )
  set "PY=python"
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  %PY% -m venv .venv
  if errorlevel 1 goto :fail
)

echo Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :fail

echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo WARNING: CadQuery may not be available for this Python/Windows configuration.
  echo Installing the core fallback stack without CadQuery...
  ".venv\Scripts\python.exe" -m pip install PySide6 numpy trimesh shapely mapbox-earcut pyvista pyvistaqt
  if errorlevel 1 goto :fail
)

echo.
echo Installation completed.
echo Run start.bat to launch the program.
goto :end

:fail
echo.
echo Installation failed.
exit /b 1

:end
pause
endlocal
