"""Configuration for SearchEventsManager API.

Paths are resolved per Windows user, not tied to the developer's computer.
Environment variables can override the defaults.
"""
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime


# Project/source directory. Do not use this for writable runtime data in a packaged app.
BASE_DIR = Path(__file__).resolve().parent
APP_NAME = "search-events-manager"


def get_user_data_dir() -> Path:
    """Return a writable, per-user application-data directory on Windows."""
    appdata = os.getenv("APPDATA")
    if appdata:
        root = Path(appdata)
    else:
        # Fallback for development or non-Windows environments.
        root = Path.home() / ".config"
    return root / APP_NAME


# LOG_DIR is backward-compatible with the existing LOG_DIR environment variable.
LOG_DIR = Path(os.getenv("LOG_DIR", str(get_user_data_dir() / "eventlogs"))).expanduser()
LOG_DIR.mkdir(parents=True, exist_ok=True)


# ── Ticketmaster API Configuration ───────────────────────────────────────────
# The API key lives in ONE place per Windows user:
#     %APPDATA%\search-events-manager\.env
#
# On first start, if that file does not exist, it is created by copying the
# seed file "ticketmaster.env" shipped with the app (same pattern as the
# seed events_manager.db). After that, the AppData file is never overwritten.
#
# To replace the key on a machine: edit %APPDATA%\search-events-manager\.env
# (takes effect on the next Ticketmaster call, no restart needed), or delete
# it and restart the app so it is re-copied from the seed.
#
# Never put a real key in this source file.
TICKETMASTER_BASE_URL = "https://app.ticketmaster.com/discovery/v2"

USER_ENV_FILE = get_user_data_dir() / ".env"
SEED_ENV_FILE_NAME = "ticketmaster.env"
_PLACEHOLDER_KEYS = {
    "",
    "your_api_key_here",
    "paste_your_ticketmaster_api_key_here",
}


class TicketmasterApiKeyMissing(Exception):
    """Raised when no usable Ticketmaster API key is configured."""


def _find_seed_env_file() -> Path | None:
    """Locate the seed ticketmaster.env shipped with the source or installer."""
    candidates = [BASE_DIR / SEED_ENV_FILE_NAME]

    # PyInstaller bundle directory, when running frozen.
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        candidates.append(Path(bundle_dir) / SEED_ENV_FILE_NAME)

    # Electron extraResources layout:
    #   resources/backend/ticketmaster.env
    #   resources/backend/SearchEventsBackend/SearchEventsBackend.exe
    executable_dir = Path(sys.executable).resolve().parent
    candidates.extend([
        executable_dir / SEED_ENV_FILE_NAME,
        executable_dir.parent / SEED_ENV_FILE_NAME,
        executable_dir.parent.parent / SEED_ENV_FILE_NAME,
    ])

    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue
    return None


def ensure_user_env_file() -> bool:
    """Copy the seed key file to AppData if the user file does not exist yet.

    Returns True if the user .env file exists after the call.
    An existing user file is never overwritten.
    """
    if USER_ENV_FILE.exists():
        return True

    seed = _find_seed_env_file()
    if seed is None:
        return False

    try:
        USER_ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(seed, USER_ENV_FILE)
        print(f"[config] Copied Ticketmaster key seed file to {USER_ENV_FILE}")
        return True
    except OSError as e:
        print(f"[config] Could not copy seed key file to {USER_ENV_FILE}: {e}")
        return False


def _read_env_file(path: Path) -> dict:
    """Parse a simple KEY=VALUE file. Blank lines and # comments are ignored."""
    values = {}
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError:
        return values

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def get_ticketmaster_api_key() -> str:
    """Return the Ticketmaster API key, re-read on every call.

    Order:
      1. %APPDATA%\\search-events-manager\\.env  (the single place to edit)
      2. TICKETMASTER_API_KEY environment variable (fallback for developers)

    Raises TicketmasterApiKeyMissing with setup instructions if neither
    contains a usable key.
    """
    ensure_user_env_file()

    key = _read_env_file(USER_ENV_FILE).get("TICKETMASTER_API_KEY", "").strip()
    if key in _PLACEHOLDER_KEYS:
        key = os.getenv("TICKETMASTER_API_KEY", "").strip()

    if key in _PLACEHOLDER_KEYS:
        raise TicketmasterApiKeyMissing(
            "Ticketmaster API key is not configured. "
            f"Add the line TICKETMASTER_API_KEY=<your key> to {USER_ENV_FILE}"
        )
    return key


def get_ticketmaster_api_secret() -> str:
    """Return the optional Ticketmaster API secret (not used by Discovery API)."""
    secret = _read_env_file(USER_ENV_FILE).get("TICKETMASTER_API_SECRET", "").strip()
    return secret or os.getenv("TICKETMASTER_API_SECRET", "").strip()


def is_ticketmaster_api_key_configured() -> bool:
    """Return True if a usable key is available, without raising."""
    try:
        get_ticketmaster_api_key()
        return True
    except TicketmasterApiKeyMissing:
        return False


# Create the AppData key file from the seed at startup, if needed.
ensure_user_env_file()

# Backward-compatible module constants. They are a snapshot taken at import
# time; application code should call get_ticketmaster_api_key() instead so a
# key edited in the AppData .env is picked up without a restart.
try:
    TICKETMASTER_API_KEY = get_ticketmaster_api_key()
except TicketmasterApiKeyMissing:
    TICKETMASTER_API_KEY = ""
    print(f"[config] WARNING: Ticketmaster API key not configured. Edit {USER_ENV_FILE}")
TICKETMASTER_API_SECRET = get_ticketmaster_api_secret()


# ── Default Search Settings ──────────────────────────────────────────────────
DEFAULT_CITY = "Saint Louis"
DEFAULT_STATE_CODE = "MO"
DEFAULT_DAYS_AHEAD = 90
DEFAULT_PAGE_SIZE = 100


# ── Logging Configuration ────────────────────────────────────────────────────
LOG_API_CALLS = True
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_log_file_path(log_name: str = "api_calls") -> Path:
    """Return today's log file path, creating the directory if needed."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    return LOG_DIR / f"{log_name}_{today}.log"


def get_current_log_file() -> Path:
    """Return the current day's API log file path."""
    return get_log_file_path("api_calls")


# ── API Rate Limits ──────────────────────────────────────────────────────────
RATE_LIMIT_CALLS_PER_SECOND = 5
RATE_LIMIT_CALLS_PER_DAY = 5000
