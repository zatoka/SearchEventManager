@echo off
echo Testing backend routes...
cd /d "%~dp0backend"
call venv\Scripts\activate
python -c "from routes import venues, events; print('Routes import OK')"
if errorlevel 1 (
    echo Routes import FAILED!
    pause
    exit /b 1
)
echo.
echo Testing PyInstaller build...
cd dist\SearchEventsBackend
SearchEventsBackend.exe --help 2>&1
pause
