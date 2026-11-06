@echo off
REM ============================================================
REM Status Script for SearchEventsManager
REM Checks if Backend and Frontend servers are running
REM ============================================================

echo.
echo ========================================
echo  SearchEventsManager - Status Check
echo ========================================
echo.

REM Check Backend (port 8002)
echo [Backend] Checking port 8002...
netstat -ano | findstr ":8002" | findstr "LISTENING" > nul
if %errorlevel% equ 0 (
    echo          Status: RUNNING
    echo          URL:    http://127.0.0.1:8002
    echo          Docs:   http://127.0.0.1:8002/docs
) else (
    echo          Status: STOPPED
)

echo.

REM Check Frontend (port 5173)
echo [Frontend] Checking port 5173...
netstat -ano | findstr ":5173" | findstr "LISTENING" > nul
if %errorlevel% equ 0 (
    echo          Status: RUNNING
    echo          URL:    http://localhost:5173
) else (
    echo          Status: STOPPED
)

echo.
echo ========================================
echo.

pause
