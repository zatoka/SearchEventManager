@echo off
REM ============================================================
REM Install WSL 2 for Docker Desktop
REM Run this script as Administrator
REM ============================================================

echo.
echo ========================================
echo  Installing WSL 2 (Windows Subsystem for Linux)
echo ========================================
echo.
echo This will:
echo   1. Enable WSL feature
echo   2. Enable Virtual Machine Platform
echo   3. Install Ubuntu Linux
echo   4. Require a computer restart
echo.
pause

echo.
echo Installing WSL...
wsl --install

echo.
echo ========================================
echo  Installation Complete!
echo ========================================
echo.
echo IMPORTANT: Please restart your computer now.
echo After restart, Ubuntu will launch and ask you to:
echo   - Create a Linux username
echo   - Create a Linux password
echo.
echo Then run Docker Desktop Installer again.
echo.
pause
