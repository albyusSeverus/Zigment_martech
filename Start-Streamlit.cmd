@echo off
REM Start the Streamlit UI for Content Engine (Windows)

setlocal ENABLEDELAYEDEXPANSION
cd /d "%~dp0"

set VENV_DIR=streamlit\.venv
set VENV_PY=%VENV_DIR%\Scripts\python.exe

echo [Check] Looking for Python...
where python >nul 2>nul || (
  echo [Error] Python not found in PATH. Install from https://python.org and retry.
  pause
  exit /b 1
)

if not exist "%VENV_PY%" (
  echo [Setup] Creating virtual environment at %VENV_DIR% ...
  python -m venv "%VENV_DIR%" || (
    echo [Error] Failed to create virtual environment.
    pause
    exit /b 1
  )
)

echo [Setup] Ensuring dependencies are installed in venv...
"%VENV_PY%" -m pip install --upgrade pip >nul 2>&1
"%VENV_PY%" -m pip install -r streamlit/requirements.txt || (
  echo [Error] Failed to install requirements into venv.
  pause
  exit /b 1
)

echo [Start] Launching Streamlit app from venv...
start "Content Engine - Streamlit" cmd /k ""%VENV_PY%" -m streamlit run streamlit/app.py --server.headless=true"

echo [Open] Your browser should open automatically. If not, visit:
echo        http://localhost:8501
echo A new terminal window is running the app. Close it to stop.
pause
