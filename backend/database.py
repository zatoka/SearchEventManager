"""SQLite database setup for SearchEventsManager.

The live database is stored in the current Windows user's AppData folder.
On first launch, an included database is copied there so updates do not write
inside the installation directory or overwrite the user's live database.
"""
import os
import shutil
import sys
import warnings
from pathlib import Path

import aiosqlite

APP_NAME = "search-events-manager"
BASE_DIR = Path(__file__).resolve().parent


def get_user_data_dir() -> Path:
    """Return a writable, per-user application-data directory."""
    appdata = os.getenv("APPDATA")
    if appdata:
        root = Path(appdata)
    else:
        root = Path.home() / ".config"
    return root / APP_NAME


def _database_path() -> Path:
    """Resolve the persistent DB path, honoring an explicit environment override."""
    override = os.getenv("SEARCH_EVENTSMANAGER_DB_PATH") or os.getenv("DB_PATH")
    if override:
        target = Path(override).expanduser()
    else:
        target = get_user_data_dir() / "events_manager.db"

    target.parent.mkdir(parents=True, exist_ok=True)

    if not target.exists():
        seed = _find_seed_database(target)
        if seed is not None:
            shutil.copy2(seed, target)
        else:
            warnings.warn(
                "No bundled/source events_manager.db was found. A new database will be created at "
                f"{target}. If the app should include preloaded venues, verify the database is packaged.",
                RuntimeWarning,
            )
    return target


def _find_seed_database(target: Path) -> Path | None:
    """Find the database shipped with the app or used by the source checkout."""
    candidates: list[Path] = []

    # Development/source checkout.
    candidates.append(BASE_DIR / "events_manager.db")

    # PyInstaller bundled data directory, when available.
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        candidates.append(Path(bundle_dir) / "events_manager.db")

    # Electron extraResources layout:
    # resources/backend/events_manager.db
    # resources/backend/SearchEventsBackend/SearchEventsBackend.exe
    executable_dir = Path(sys.executable).resolve().parent
    candidates.extend([
        executable_dir / "events_manager.db",
        executable_dir.parent / "events_manager.db",
        executable_dir.parent.parent / "events_manager.db",
    ])

    for candidate in candidates:
        try:
            candidate = candidate.resolve()
            if candidate != target.resolve() and candidate.is_file():
                return candidate
        except OSError:
            continue
    return None


DB_PATH = _database_path()


async def _add_column_if_missing(db, table, column, definition):
    """Add a database column only if it does not already exist."""
    async with db.execute(f"PRAGMA table_info({table})") as cursor:
        rows = await cursor.fetchall()

    existing_columns = {row["name"] for row in rows}

    if column not in existing_columns:
        await db.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


async def get_db():
    """Open database and safely apply required schema migrations."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row

    # --------------------------------------------------
    # Original application tables
    # --------------------------------------------------

    await db.execute("""
        CREATE TABLE IF NOT EXISTS venues (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT,
            address TEXT,
            scraper_type TEXT,
            notes TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS my_events (
            id TEXT PRIMARY KEY,
            ticketmaster_id TEXT UNIQUE,
            title TEXT NOT NULL,
            event_date TEXT,
            event_time TEXT,
            day_of_week TEXT,
            venue_name TEXT,
            category TEXT,
            event_url TEXT,
            image_url TEXT,
            price_min REAL,
            price_max REAL,
            description TEXT,
            saved_at TEXT
        )
    """)

        # --------------------------------------------------
    # Geographic tables
    # --------------------------------------------------

    await db.execute("""
        CREATE TABLE IF NOT EXISTS regions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            country_code TEXT NOT NULL DEFAULT 'US'
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            state_code TEXT NOT NULL,
            country_code TEXT NOT NULL,
            county TEXT,
            region_id INTEGER,
            UNIQUE(name, state_code, country_code),
            FOREIGN KEY (region_id) REFERENCES regions(id)
        )
    """)

    # --------------------------------------------------
    # Venue geographic and Ticketmaster fields
    # --------------------------------------------------

    await _add_column_if_missing(
        db, "venues", "ticketmaster_id", "TEXT"
    )

    await _add_column_if_missing(
        db, "venues", "city_id",
        "INTEGER REFERENCES cities(id)"
    )

    await _add_column_if_missing(
        db, "venues", "postal_code", "TEXT"
    )

    await _add_column_if_missing(
        db, "venues", "latitude", "REAL"
    )

    await _add_column_if_missing(
        db, "venues", "longitude", "REAL"
    )

    await _add_column_if_missing(
        db, "venues", "timezone", "TEXT"
    )

    # --------------------------------------------------
    # City geographic fields
    # --------------------------------------------------

    await _add_column_if_missing(
        db, "cities", "county", "TEXT"
    )

    await _add_column_if_missing(
        db, "cities", "region_id",
        "INTEGER REFERENCES regions(id)"
    )

    # --------------------------------------------------
    # Indexes
    # --------------------------------------------------

    await db.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_venues_ticketmaster_id
        ON venues(ticketmaster_id)
    """)

    await db.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_venues_city_id
        ON venues(city_id)
    """)

    await db.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_cities_region_id
        ON cities(region_id)
    """)

    await db.commit()

    return db