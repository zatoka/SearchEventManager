@echo off
REM ============================================================
REM Import Venues from CSV File
REM ============================================================

echo.
echo ========================================
echo  Import Venues from CSV
echo ========================================
echo.

cd /d "%~dp0"

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    pause
    exit /b 1
)

REM Run import script
REM Usage: import_venues.py [csv_file] [--clear]
REM 
REM Examples:
REM   import_venues.py                  - Use default venues.csv
REM   import_venues.py venues.csv       - Use venues.csv
REM   import_venues.py --clear          - Clear existing and import venues.csv
REM   import_venues.py my_venues.csv --clear

venv\Scripts\python.exe import_venues.py %*

echo.
pause
