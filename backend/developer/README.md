# Ticketmaster Discovery API v2 Test Kit

This is a standalone test kit for the SearchEventsManager backend. It does not modify the application's existing Python modules.

## Contents
- `ticketmaster_test.py` — sequential API test runner; Python standard library only.
- `postman/Ticketmaster_Discovery_API_v2.postman_collection.json` — import into Postman.
- `postman/Ticketmaster_Local.postman_environment.json` — import into Postman.
- `.env.example` — template for the Python runner.
- `results/` — JSON test reports are written here.

## A. Python test runner (Windows)
1. Copy this `postman` folder into your existing `SearchEventsManager/backend/` folder.
2. In `backend/postman`, copy `.env.example` to `.env`.
3. Edit `.env` and set `TICKETMASTER_API_KEY` to your own valid Ticketmaster consumer key.
4. Open Command Prompt or PowerShell:
   ```powershell
   cd path\to\SearchEventsManager\backend\postman
   python ticketmaster_test.py
   ```
5. Review the console summary and the detailed JSON file created under `results`.

No pip installation is needed; the runner uses Python's standard library.

Optional: change `TM_CITY`, `TM_STATE_CODE`, `TM_COUNTRY_CODE`, or `TM_POSTAL_CODE` in `.env`.

## B. Postman
1. Open Postman.
2. Select **Import** and import both JSON files from the `postman` subfolder.
3. Select environment **Ticketmaster Discovery API - Local**.
4. Set its `apikey` variable to your Ticketmaster consumer key. Save the environment.
5. Run the collection in this order. Search requests populate IDs used by detail requests:
   - Event Search -> Event Details -> Event Images
   - Attraction Search -> Attraction Details
   - Classification Search -> Classification Details, Genre Details, Segment Details, Sub-Genre Details
   - Venue Search -> Venue Details
   - Find Suggest
6. Use Collection Runner to run all requests in folder/order. If an ID variable remains blank, run its corresponding Search request first.

## Endpoints covered
1. `GET /events.json`
2. `GET /events/{id}.json`
3. `GET /events/{id}/images.json`
4. `GET /attractions.json`
5. `GET /attractions/{id}.json`
6. `GET /classifications.json`
7. `GET /classifications/{id}.json`
8. `GET /classifications/genres/{id}.json`
9. `GET /classifications/segments/{id}.json`
10. `GET /classifications/subgenres/{id}.json`
11. `GET /venues.json`
12. `GET /venues/{id}.json`
13. `GET /suggest.json`

Three additional Event Search examples exercise keyword/category, postal code, and source filters.

## Important notes
- These are read-only GET requests; they do not purchase tickets or modify Ticketmaster data.
- Ticketmaster's published default limits are 5,000 calls/day and 5 requests/second. Avoid repeatedly running the full collection.
- The detail/image requests require IDs obtained from their corresponding search requests.
- A 404 on a dependent detail endpoint may mean the preceding search returned no records or the ID is unavailable. Check the saved environment variables.
- Keep `.env` private. Do not commit it or share screenshots containing the key.
- This test kit intentionally reads its own `backend/postman/.env`; it does not alter `backend/config.py` or the application's runtime configuration.

Official docs: https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/
