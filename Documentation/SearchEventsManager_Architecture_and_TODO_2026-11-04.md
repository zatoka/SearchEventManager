# SearchEventsManager

## Database Architecture and Project TODO

**Updated:** November 4, 2026

------------------------------------------------------------------------

# 1. Current Architecture

## Data model

The application now uses a simplified database model:

  -----------------------------------------------------------------------
  Table                   Purpose                 Status
  ----------------------- ----------------------- -----------------------
  `venues`                Venues explicitly       Active; single source
                          selected or manually    of truth for saved
                          added by the user       venues

  `my_events`             Events explicitly saved Active
                          by the user             

  `regions`               Geographic metro-region Active
                          definitions             

  `cities`                Geographic city, state, Active
                          county, and region data 

  `sqlite_sequence`       SQLite-managed sequence Internal SQLite table
                          metadata                
  -----------------------------------------------------------------------

The obsolete `events` and `user_venues` tables have been removed from
the live database.

## Event retrieval and persistence

-   Ticketmaster venue discovery is dynamic. Search results remain
    temporary until the user selects a venue.
-   Saved venues are stored in `venues`.
-   Venue-specific event retrieval for Ticketmaster, MetroTix, and City
    Winery is dynamic. Results are returned to the frontend and are not
    persisted in an event cache.
-   General Ticketmaster regional search is dynamic and does not write
    search results to the database.
-   Only events explicitly saved by the user are stored, in `my_events`.
-   My Events retains its save, list, delete, and expired-event cleanup
    behavior.

## Application flow

### My Venues

-   `GET /venues/` returns saved venues.
-   Ticketmaster discovery endpoints return temporary search results.
-   Selecting a discovered venue creates a record in `venues`.
-   The compatibility routes `/venues/my` and `/venues/my/{venue_id}`
    remain in `backend/routes/venues.py` for existing frontend
    compatibility.
-   Removing a venue deletes its `venues` record. It does not delete
    saved My Events.

### Venue Events

-   The frontend Events page calls `fetchVenueEvents(venueId)` for
    venue-specific results.
-   Backend `POST /venues/{venue_id}/fetch` retrieves fresh events and
    returns them directly.
-   Venue event results are temporary and are not written to SQLite.
-   The Events page hides the Remove action for temporary venue results.

### My Events

-   The frontend loads explicitly saved events from `/my-events/`.
-   Saving and deleting My Events continues to use the `my_events`
    table.
-   Existing saved events are independent of the saved-venue list.

## Relevant source files

  -----------------------------------------------------------------------
  File                                Current responsibility
  ----------------------------------- -----------------------------------
  `backend/database.py`               Creates and migrates active tables:
                                      `venues`, `my_events`, `regions`,
                                      and `cities`; maintains geographic
                                      fields and indexes

  `backend/routes/venues.py`          Saved venue CRUD and dynamic
                                      Ticketmaster venue discovery

  `backend/routes/events.py`          Dynamic venue event retrieval,
                                      Ticketmaster search and filters,
                                      and My Events operations

  `frontend/src/pages/Events.jsx`     Displays temporary venue results or
                                      explicitly saved My Events

  `frontend/src/api/client.js`        Frontend API functions, including
                                      `fetchVenueEvents`, Ticketmaster
                                      search, and My Events
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 2. Completed Database Simplification --- November 4, 2026

The following changes were implemented and tested:

1.  Changed `backend/routes/venues.py` so `venues` is the single source
    of truth for saved venues. Compatibility `/venues/my` routes were
    retained.
2.  Changed venue-specific event fetching in `backend/routes/events.py`
    to return fresh results without inserting them into the old `events`
    cache.
3.  Updated `frontend/src/pages/Events.jsx` to use
    `fetchVenueEvents(venueId)` for venue-specific results. My Events
    continues to load from `/my-events/`.
4.  Removed cached-event routes and the obsolete `user_venues` route
    from `backend/routes/events.py`.
5.  Changed `backend/database.py` so it no longer creates `events` or
    `user_venues`.
6.  Removed the two remaining cached-event deletion statements from
    `backend/routes/venues.py`.
7.  Ran a source-code dependency audit. The search for `user_venues`,
    `FROM events`, `INTO events`, `UPDATE events`, `DELETE FROM events`,
    and `JOIN events` returned no matches in `backend/routes`,
    `backend/database.py`, or `frontend/src`.
8.  Created a fresh pre-cleanup database backup:
    `events_manager_backup_final_cleanup_20261104_114253.db`
9.  Dropped `events` and `user_venues` from the live SQLite database.

## Verification results

-   Python syntax checks passed for the revised backend files.
-   My Events count remained **2** after the changes and after table
    removal.
-   Before the final cleanup, an Enterprise Center venue fetch returned
    **73 events**.
-   The `events` cache contained **0 rows** after that fetch, confirming
    the results were not persisted.
-   Ticketmaster regional searches for Saint Louis and Chicago were
    tested successfully.
-   My Venues, venue event fetching, and My Events were tested
    successfully before physical table removal.
-   After the final table removal, the user confirmed the final
    application checks passed: My Venues, venue Fetch Events, My Events,
    and Ticketmaster Saint Louis/Chicago searches.
-   Final live database tables: `cities`, `my_events`, `regions`,
    `sqlite_sequence`, `venues`.
-   Final `my_events` row count: **2**.

## Backup and recovery note

The pre-cleanup backup is located in the user's application data
directory:

`%APPDATA%\search-events-manager\events_manager_backup_final_cleanup_20261104_114253.db`

