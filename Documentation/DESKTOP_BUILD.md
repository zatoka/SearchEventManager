# Building Desktop Application

This guide explains how to create a standalone desktop application (`.exe` file) that can run on any Windows computer without needing Python, Docker, or any other dependencies.

## What You'll Get

A single installer file: `SearchEventsManager Setup 1.0.0.exe`

Your son can:
1. Download the file
2. Run it
3. Click "Next" a few times
4. Use the application!

No Python, no Docker, no technical knowledge needed!

## Prerequisites (For Building Only)

You need these installed on YOUR computer to build the app:

1. **Python 3.11+** (already installed)
2. **Node.js 18+** (already installed)
3. **PyInstaller** (will be installed automatically)

## Build Steps

### Option 1: Automated Build (Recommended)

Just run:
```cmd
build-desktop.bat
```

This will:
1. Install PyInstaller (if needed)
2. Build the Python backend into an `.exe`
3. Build the React frontend
4. Package everything with Electron
5. Create an installer

**Build time**: 10-15 minutes

### Option 2: Manual Build

If the automated script doesn't work, run these commands manually:

```cmd
# 1. Install PyInstaller
pip install pyinstaller

# 2. Build backend
cd backend
pyinstaller --clean --noconfirm --name "SearchEventsBackend" --add-data "st_louis_concert_venues.csv;." --add-data "events_manager.db;." --hidden-import "uvicorn.logging" --hidden-import "uvicorn.protocols" --hidden-import "uvicorn.protocols.http" --hidden-import "uvicorn.protocols.http.auto" --hidden-import "uvicorn.protocols.websockets" --hidden-import "uvicorn.protocols.websockets.auto" --hidden-import "uvicorn.lifespan" --hidden-import "uvicorn.lifespan.on" --collect-all "playwright" --collect-all "aiohttp" main.py
cd ..

# 3. Build frontend
cd frontend
npm run build
npm run dist:win
cd ..
```

## Output

After building, you'll find:

```
frontend/dist-electron/
├── SearchEventsManager Setup 1.0.0.exe    ← Give this to your son!
└── win-unpacked/
    └── SearchEventsManager.exe            ← Portable version (no installer)
```

## For Your Son

### Installation Steps:

1. Download `SearchEventsManager Setup 1.0.0.exe`
2. Double-click to run
3. Click "Next" through the installer
4. Choose installation location (default is fine)
5. Click "Install"
6. Click "Finish"
7. Application opens automatically!

### Features:

- ✅ No Python installation needed
- ✅ No Docker installation needed
- ✅ No technical knowledge required
- ✅ Works like any Windows application
- ✅ Includes all scrapers (TM, CW, MX)
- ✅ Includes database
- ✅ Includes all dependencies

### Uninstalling:

Just like any Windows application:
- Go to Settings → Apps → SearchEventsManager → Uninstall

OR

- Run `uninstall.exe` in the installation folder

## Troubleshooting Build Issues

### "PyInstaller not found"
```cmd
pip install pyinstaller
```

### "npm not found"
Make sure Node.js is installed and in your PATH.

### "Module not found" errors
```cmd
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

### Build takes too long
This is normal! First build:
- Backend: 5-10 minutes
- Frontend: 2-3 minutes
- Electron packaging: 1-2 minutes

Subsequent builds are faster (cached).

## File Sizes

- Backend `.exe`: ~200-300 MB (includes Python + Playwright + Chromium)
- Frontend build: ~5-10 MB
- Final installer: ~250-350 MB

This is normal for Electron + Python apps.

## Alternative: Portable Version

If you don't want an installer, use the portable version:

```
frontend/dist-electron/win-unpacked/SearchEventsManager.exe
```

Just copy the entire `win-unpacked` folder to your son's computer. He can run the `.exe` directly - no installation needed!

## Testing Before Sharing

Always test the installer on your own machine first:

1. Run `build-desktop.bat`
2. Install the app: `frontend\dist-electron\SearchEventsManager Setup 1.0.0.exe`
3. Test all features
4. If everything works, share with your son!

## Notes

- The application will run on Windows 10/11 (64-bit)
- It will NOT run on Mac or Linux (you'd need to build separately for those)
- The database is included in the build
- API keys are included (from your config.py)

## Security Note

Your Ticketmaster API key is embedded in the executable. Only share with trusted people (like your son).

If you want to keep API keys separate, you can:
1. Remove them from config.py before building
2. Have your son create a `.env` file after installation
