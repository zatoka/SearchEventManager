"""
Troubleshooting endpoints: read the app's log files and browse the database.

Opened from the frontend with hidden hotkeys (Ctrl+Shift+L logs, Ctrl+Shift+D database).

Safety:
- READ-ONLY: the database is opened with SQLite "mode=ro"; nothing can be changed.
- Only log files inside the app's own data folders are listed; file names are
  matched against that list (no paths accepted from the request).
- The .env key file is never exposed, and API key values are masked in log text.
- Turn everything off with DIAGNOSTICS_ENABLED=false in
  %APPDATA%\\search-events-manager\\.env  (takes effect on the next request).
"""
import os
import re
from datetime import datetime
from pathlib import Path

import aiosqlite
from fastapi import APIRouter, HTTPException, Query

from config import LOG_DIR, USER_ENV_FILE, _read_env_file, get_user_data_dir
from database import DB_PATH

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])

MAX_LOG_BYTES = 2 * 1024 * 1024     # read at most the last 2 MB of a log file
MAX_ROWS = 500


def _enabled() -> bool:
    value = _read_env_file(USER_ENV_FILE).get("DIAGNOSTICS_ENABLED", "") or \
        os.getenv("DIAGNOSTICS_ENABLED", "")
    return value.strip().lower() not in ("false", "0", "no", "off")


def _require_enabled():
    if not _enabled():
        raise HTTPException(status_code=403, detail="Diagnostics are disabled (DIAGNOSTICS_ENABLED=false).")


# ── Logs ───────────────────────────────────────────────────────────────────

def _log_files() -> dict:
    """{id: Path} of readable log files. id is what the client sends back."""
    files = {}
    if LOG_DIR.is_dir():
        for p in LOG_DIR.glob("*.log"):
            files[f"eventlogs/{p.name}"] = p
    data_dir = get_user_data_dir()
    if data_dir.is_dir():
        for p in data_dir.glob("*.log"):              # e.g. Electron app.log
            files[p.name] = p
    return files


def _secret_values() -> list:
    """Key values to mask in log text (never returned to the client)."""
    env = _read_env_file(USER_ENV_FILE)
    return [v for k, v in env.items() if ("KEY" in k or "SECRET" in k or "TOKEN" in k) and len(v) >= 8]


def _mask(text: str) -> str:
    for secret in _secret_values():
        text = text.replace(secret, "***")
    # apikey=... in URLs, x-api-key headers
    text = re.sub(r"(?i)(apikey=|api[_-]?key[\"']?\s*[:=]\s*[\"']?)[^&\s\"',}]+", r"\1***", text)
    return text


@router.get("/logs")
async def list_logs():
    _require_enabled()
    items = []
    for log_id, path in _log_files().items():
        stat = path.stat()
        items.append({
            "id": log_id,
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        })
    items.sort(key=lambda i: i["modified"], reverse=True)
    return {"log_dir": str(LOG_DIR), "files": items}


@router.get("/logs/read")
async def read_log(
    id: str = Query(..., description="Log id from /diagnostics/logs"),
    lines: int = Query(500, ge=10, le=5000),
):
    _require_enabled()
    path = _log_files().get(id)
    if path is None:
        raise HTTPException(status_code=404, detail="Log file not found")

    size = path.stat().st_size
    with open(path, "rb") as f:
        if size > MAX_LOG_BYTES:
            f.seek(size - MAX_LOG_BYTES)
        data = f.read().decode("utf-8", errors="replace")

    all_lines = data.splitlines()
    tail = all_lines[-lines:]
    return {
        "id": id,
        "size_bytes": size,
        "total_lines_read": len(all_lines),
        "returned_lines": len(tail),
        "truncated": size > MAX_LOG_BYTES or len(all_lines) > len(tail),
        "text": _mask("\n".join(tail)),
    }


# ── Database (read-only) ───────────────────────────────────────────────────

async def _connect_ro():
    if not Path(DB_PATH).exists():
        raise HTTPException(status_code=404, detail="Database file not found")
    db = await aiosqlite.connect(f"file:{Path(DB_PATH).as_posix()}?mode=ro", uri=True)
    db.row_factory = aiosqlite.Row
    return db


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


async def _table_names(db) -> list:
    async with db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ) as cur:
        return [r["name"] for r in await cur.fetchall()]


@router.get("/db/schema")
async def db_schema():
    _require_enabled()
    db = await _connect_ro()
    try:
        tables = []
        for name in await _table_names(db):
            q = _quote(name)
            async with db.execute(f"PRAGMA table_info({q})") as cur:
                columns = [{
                    "name": c["name"], "type": c["type"], "not_null": bool(c["notnull"]),
                    "default": c["dflt_value"], "primary_key": bool(c["pk"]),
                } for c in await cur.fetchall()]
            async with db.execute(f"SELECT COUNT(*) AS n FROM {q}") as cur:
                row_count = (await cur.fetchone())["n"]
            async with db.execute(
                "SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name=? ORDER BY name", (name,)
            ) as cur:
                indexes = [{"name": i["name"], "sql": i["sql"]} for i in await cur.fetchall()]
            async with db.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (name,)
            ) as cur:
                create_sql = (await cur.fetchone())["sql"]
            tables.append({"name": name, "row_count": row_count, "columns": columns,
                           "indexes": indexes, "create_sql": create_sql})

        stat = Path(DB_PATH).stat()
        return {
            "db_path": str(DB_PATH),
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            "tables": tables,
        }
    finally:
        await db.close()


@router.get("/db/table/{table}")
async def db_table_rows(
    table: str,
    limit: int = Query(50, ge=1, le=MAX_ROWS),
    offset: int = Query(0, ge=0),
):
    _require_enabled()
    db = await _connect_ro()
    try:
        if table not in await _table_names(db):     # only real table names
            raise HTTPException(status_code=404, detail="Table not found")
        q = _quote(table)
        async with db.execute(f"SELECT COUNT(*) AS n FROM {q}") as cur:
            total = (await cur.fetchone())["n"]
        async with db.execute(f"SELECT * FROM {q} LIMIT ? OFFSET ?", (limit, offset)) as cur:
            rows = await cur.fetchall()
            columns = [d[0] for d in cur.description] if cur.description else []
        return {
            "table": table, "total": total, "limit": limit, "offset": offset,
            "columns": columns,
            "rows": [[r[c] for c in columns] for r in rows],
        }
    finally:
        await db.close()
