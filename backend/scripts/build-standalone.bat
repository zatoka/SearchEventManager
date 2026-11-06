@echo off
REM ============================================================
REM Build Standalone Executable for SearchEventsManager
REM ============================================================

echo.
echo ========================================
echo  Building Standalone Application
echo ========================================
echo.

cd /d "%~dp0"

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo [1/2] Building Python backend executable...
echo This may take a few minutes...
echo.

pyinstaller --clean --noconfirm ^
    --name "SearchEventsBackend" ^
    --add-data "st_louis_concert_venues.csv;." ^
    --add-data "config.py;." ^
    --hidden-import "uvicorn.logging" ^
    --hidden-import "uvicorn.protocols" ^
    --hidden-import "uvicorn.protocols.http" ^
    --hidden-import "uvicorn.protocols.http.auto" ^
    --hidden-import "uvicorn.protocols.websockets" ^
    --hidden-import "uvicorn.protocols.websockets.auto" ^
    --hidden-import "uvicorn.lifespan" ^
    --hidden-import "uvicorn.lifespan.on" ^
    --collect-all "playwright" ^
    --collect-all "aiohttp" ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Backend build failed!
    pause
    exit /b 1
)

echo.
echo [2/2] Backend build complete!
echo.
echo Executable created at: dist\SearchEventsBackend.exe
echo.
pause
