# SearchEventsManager --- Kiro Handoff

**Handoff date:** November 5, 2026\
**Development scope:** FastAPI backend + React/Vite frontend. Electron
desktop packaging is intentionally outside this handoff.

## First steps in Kiro

1.  Extract the `SearchEventsManager_Source` package.
2.  Open the extracted `SearchEventsManager_Source` folder in Kiro using
    **Open Folder**.
3.  Read this file before making changes.
4.  Open `PROJECT_TODO.md` from the companion Reference package.
5.  Ask Kiro to inspect the current source and summarize the
    architecture before editing anything.

Suggested first prompt for Kiro:

> Read `KIRO_HANDOFF.md` and inspect the existing SearchEventsManager
> source. Do not modify files yet. Summarize the architecture, identify
> the backend and frontend entry points, explain how the frontend calls
> the backend, identify configuration and dependency requirements, and
> report any uncertainties. Preserve existing behavior and wait for
> approval before making changes.

## Project architecture

-   **Backend:** Python / FastAPI.
-   **Frontend:** React / Vite.
-   **Backend entry point:** `backend/main.py`.
-   **API routes:** `backend/routes/`.
-   **Event and venue integrations:** `backend/scrapers/`.
-   **Database logic:** `backend/database.py`.
-   **Data models:** `backend/models.py`.
-   **Backend configuration:** `backend/config.py`.
-   **Python dependency list:** `backend/requirements.txt`.
-   **Frontend source:** `frontend/src/`.
-   **Frontend dependency manifest:** `frontend/package.json`.
-   **Frontend lockfile:** `frontend/package-lock.json`.
-   **Vite configuration:** `frontend/vite.config.js`.

## Dependencies and setup

The source package intentionally does not contain installed libraries or
generated build output.

When the computer permits development setup:

### Backend

From the project root:

``` bash
cd backend
python -m venv venv
```

On Windows, activate the environment:

``` powershell
.\venv\Scripts\Activate.ps1
```

Then install dependencies:

``` bash
python -m pip install -r requirements.txt
```

### Frontend

Open another terminal:

``` bash
cd frontend
npm ci
```

These commands require working Python/Node installations and permission
to download packages. If a command is blocked, capture the exact error
and check the computer's security policy rather than attempting to
bypass it.

## Configuration and credentials

-   Example environment files are included where present.
-   Real `.env` files, API keys, tokens, and passwords must not be
    included in shared archives.
-   Check `backend/config.py`, `backend/.env.example`, and the relevant
    scraper before deciding which environment variables are required.
-   Supply the Ticketmaster API key locally. Do not commit it or paste
    it into shared documentation.

## Database safety

-   No application database is included in the source package.
-   Inspect `backend/database.py` and configuration to establish the
    database path and initialization behavior before running the
    application.
-   Do not overwrite, migrate, or initialize over an existing database
    without first making a backup and obtaining approval.

## Development guardrails

1.  Inspect the relevant current source file before changing it.
2.  Preserve existing working functionality and API contracts.
3.  Make focused, incremental changes; avoid broad refactoring unless
    requested.
4.  Do not assume a feature is missing just because it is not described
    here---verify the current source.
5.  Do not reintroduce Electron or desktop packaging unless explicitly
    requested.
6.  Do not run migrations or destructive commands without a backup and
    approval.
7.  Keep credentials and private database files out of source packages.

## Companion reference package

The separate Reference package is intended to contain project
documentation, tests, Postman collection/environment files, developer
testing materials, and the development TODO snapshot. Use those
materials as supporting context, but verify implementation status
against the current source.
