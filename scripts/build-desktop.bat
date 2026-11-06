@echo off
REM ============================================================
REM Build Desktop Application for SearchEventsManager
REM Creates a standalone .exe file that doesn't need Docker
REM ============================================================

echo.
echo ========================================
echo  Building Desktop Application
echo ========================================
echo.

cd /d "%~dp0"

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [1/3] Installing PyInstaller...
    pip install pyinstaller
) else (
    echo [1/3] PyInstaller already installed
)

echo.
echo [2/3] Building Python backend executable...
echo This may take 5-10 minutes...
echo.

cd backend

REM Build backend with PyInstaller
pyinstaller --clean --noconfirm ^
    --name "SearchEventsBackend" ^
    --add-data "st_louis_concert_venues.csv;." ^
    --add-data "events_manager.db;." ^
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

cd ..

echo.
echo [3/3] Building Electron application...
echo.

cd frontend

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing npm dependencies...
    npm install
)

REM Build React app for production
echo Building React frontend...
npm run build

REM Build Electron app
echo Building Electron desktop app...
npm run dist:win

if errorlevel 1 (
    echo.
    echo [ERROR] Electron build failed!
    pause
    exit /b 1
)

cd ..

echo.
echo ========================================
echo  BUILD COMPLETE!
echo ========================================
echo.
echo The installer is located at:
echo   frontend\dist-electron\SearchEventsManager Setup 1.0.0.exe
echo.
echo You can copy this file to your son's computer.
echo He just needs to run it - no Python or Docker needed!
echo.
pause
