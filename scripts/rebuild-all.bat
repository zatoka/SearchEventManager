@echo off
echo ============================================
echo Rebuilding SearchEventsManager
echo ============================================

echo.
echo Step 1: Killing any running backend processes...
taskkill /F /IM SearchEventsBackend.exe 2>nul

echo.
echo Step 2: Rebuilding backend with PyInstaller...
cd /d "%~dp0backend"
call venv\Scripts\activate
pyinstaller SearchEventsBackend.spec --noconfirm
if errorlevel 1 (
    echo ERROR: Backend build failed!
    pause
    exit /b 1
)

echo.
echo Step 3: Rebuilding Electron app...
cd /d "%~dp0frontend"
if exist dist-electron rmdir /s /q dist-electron
call npm run dist:win
if errorlevel 1 (
    echo ERROR: Frontend build failed!
    pause
    exit /b 1
)

echo.
echo ============================================
echo BUILD SUCCESSFUL!
echo.
echo Installer location:
echo %~dp0frontend\dist-electron\SearchEventsManager Setup 1.0.0.exe
echo.
echo ============================================
pause
