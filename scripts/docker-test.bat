@echo off
REM ============================================================
REM Test Docker Setup for SearchEventsManager
REM ============================================================

echo.
echo ========================================
echo  Docker Setup Test
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed!
    echo.
    echo Please install Docker Desktop:
    echo https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

echo [OK] Docker is installed
docker --version
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop is not running!
    echo.
    echo Please start Docker Desktop from the Start Menu.
    echo Wait for the whale icon to turn green in the system tray.
    echo.
    pause
    exit /b 1
)

echo [OK] Docker Desktop is running
echo.

REM Check if .env file exists
if not exist ".env" (
    echo [WARN] .env file not found!
    echo.
    echo Creating .env from .env.example...
    copy .env.example .env >nul
    echo.
    echo [ACTION REQUIRED] Please edit .env file with your API keys:
    echo    TICKETMASTER_API_KEY=your_key_here
    echo    TICKETMASTER_API_SECRET=your_secret_here
    echo.
    pause
    exit /b 1
)

echo [OK] .env file exists
echo.

REM Stop any running containers
echo [1/3] Stopping existing containers...
docker-compose down 2>nul
echo.

REM Build containers
echo [2/3] Building containers (this may take 5-10 minutes)...
docker-compose build
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed! Check the error messages above.
    pause
    exit /b 1
)
echo.

REM Start containers
echo [3/3] Starting containers...
docker-compose up -d
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start containers! Check the error messages above.
    pause
    exit /b 1
)
echo.

echo ========================================
echo  SUCCESS! Docker containers are running!
echo ========================================
echo.
echo  Frontend:    http://localhost
echo  Backend API: http://localhost:8002
echo  API Docs:    http://localhost:8002/docs
echo.
echo  To view logs:     docker-compose logs -f
echo  To stop:          docker-compose down
echo.
pause
