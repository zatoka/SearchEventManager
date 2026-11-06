@echo off
REM ============================================================
REM Restart Script for SearchEventsManager
REM Restarts both Backend and Frontend servers
REM ============================================================

echo.
echo ========================================
echo  SearchEventsManager - Restarting...
echo ========================================
echo.

REM Call stop script
call "%~dp0stop.bat"

echo.
echo Waiting 3 seconds before starting...
timeout /t 3 /nobreak > nul

REM Call start script
call "%~dp0start.bat"
