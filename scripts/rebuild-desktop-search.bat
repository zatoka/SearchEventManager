@echo off
setlocal

echo ============================================
echo Rebuilding SearchEventsManager
echo ============================================

set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%backend"
set "FRONTEND_DIR=%PROJECT_DIR%frontend"

echo.
echo Project folder:
echo %PROJECT_DIR%

if not exist "%BACKEND_DIR%\SearchEventsBackend.spec" (
    echo ERROR: Cannot find backend\SearchEventsBackend.spec
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%\package.json" (
    echo ERROR: Cannot find frontend\package.json
    pause
    exit /b 1
)

echo.
echo Step 1: Stopping running application processes...
taskkill /F /IM SearchEventsManager.exe >nul 2>&1
taskkill /F /IM SearchEventsBackend.exe >nul 2>&1

echo.
echo Step 2: Checking PyInstaller in the current Python...
python -m PyInstaller --version
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller is not available to the Python command.
    echo Run "python -m PyInstaller --version" in a terminal first.
    echo Use the same Python installation that has PyInstaller installed.
    pause
    exit /b 1
)

echo.
echo Step 3: Rebuilding backend with PyInstaller...
cd /d "%BACKEND_DIR%"
python -m PyInstaller --clean SearchEventsBackend.spec --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: Backend build failed. The Electron build was not started.
    pause
    exit /b 1
)

if not exist "%BACKEND_DIR%\dist\SearchEventsBackend\SearchEventsBackend.exe" (
    echo.
    echo ERROR: The rebuilt backend executable was not found.
    pause
    exit /b 1
)

echo.
echo Step 4: Rebuilding Electron app and Windows installer...
cd /d "%FRONTEND_DIR%"

if exist "dist-electron" (
    rmdir /s /q "dist-electron"
    if exist "dist-electron" (
        echo ERROR: Could not remove frontend\dist-electron.
        echo Close any running SearchEventsManager windows and try again.
        pause
        exit /b 1
    )
)

call npm run dist:win
if errorlevel 1 (
    echo.
    echo ERROR: Frontend or installer build failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo BUILD SUCCESSFUL!
echo.
echo Installer output folder:
echo %FRONTEND_DIR%\dist-electron
echo.
echo Look for:
echo SearchEventsManager Setup 1.0.0.exe
echo ============================================
pause
endlocal
