@echo off
setlocal enabledelayedexpansion

REM Dev script for Windows (equivalente a scripts/dev.sh)

set "ROOT_DIR=%~dp0.."
for %%I in ("%ROOT_DIR%") do set "ROOT_DIR=%%~fI"
set "FRONTEND_DIR=%ROOT_DIR%\frontend"
set "BACKEND_DIR=%ROOT_DIR%\backend"

if not defined FRONTEND_PORT set "FRONTEND_PORT=3000"
if not defined BACKEND_PORT set "BACKEND_PORT=8000"

echo [dev.bat] ROOT_DIR=%ROOT_DIR%
echo [dev.bat] FRONTEND_PORT=%FRONTEND_PORT%
echo [dev.bat] BACKEND_PORT=%BACKEND_PORT% (proxied por /api)

REM Backend deps (venv local)
set "VENV_DIR=%ROOT_DIR%\.venv"
if not exist "%VENV_DIR%" (
  echo [dev.bat] Creando venv en %VENV_DIR%
  python -m venv "%VENV_DIR%" || exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat" || exit /b 1

echo [dev.bat] Instalando dependencias backend (requirements.txt)
python -m pip install --upgrade pip || exit /b 1
python -m pip install -r "%ROOT_DIR%\requirements.txt" || exit /b 1

REM Frontend deps
if not exist "%FRONTEND_DIR%\node_modules" (
  echo [dev.bat] Instalando dependencias frontend (npm install)
  pushd "%FRONTEND_DIR%" || exit /b 1
  npm install || exit /b 1
  popd
)

REM Start backend in a new window
echo [dev.bat] Arrancando backend...
start "backend" cmd /k "cd /d %ROOT_DIR% && set PYTHONPATH=%BACKEND_DIR% && set BACKEND_PORT=%BACKEND_PORT% && set BACKEND_URL=http://127.0.0.1:%BACKEND_PORT% && python -m uvicorn backend.main:app --host 127.0.0.1 --port %BACKEND_PORT% --reload"

REM Start frontend in a new window
echo [dev.bat] Arrancando frontend...
start "frontend" cmd /k "cd /d %FRONTEND_DIR% && set BACKEND_URL=http://127.0.0.1:%BACKEND_PORT% && set BACKEND_PORT=%BACKEND_PORT% && npm run dev -- --port %FRONTEND_PORT%"

echo.
echo [dev.bat] OK
echo - App:       http://127.0.0.1:%FRONTEND_PORT%
echo - API(/api): http://127.0.0.1:%FRONTEND_PORT%/api/
echo.

endlocal
