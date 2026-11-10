# SearchEventsManager - Desktop Build (Git Bash)

Step-by-step commands to build the Windows desktop app (backend `.exe` + Electron installer).

Here are the commands for **Git Bash**. Run them in order from the project folder.
Before you start, **stop the dev backend** (Ctrl+C), because the built backend uses the same port, **8002**.

> Git Bash needs forward slashes in paths (`./venv/Scripts/python.exe`), not backslashes.

---

## 1. Install PyInstaller (one time)

```bash
cd ~/PROJECT-FOLDERS-DOCUMENTS/KIRO/SearchEventManager/backend
./venv/Scripts/python.exe -m pip install pyinstaller
./venv/Scripts/python.exe -m pip freeze | grep -i -E "^(pyinstaller|pyinstaller-hooks-contrib)==" > requirements-build.txt
cat requirements-build.txt
```

The last two commands record the exact PyInstaller version in `requirements-build.txt`.
On another laptop, install the same version with:

```bash
./venv/Scripts/python.exe -m pip install -r requirements-build.txt
```

---

## 2. Create the seed database (your venues, no saved events)

The installer ships a seed database. A new install copies it into the user's AppData on first start.
An existing install never overwrites its own database.

This command makes a **copy**. Your live database in AppData isn't changed.

```bash
./venv/Scripts/python.exe -c "import sqlite3,os; s=sqlite3.connect(os.path.join(os.environ['APPDATA'],'search-events-manager','events_manager.db')); d=sqlite3.connect('events_manager.db'); s.backup(d); d.execute('DELETE FROM my_events'); d.commit(); d.execute('VACUUM'); print('venues:', d.execute('select count(*) from venues').fetchone()[0], '| my_events:', d.execute('select count(*) from my_events').fetchone()[0])"
```

It should print the number of venues and `my_events: 0`.
The file `backend/events_manager.db` is ignored by Git.

---

## 3. Build the backend .exe

```bash
./venv/Scripts/python.exe -m PyInstaller --clean --noconfirm SearchEventsBackend.spec
```

This takes about 5-10 minutes. The result is:

```
backend/dist/SearchEventsBackend/SearchEventsBackend.exe
```

---

## 4. Test the backend .exe on its own

Start it:

```bash
./dist/SearchEventsBackend/SearchEventsBackend.exe --host 127.0.0.1 --port 8002
```

Leave it running and open a **second Git Bash window**:

```bash
curl -s http://127.0.0.1:8002/health
curl -s "http://127.0.0.1:8002/api/ticketmaster/search?region=saint_louis&size=5" | head -c 300; echo
curl -s "http://127.0.0.1:8002/api/ticketmaster/search?region=saint_louis&venue_mode=my_venues&size=5" | head -c 300; echo
curl -s http://127.0.0.1:8002/api/diagnostics/logs | head -c 300; echo
```

You should see:
- `{"status":"ok"}` from `/health`
- JSON with `"events"` from both searches
- a JSON list of log files from the diagnostics check

If anything fails, copy the output from the first window, where the `.exe` prints its errors.
When you're done, press **Ctrl+C** in the first window.

---

## 5. Build the desktop installer

```bash
cd ../frontend
npm run dist:win
```

This builds the React app and then the Windows installer.
It downloads Electron and the NSIS tools from GitHub the first time.

**Outputs:**

| What | Where |
|---|---|
| Installer | `frontend/dist-electron/SearchEventsManager Setup 1.0.0.exe` |
| Test without installing | `frontend/dist-electron/win-unpacked/SearchEventsManager.exe` |

---

## 6. Test the desktop app

Run `frontend/dist-electron/win-unpacked/SearchEventsManager.exe` and check:

- [ ] Ticketmaster search (Saint Louis and Chicago), paging stays in date order
- [ ] Search progress panel, **Cancel** and **Search Again**
- [ ] Venues: **Fetch Events** dialog and **View Events**
- [ ] City Winery, The Sheldon and Jazz at the Bistro return events
- [ ] **My Venues Only** combines all sources
- [ ] Save to My Events, Remove event, Remove venue dialogs
- [ ] **▶ YouTube** and **Get Tickets** open in the normal web browser
- [ ] **Ctrl+Shift+L** (Logs) and **Ctrl+Shift+D** (Database) dialogs
- [ ] **❓ Help** page

The app's log is:

```
%APPDATA%\search-events-manager\app.log
```

It also appears in the Logs dialog (Ctrl+Shift+L).

---

## If something fails

| Problem | What to do |
|---|---|
| Step 3 fails with `Unable to find 'events_manager.db'` | Step 2 didn't run in the `backend` folder. Run it again from `backend`. |
| Step 4: port 8002 already in use | The dev backend or the desktop app is still running. Stop it and try again. |
| Step 5 fails with a download or certificate error | The company network is probably blocking GitHub. Run step 5 on the home laptop instead. |
| The app shows **"Backend failed to start"** | Check `app.log` with Ctrl+Shift+L, or open it in Notepad. |

---

## Notes

- **API keys in the installer:** the installer includes `backend/ticketmaster.env` (the seed key file). Anyone with the installer can read the key inside it. Don't post the installer publicly.
- **Build output is not committed:** `backend/build`, `backend/dist`, `frontend/dist-electron` and `backend/events_manager.db` are all ignored by Git.
- **Turning off the troubleshooting dialogs:** add `DIAGNOSTICS_ENABLED=false` to `%APPDATA%\search-events-manager\.env` before sharing the app.
