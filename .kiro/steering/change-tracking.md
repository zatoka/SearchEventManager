---
inclusion: always
---

# Change tracking for SearchEventsManager

The project is tracked in Git and pushed to a private GitHub repo:
`https://github.com/zatoka/SearchEventManager` (branch `main`).
The remote laptop gets changes with `git pull`. Manual file copies into
`%APPDATA%\search-events-manager\changelogs\` are no longer made.

## Rules

1. Git history is the change log. Do not create `changelogs\` copies for new changes.
   The existing `changelogs\` folder is kept as history from before Git.
2. Only commit or push when the user asks. Stage specific files by name, not `git add .`.
3. Before every commit, show the list of staged files and confirm no secrets are included.
4. Commit messages: short summary line, then what changed and why.
   Do not let cmd expand `%VAR%` in messages (it leaks local paths/usernames).
5. Repo-local identity only: `user.name=zatoka`. Never change global git config.

## Never commit

- `backend/ticketmaster.env` or any real `.env` (API keys, secrets)
- `events_manager.db` or other database files
- `venv/`, `node_modules/`, `dist/`, `dist-electron/`, build output
- `history-*`, `snap*`, `response.txt`, `list_command_for_remote.txt`
- `Documentation/buyflow-webex-listener-flow.md` (not part of this project)

These are listed in the root `.gitignore`. If a new private file appears, add it there first.

## Remote laptop

- First time: `git clone https://github.com/zatoka/SearchEventManager.git`, then copy
  `backend/ticketmaster.env` over separately (it is not in Git).
- After that: `git pull`.
