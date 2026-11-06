# SearchEventsManager --- Development TODO

**Handoff snapshot:** November 5, 2026\
**Important:** This is a status/priority snapshot from the development
handoff. Verify each item against the current source and runtime before
changing code.

## Architecture and design decisions

-   The application uses a React/Vite frontend and FastAPI backend.
-   The `venues` table is the single source of truth for user-selected
    venues.
-   Ticketmaster venue discovery is temporary until a venue is
    selected/saved.
-   Venue-specific event retrieval (Ticketmaster, MetroTix, City Winery)
    is dynamic and does not write results into an events cache.
-   `my_events` stores only events explicitly saved by the user.
-   `regions` and `cities` remain available for regional
    organization/search.
-   The current saved-venue Ticketmaster identifier column is
    `venues.ticketmaster_id`. Do not rename it without a separately
    planned migration.

## Ticketmaster search modes

The intended search modes are:

1.  **All Venues** --- search events in the selected city/region.
2.  **My Venues Only** --- search across all saved Ticketmaster venues,
    regardless of the selected region.
3.  **Individual Venue** --- search one selected saved venue, regardless
    of the selected region.

Tasks to verify:

-   [ ] Confirm all three search modes work in the current source and
    runtime.
-   [ ] Confirm venue mode takes precedence over region for My Venues
    Only and Individual Venue.
-   [ ] Confirm My Venues Only searches every saved Ticketmaster venue
    with a usable `ticketmaster_id`.
-   [ ] Confirm combined results are deduplicated by Ticketmaster event
    ID.
-   [ ] Confirm combined results are sorted correctly by event
    date/time.
-   [ ] Confirm pagination works across the combined result set.
-   [ ] Confirm Ticketmaster API pagination retrieves results beyond the
    first API page.
-   [ ] Preserve manual search behavior and existing region selector
    behavior.

## Venue management and API checks

-   [ ] Verify `GET /api/venues/` returns saved venues.
-   [ ] Verify `GET /api/venues/my` returns the user's saved venues.
-   [ ] Verify `/api/venues/ticketmaster/search-by-region` performs
    regional venue discovery.
-   [ ] Verify saved venue creation, listing, editing, and deletion.
-   [ ] Verify saved Ticketmaster venue IDs are used correctly for
    individual and My Venues Only event retrieval.

## Packaging and runtime context

-   The current handoff target is backend + React/Vite development only.
-   Electron, PyInstaller, and Windows desktop packaging are
    intentionally excluded from the source handoff.
-   Historical note: on November 5, 2026, the backend PyInstaller build
    and Electron Windows installer build completed successfully. This is
    historical context, not part of the current target.

## Data and security

-   [ ] Keep real `.env` files, API keys, tokens, and passwords out of
    shared archives and repositories.
-   [ ] Back up the database before schema changes or migrations.
-   [ ] Confirm the active database path before running any command that
    initializes or modifies the database.
-   [ ] Review test scripts and Postman environment variables before
    running; provide credentials locally.
