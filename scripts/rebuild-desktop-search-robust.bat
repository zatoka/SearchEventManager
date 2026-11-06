@echo off
setlocal EnableExtensions

title SearchEventsManager - Full Rebuild

echo ============================================================
echo SearchEventsManager - Full Rebuild
echo ============================================================
echo.

REM Use the folder containing this .bat file as the project root.
set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%backend"
set "FRONTEND_DIR=%PROJECT_DIR%frontend"

REM Find a Python command that already has PyInstaller installed.
REM Prefer "python"; fall back to the Windows Python launcher.
set "PYTHON_CMD="

where python >nul 2>&1
if not errorlevel 1 (
    python -m PyInstaller --version >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    where py >nul 2>&1
    if not errorlevel 1 (
        py -3 -m PyInstaller --version >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=py -3"
    )
)

echo Project folder:
echo "%PROJECT_DIR%"
echo.

REM Check required project files and tools before changing anything.
if not exist "%BACKEND_DIR%\SearchEventsBackend.spec" (
    echo ERROR: Cannot find:
    echo "%BACKEND_DIR%\SearchEventsBackend.spec"
    echo Put this .bat file in the SearchEventsManager project root.
    goto :fail
)

if not exist "%BACKEND_DIR%\main.py" (
    echo ERROR: Cannot find backend\main.py.
    goto :fail
)

if not exist "%FRONTEND_DIR%\package.json" (
    echo ERROR: Cannot find frontend\package.json.
    goto :fail
)

if not exist "%BACKEND_DIR%\events_manager.db" (
    echo WARNING: backend\events_manager.db was not found.
    echo The desktop package may not include the expected database.
    echo.
)

where npm >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm was not found. Install Node.js, then open a new terminal.
    goto :fail
)

if not defined PYTHON_CMD (
    echo ERROR: No Python command with PyInstaller was found.
    echo.
    echo Open Command Prompt in the project folder and try:
    echo   python -m PyInstaller --version
    echo or:
    echo   py -3 -m PyInstaller --version
    echo.
    echo Use the same Python installation where PyInstaller is installed.
    goto :fail
)

echo Python command selected: %PYTHON_CMD%
%PYTHON_CMD% --version
%PYTHON_CMD% -m PyInstaller --version
echo.

REM Verify frontend dependencies exist rather than attempting a network install.
if not exist "%FRONTEND_DIR%\node_modules" (
    echo ERROR: frontend\node_modules was not found.
    echo Open a terminal in frontend and run: npm install
    goto :fail
)

echo This script will rebuild the backend and desktop installer.
echo It will close any running SearchEventsManager app and remove
echo the previous frontend\dist-electron output folder.
echo.
choice /C YN /M "Continue"
if errorlevel 2 (
    echo Build cancelled. No build files were removed.
    goto :cancelled
)

echo.
echo Step 1 of 4: Closing running SearchEventsManager processes...
taskkill /F /IM SearchEventsManager.exe >nul 2>&1
taskkill /F /IM SearchEventsBackend.exe >nul 2>&1

echo.
echo Step 2 of 4: Building backend with SearchEventsBackend.spec...
pushd "%BACKEND_DIR%"
if errorlevel 1 (
    echo ERROR: Could not enter the backend folder.
    goto :fail
)

%PYTHON_CMD% -m PyInstaller --clean SearchEventsBackend.spec --noconfirm
if errorlevel 1 (
    popd
    echo.
    echo ERROR: PyInstaller failed. Review the error above.
    goto :fail
)
popd

if not exist "%BACKEND_DIR%\dist\SearchEventsBackend\SearchEventsBackend.exe" (
    echo ERROR: Backend build reported success, but the executable was not found:
    echo "%BACKEND_DIR%\dist\SearchEventsBackend\SearchEventsBackend.exe"
    goto :fail
)

echo.
echo Step 3 of 4: Removing previous Electron output...
if exist "%FRONTEND_DIR%\dist-electron" (
    rmdir /S /Q "%FRONTEND_DIR%\dist-electron"
    if exist "%FRONTEND_DIR%\dist-electron" (
        echo ERROR: Could not remove frontend\dist-electron.
        echo Close any running app windows and check folder permissions.
        goto :fail
    )
)

echo.
echo Step 4 of 4: Building React app and Windows installer...
pushd "%FRONTEND_DIR%"
if errorlevel 1 (
    echo ERROR: Could not enter the frontend folder.
    goto :fail
)

call npm run dist:win
if errorlevel 1 (
    popd
    echo.
    echo ERROR: npm run dist:win failed. Review the error above.
    goto :fail
)
popd

echo.
if not exist "%FRONTEND_DIR%\dist-electron\win-unpacked\SearchEventsManager.exe" (
    echo WARNING: The unpacked app executable was not found at the expected path.
    echo Check the output folder:
    echo "%FRONTEND_DIR%\dist-electron"
)

echo ============================================================
echo BUILD FINISHED
echo ============================================================
echo Output folder:
echo "%FRONTEND_DIR%\dist-electron"
echo.
echo Look for the installer:
echo SearchEventsManager Setup 1.0.0.exe
echo.
echo If the installer filename has a different version, look for
echo the Setup .exe file in the output folder.
echo.
pause
endlocal
exit /b 0

:cancelled
echo.
pause
endlocal
exit /b 0

:fail
echo.
echo BUILD STOPPED. No installer success is being reported.
echo Correct the error above and run this script again.
echo.
pause
endlocal
exit /b 1
