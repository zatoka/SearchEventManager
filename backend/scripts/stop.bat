@echo off
REM ============================================================
REM Stop Script for SearchEventsManager
REM Stops both Backend (FastAPI) and Frontend (Vite/React)
REM ============================================================

echo.
echo ========================================
echo  SearchEventsManager - Stopping...
echo ========================================
echo.

REM Kill Backend (port 8002)
echo [1/2] Stopping Backend (port 8002)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8002 ^| findstr LISTENING') do (
    echo Killing process %%a on port 8002...
    taskkill /PID %%a /F > nul 2>&1
)

REM Kill Frontend (port 5173)
echo [2/2] Stopping Frontend (port 5173)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    echo Killing process %%a on port 5173...
    taskkill /PID %%a /F > nul 2>&1
)

REM Also kill by window title (backup method)
taskkill /FI "WINDOWTITLE eq SearchEventsManager-Backend*" /F > nul 2>&1
taskkill /FI "WINDOWTITLE eq SearchEventsManager-Frontend*" /F > nul 2>&1

REM Kill any node processes for vite (be careful - kills all node)
REM Uncomment if needed:
REM taskkill /IM node.exe /F > nul 2>&1

echo.
echo ========================================
echo  Application Stopped Successfully!
echo ========================================
echo.

pause
