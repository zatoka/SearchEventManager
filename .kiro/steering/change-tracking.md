---
inclusion: always
---

# Change tracking for SearchEventsManager

This project does not use Git. The user syncs changed files manually to a remote laptop.
Every time a source, config, or script file in the project is created, modified, or deleted, follow these rules.

## Location

Root: `C:\Users\p2801412\AppData\Roaming\search-events-manager\changelogs\`

- `CODE_CHANGE_LOG.md` - the running log (newest entry at the top).
- One folder per change set: `YYYY-MM-DD_short-description\` (e.g. `2026-11-06_api-key-cleanup\`).

## For each change set

1. Before editing an existing file, copy the current version to
   `<change-set>\original\<path relative to project root>` (e.g. `original\backend\config.py`).
2. After editing and verifying, copy the final version to
   `<change-set>\updated\<path relative to project root>`.
   New files go only in `updated\`. Deleted files go only in `original\` and are noted as deleted.
3. Add an entry to `CODE_CHANGE_LOG.md` with: date, change-set folder name, list of files
   (relative paths, marked new/modified/deleted), what and why, verification, rollback note.
4. Keep the relative folder structure so the `updated\` folder can be copied straight over the
   project root on the remote laptop.

## Never copy into changelogs

- Real `.env` files, API keys, tokens, passwords
- `events_manager.db` or other database files
- `venv\`, `node_modules\`, `dist\`, build output
