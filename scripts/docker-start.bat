@echo off
REM ============================================================
REM Build and Start Docker Containers
REM ============================================================

echo.
echo ========================================
echo  Building Docker Containers
echo ========================================
echo.
echo This will take 5-10 minutes on first run.
echo.

cd /d "%~dp0"

REM Use docker compose (V2 syntax)
docker compose up --build

echo.
pause