The backup was created immediately before dropping the two obsolete
tables. Keep it until the simplified application has been used and
validated over time.

------------------------------------------------------------------------

# 3. Working Project TODO

Legend: `[x]` completed; `[ ]` outstanding.

## A. Database and event architecture

-   [x] Make `venues` the single source of truth for saved venues.
-   [x] Keep Ticketmaster venue discovery temporary until a venue is
    selected.
-   [x] Fetch venue events dynamically rather than persisting an event
    cache.
-   [x] Keep explicitly saved events in `my_events`.
-   [x] Remove cached-event endpoints and old `user_venues` route.
-   [x] Stop creating the obsolete `events` and `user_venues` tables.
-   [x] Remove remaining source-code references to the obsolete tables.
-   [x] Back up the live database and drop the obsolete tables.
-   [x] Verify the remaining tables and preserve the two saved My Events
    records.
-   [ ] Continue regression testing the simplified architecture during
    subsequent development.

## B. Ticketmaster Event Search

-   [x] Separate Saint Louis Metro and Chicago Metro searches.
-   [x] Add a region selector.
-   [x] Apply a 50-mile geographic radius for regional searches.
-   [x] Use a manual **Search Events** button instead of searching
    automatically.
-   [x] Restore Wrigley Field venue-specific fetching; it previously
    returned 81 events.
-   [ ] Add pagination and allow browsing beyond the first 100 events.
-   [ ] Fix the navigation/Events-page "No events found" issue.
-   [ ] Add a **My Venues Only** filter.
-   [ ] Continue verifying regional and venue-specific search behavior
    independently.

## C. Venue Management and Discovery

-   [x] Keep selected/saved venues separate from temporary Ticketmaster
    discovery results.
-   [x] Support selecting a discovered venue and saving it in `venues`.
-   [ ] Ensure venue dropdowns show cities appropriate to the selected
    region.
-   [ ] Ensure venue searches use the selected region correctly.
-   [ ] Review venue discovery/importing coverage and accuracy.
-   [ ] Verify the Ticketmaster venue-discovery button and related
    interactions remain reliable.
-   [ ] Continue checking venue records for correct city, county,
    region, and geographic data.

## D. My Venues and My Events

-   [x] Make `venues` the saved-venue collection; remove dependence on
    `user_venues`.
-   [x] Ensure removing a venue does not delete explicitly saved My
    Events.
-   [x] Preserve My Events save, list, delete, and expired-event cleanup
    behavior.
-   [x] Verify the two existing My Events records survived the
    architecture changes.
-   [ ] Verify manual My Events saving from each relevant event-search
    result type.
-   [ ] Verify Ticketmaster search results can be saved to My Events and
    remain independent of venue removal.

## E. User Interface and Reliability

-   [ ] Replace browser-native confirmation dialogs (for example,
    `window.confirm`) with the application's consistent styled
    confirmation modal.
-   [ ] Audit all confirmation prompts, including add, remove, delete,
    and destructive actions, and standardize them.
-   [ ] Review interface consistency and usability.
-   [ ] Review performance of event and venue searches.
-   [ ] Continue independent verification of venue fetches, regional
    searches, and filters.

## F. Export and Configuration

-   [ ] Add export functionality for event search results:
    -   [ ] Excel (`.xlsx`)
    -   [ ] PDF (`.pdf`)
-   [ ] Keep the Ticketmaster API key in one place only.
-   [ ] Eliminate hardcoded duplicate keys and fallback values.
-   [ ] Use shared configuration for backend, tests, and desktop
    application.
-   [ ] Keep the API key out of packaged source and distribution
    artifacts.
-   [ ] Rotate the Ticketmaster API key that was previously exposed.

------------------------------------------------------------------------

# 4. Regression Test Checklist

Run these checks after relevant frontend, backend, or database changes:

1.  My Venues lists saved venues.
2.  Ticketmaster venue discovery returns temporary results and does not
    save them until selected.
3.  Selecting a discovered venue adds it to My Venues.
4.  Removing a venue removes only the venue record.
5.  Fetching venue events returns fresh results without recreating an
    `events` table or writing event rows.
6.  Ticketmaster venue-specific fetching works.
7.  MetroTix venue fetching works.
8.  City Winery venue fetching works.
9.  Ticketmaster Saint Louis regional search works.
10. Ticketmaster Chicago regional search works.
11. Ticketmaster pagination works beyond the first 100 results once
    implemented.
12. Events can be explicitly saved to My Events.
13. My Events can be listed and deleted.
14. Expired My Events cleanup behaves correctly.
15. Saved My Events remain after removing their associated venue.
16. Export to Excel and PDF works once implemented.
17. Confirmation prompts use the consistent styled modal once
    implemented.

------------------------------------------------------------------------

# 5. Development Safety Rules

-   Continue working one file at a time.
-   Inspect the current project file before preparing a replacement.
-   Preserve working Ticketmaster, MetroTix, City Winery, My Venues, and
    My Events functionality.
-   Run Python syntax checks after backend Python changes.
-   Run the application and test affected flows before proceeding to the
    next file.
-   Back up the live database before any schema migration or destructive
    database operation.
-   Do not drop or rename active tables without auditing backend and
    frontend dependencies first.
-   Do not edit generated `backend/dist` output manually; rebuild
    packaged output after source changes.
-   Keep the user's live database in
    `%APPDATA%\search-events-manager\events_manager.db`; do not
    overwrite it with a bundled seed database during routine
    development.
