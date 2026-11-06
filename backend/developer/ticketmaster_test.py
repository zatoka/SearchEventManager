"""
Ticketmaster Discovery API v2 test runner.
Uses only Python standard library.

API key lookup (first usable value wins):
  1. TICKETMASTER_API_KEY environment variable, if already set
  2. backend/developer/.env  (optional local override)
  3. %APPDATA%\\search-events-manager\\.env  (the app's single key file)
"""
import json, os, sys, time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from datetime import datetime, timezone, timedelta

HERE = Path(__file__).resolve().parent
ENV_FILE = HERE / ".env"
APPDATA_ENV_FILE = Path(os.getenv("APPDATA") or (Path.home() / ".config")) / "search-events-manager" / ".env"
BASE_URL = os.getenv("TM_BASE_URL", "https://app.ticketmaster.com/discovery/v2").rstrip("/")
DEFAULTS = {"TM_CITY": "Saint Louis", "TM_STATE_CODE": "MO", "TM_COUNTRY_CODE": "US"}
PLACEHOLDER_KEYS = {"", "your_api_key_here", "paste_your_ticketmaster_api_key_here"}

def _load_env_file(path):
    """Load KEY=VALUE pairs without overriding values already set. Placeholders are skipped."""
    if not path.exists(): return
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k == "TICKETMASTER_API_KEY" and v in PLACEHOLDER_KEYS: continue
        if os.environ.get(k, "").strip() in PLACEHOLDER_KEYS or k not in os.environ:
            os.environ[k] = v

def load_env():
    _load_env_file(ENV_FILE)
    _load_env_file(APPDATA_ENV_FILE)
    for k, v in DEFAULTS.items(): os.environ.setdefault(k, v)

def call(path, params=None):
    key = os.getenv("TICKETMASTER_API_KEY", "").strip()
    if key in PLACEHOLDER_KEYS:
        raise RuntimeError(f"Set TICKETMASTER_API_KEY in {APPDATA_ENV_FILE} (or {ENV_FILE}) first.")
    p = dict(params or {})
    p["apikey"] = key
    url = f"{BASE_URL}/{path.lstrip('/')}?{urlencode(p, doseq=True)}"
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "SearchEventsManager-API-Test/1.0"})
    start = time.perf_counter()
    try:
        with urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        status = e.code
    except URLError as e:
        raise RuntimeError(f"Network error: {e}") from e
    ms = round((time.perf_counter() - start) * 1000, 1)
    try: data = json.loads(raw) if raw else {}
    except json.JSONDecodeError: data = {"_raw": raw[:1000]}
    return status, ms, data

def embedded(data, key):
    return data.get("_embedded", {}).get(key, []) if isinstance(data, dict) else []

def main():
    load_env()
    city, state, country = (os.getenv("TM_CITY"), os.getenv("TM_STATE_CODE"), os.getenv("TM_COUNTRY_CODE"))
    tests, saved = [], {}
    def run(name, path, params=None, expected=200, capture=None):
        try:
            status, ms, data = call(path, params)
            ok = status == expected
            if capture and ok:
                items = embedded(data, capture[0])
                if items: saved[capture[1]] = items[0].get("id")
            count = None
            for k in ("events", "attractions", "venues", "classifications"):
                arr = embedded(data, k)
                if arr: count = len(arr); break
            tests.append({"test": name, "status": status, "expected": expected, "ms": ms, "ok": ok, "count": count, "data": data})
            print(f"{'PASS' if ok else 'FAIL'} | {name:<34} | HTTP {status} | {ms} ms" + (f" | {count} records" if count is not None else ""))
            return data if ok else {}
        except Exception as e:
            tests.append({"test": name, "ok": False, "error": str(e)})
            print(f"ERROR| {name}: {e}")
            return {}
    print("\nTICKETMASTER DISCOVERY API v2 TESTS")
    print(f"Base URL: {BASE_URL} | Location: {city}, {state}, {country}\n")
    # Search endpoints and capture first IDs for dependent detail calls.
    ev = run("Events search", "events.json", {"city": city, "stateCode": state, "countryCode": country, "size": 5}, capture=("events", "event_id"))
    run("Event details", f"events/{saved['event_id']}.json" if saved.get("event_id") else "events/INVALID_TEST_ID.json", expected=200 if saved.get("event_id") else 404)
    if saved.get("event_id"):
        run("Event images", f"events/{saved['event_id']}/images.json")
    att = run("Attraction search", "attractions.json", {"keyword": "Little River Band", "size": 5}, capture=("attractions", "attraction_id"))
    run("Attraction details", f"attractions/{saved['attraction_id']}.json" if saved.get("attraction_id") else "attractions/INVALID_TEST_ID.json", expected=200 if saved.get("attraction_id") else 404)
    cls = run("Classification search", "classifications.json", {"size": 10}, capture=("classifications", "classification_id"))
    run("Classification details", f"classifications/{saved['classification_id']}.json" if saved.get("classification_id") else "classifications/INVALID_TEST_ID.json", expected=200 if saved.get("classification_id") else 404)
    # Search classifications response commonly nests segment/genre/subgenre IDs.
    citems = embedded(cls, "classifications")
    seg = gen = sub = None
    if citems:
        c = citems[0]
        segment_obj = c.get("segment") or {}
        seg = segment_obj.get("id")
        genres = (segment_obj.get("_embedded") or {}).get("genres") or []
        if genres:
            genre_obj = genres[0]
            gen = genre_obj.get("id")
            subgenres = (genre_obj.get("_embedded") or {}).get("subgenres") or []
            if subgenres: sub = subgenres[0].get("id")
    run("Segment details", f"classifications/segments/{seg}.json" if seg else "classifications/segments/INVALID_TEST_ID.json", expected=200 if seg else 404)
    run("Genre details", f"classifications/genres/{gen}.json" if gen else "classifications/genres/INVALID_TEST_ID.json", expected=200 if gen else 404)
    run("Sub-genre details", f"classifications/subgenres/{sub}.json" if sub else "classifications/subgenres/INVALID_TEST_ID.json", expected=200 if sub else 404)
    ven = run("Venue search", "venues.json", {"city": city, "stateCode": state, "countryCode": country, "size": 5}, capture=("venues", "venue_id"))
    run("Venue details", f"venues/{saved['venue_id']}.json" if saved.get("venue_id") else "venues/INVALID_TEST_ID.json", expected=200 if saved.get("venue_id") else 404)
    run("Find suggestions", "suggest.json", {"keyword": "concert", "city": city, "countryCode": country})
    # Extra search parameter coverage for event filters
    run("Events keyword + category", "events.json", {"keyword": "concert", "classificationName": "Music", "city": city, "stateCode": state, "countryCode": country, "size": 5})
    run("Events postal code", "events.json", {"postalCode": os.getenv("TM_POSTAL_CODE", "63146"), "countryCode": country, "size": 5})
    run("Events source filter", "events.json", {"source": "ticketmaster", "countryCode": country, "size": 5})
    out = HERE / "results" / f"test-results-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"created_utc": datetime.now(timezone.utc).isoformat(), "tests": tests}, indent=2), encoding="utf-8")
    passed = sum(1 for t in tests if t.get("ok"))
    failed = len(tests) - passed
    print(f"\nSUMMARY: {passed} passed, {failed} failed out of {len(tests)}")
    print(f"Full JSON results: {out}")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
