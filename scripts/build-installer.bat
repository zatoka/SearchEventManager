@echo off
echo ============================================
echo SearchEventsManager - Build Installer
echo ============================================
echo.
echo This script will build the desktop installer.
echo.
echo IMPORTANT: Close any running SearchEventsManager 
echo or Electron processes before continuing.
echo.
pause

echo.
echo Cleaning previous build...
rd /s /q "frontend\dist-electron" 2>nul
rd /s /q "frontend\dist" 2>nul

echo.
echo Building frontend and installer...
cd frontend
call npm run dist:win

echo.
echo ============================================
if exist "dist-electron\SearchEventsManager Setup 1.0.0.exe" (
    echo BUILD SUCCESSFUL!
    echo.
    echo Installer location:
    echo %CD%\dist-electron\SearchEventsManager Setup 1.0.0.exe
    echo.
    start explorer "dist-electron"
) else (
    echo BUILD FAILED.
    echo Check the error messages above.
)
echo ============================================
pause
