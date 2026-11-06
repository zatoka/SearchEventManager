# Desktop Application - Quick Start Guide

## Goal
Create a standalone `.exe` file that your son can run without installing Python or Docker.

## What You Need to Do

### Step 1: Run the Build Script

```cmd
cd "C:\Users\grego\OneDrive\Documentos\My Kiro Projects\SearchEventsManager"
build-desktop.bat
```

**Wait 10-15 minutes** while it builds.

### Step 2: Find the Installer

After the build completes, you'll find:

```
frontend\dist-electron\SearchEventsManager Setup 1.0.0.exe
```

### Step 3: Share with Your Son

**Option A: Installer (Recommended)**
- File: `SearchEventsManager Setup 1.0.0.exe`
- Size: ~250-350 MB
- He runs it, clicks "Next", done!

**Option B: Portable (No Installer)**
- Folder: `frontend\dist-electron\win-unpacked\`
- He copies folder, runs `SearchEventsManager.exe`

## What Your Son Gets

A desktop application that:
- ✅ Opens with a double-click
- ✅ No Python needed
- ✅ No Docker needed
- ✅ No technical knowledge required
- ✅ Includes all features (search, filters, scrapers)
- ✅ Works offline (after first use)

## How It Works

The build process:

1. **PyInstaller** packages Python + your backend code into a standalone `.exe`
2. **Electron** packages your React frontend into a desktop app
3. **electron-builder** creates an installer

Everything is bundled together - no external dependencies!

## Quick Reference

| File | Purpose |
|------|---------|
| `build-desktop.bat` | Main build script |
| `backend/build-standalone.bat` | Build just the backend |
| `DESKTOP_BUILD.md` | Detailed documentation |

## Next Steps

1. Run `build-desktop.bat`
2. Wait for build to complete (10-15 min)
3. Test the installer on your machine
4. If it works, share with your son!
5. He installs and enjoys!

## Need Help?

- Check `DESKTOP_BUILD.md` for troubleshooting
- Build logs are shown in the console
- If build fails, try running as Administrator

---

**Your son will love having his own copy!** 🎵
