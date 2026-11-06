@echo off
REM ============================================================
REM Start Script for SearchEventsManager
REM Starts both Backend (FastAPI) and Frontend (Vite/React)
REM ============================================================

echo.
echo ========================================
echo  SearchEventsManager - Starting...
echo ========================================
echo.

REM Get the backend directory
set BACKEND_DIR=%~dp0
set FRONTEND_DIR=%BACKEND_DIR%..\frontend

REM Change to backend directory
cd /d "%BACKEND_DIR%"

REM ============================================================
REM CHECK AND KILL EXISTING PROCESSES
REM ============================================================

echo [0/2] Checking for running processes...

REM Check and kill Backend (port 8002)
netstat -ano | findstr ":8002" | findstr "LISTENING" > nul
if %errorlevel% equ 0 (
    echo       Backend already running on port 8002 - Killing...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8002 ^| findstr LISTENING') do (
        taskkill /PID %%a /F > nul 2>&1
    )
    timeout /t 2 /nobreak > nul
) else (
    echo       Backend not running - OK
)

REM Check and kill Frontend (port 5173)
netstat -ano | findstr ":5173" | findstr "LISTENING" > nul
if %errorlevel% equ 0 (
    echo       Frontend already running on port 5173 - Killing...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
        taskkill /PID %%a /F > nul 2>&1
    )
    timeout /t 2 /nobreak > nul
) else (
    echo       Frontend not running - OK
)

echo.

REM ============================================================
REM START SERVERS
REM ============================================================

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Start Backend (FastAPI on port 8002)
echo [1/2] Starting Backend API on port 8002...
start "SearchEventsManager-Backend" cmd /k "cd /d "%BACKEND_DIR%" && venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8002"

REM Wait a moment for backend to start
timeout /t 3 /nobreak > nul

REM Start Frontend (Vite on port 5173)
echo [2/2] Starting Frontend on port 5173...
start "SearchEventsManager-Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"

REM Wait for frontend to start
timeout /t 3 /nobreak > nul

echo.
echo ========================================
echo  Application Started Successfully!
echo ========================================
echo.
echo  Backend API:  http://127.0.0.1:8002
echo  Frontend UI:  http://localhost:5173
echo  API Docs:     http://127.0.0.1:8002/docs
echo.
echo  Two windows opened:
echo   - SearchEventsManager-Backend
echo   - SearchEventsManager-Frontend
echo.
echo  To stop: run stop.bat
echo ========================================
echo.

REM Open browser to frontend
timeout /t 2 /nobreak > nul
start http://localhost:5173

pause
