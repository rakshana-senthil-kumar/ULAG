@echo off
title BHUMI-FUSION Launcher
echo ================================================================
echo           BHUMI-FUSION: AI Cadastral Reconciliation
echo ================================================================
echo.

cd /d "%~dp0"
set "ROOT_DIR=%CD%"
set "PYTHONPATH=%ROOT_DIR%"

echo [1/4] Checking Python environment...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo [2/4] Checking Node.js and npm...
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js / npm is not installed or not in PATH.
    pause
    exit /b 1
)

echo [3/4] Starting FastAPI Backend on port 8000...
start "BHUMI-FUSION Backend" cmd /k "cd /d "%ROOT_DIR%" && set PYTHONPATH=%ROOT_DIR% && python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [4/4] Starting Vite Frontend on port 5173...
start "BHUMI-FUSION Frontend" cmd /k "cd /d "%ROOT_DIR%\frontend" && npm run dev"

echo.
echo Waiting 3 seconds for services to initialize...
ping 127.0.0.1 -n 4 >nul

echo Opening BHUMI-FUSION in default browser: http://localhost:5173
start http://localhost:5173

echo.
echo ================================================================
echo   BHUMI-FUSION is running!
echo   Frontend: http://localhost:5173
echo   Backend:  http://127.0.0.1:8000 (API Docs: http://127.0.0.1:8000/docs)
echo.
echo   To stop all servers, run: stop.bat
echo ================================================================
echo.
pause
