"""
City Winery events from the venue's published feeds (no browser needed).

Each City Winery events page (e.g. https://citywinery.com/pages/events/st-louis)
advertises two public feeds in its <head>:

    <link rel="alternate" type="text/calendar"     href="https://awsapi.citywinery.com/feeds/St. Louis/events.ics">
    <link rel="alternate" type="application/rss+xml" href="https://awsapi.citywinery.com/feeds/St. Louis/rss.xml">

- iCal (events.ics): title, exact local start/end time, ticket URL, status, location.
- RSS  (rss.xml):    the same events plus image and categories.

Both use the same event id (iCal UID == RSS guid), so they are merged by id.
Standard library parsing only; HTTP via aiohttp (already a backend dependency).
"""
import re
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from urllib.parse import quote
import aiohttp

from scrapers.http_utils import BROWSER_HEADERS, USER_AGENT, ssl_context  # noqa: F401

FEED_BASE = "https://awsapi.citywinery.com/feeds"
LOCAL_TZ_NAME = "America/Chicago"  # St. Louis and Chicago are both Central time
# The events page is behind Cloudflare, which returns 403 without normal
# browser Accept headers. The feeds work either way.
REQUEST_HEADERS = BROWSER_HEADERS

# key -> feed city name, display venue name, events page
CITIES = {
    "st_louis": {
        "feed_city": "St. Louis",
        "venue_name": "City Winery St. Louis",
        "page_url": "https://citywinery.com/pages/events/st-louis",
    },
    "chicago": {
        "feed_city": "Chicago",
        "venue_name": "City Winery Chicago",
        "page_url": "https://citywinery.com/pages/events/chicago",
    },
}

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# In-memory cache per city: {city_key: (monotonic_time, events)}
CACHE_SECONDS = 10 * 60
_cache: dict = {}


class CityWineryFeedError(Exception):
    """The City Winery feed could not be downloaded or read."""


def feed_urls(city_key: str) -> dict:
    """Return {'ics': url, 'rss': url} for a city key."""
    city = CITIES[city_key]["feed_city"]
    base = f"{FEED_BASE}/{quote(city)}"
    return {"ics": f"{base}/events.ics", "rss": f"{base}/rss.xml"}


def city_key_from_url(url: Optional[str]) -> str:
    """Map a saved venue URL (or any text) to a city key. Defaults to St. Louis."""
    text = (url or "").lower()
    if "chicago" in text:
        return "chicago"
    return "st_louis"


def discover_feed_urls(page_html: str) -> dict:
    """Read the feed links advertised in an events page's <head>."""
    found = {}
    for tag in re.findall(r"<link\b[^>]*>", page_html, re.I):
        href = re.search(r'href=["\']([^"\']+)', tag, re.I)
        if not href or "awsapi.citywinery.com/feeds" not in href.group(1):
            continue
        if "text/calendar" in tag:
            found["ics"] = href.group(1).replace(" ", "%20")
        elif "rss" in tag:
            found["rss"] = href.group(1).replace(" ", "%20")
    return found


# ── iCal parsing ───────────────────────────────────────────────────────────

def _unfold_ics(text: str) -> list:
    """Join folded iCal lines (continuation lines start with a space or tab)."""
    lines = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def _ics_unescape(value: str) -> str:
    return (value.replace("\\n", "\n").replace("\\N", "\n")
                 .replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\"))


def _to_local(dt: datetime, source_tz: str) -> datetime:
    """Convert to Central time. zoneinfo is loaded lazily so a missing time-zone
    database (possible in a packaged build) cannot break importing this module;
    in that case the feed's own time is kept unchanged."""
    try:
        from zoneinfo import ZoneInfo
        return dt.replace(tzinfo=ZoneInfo(source_tz)).astimezone(ZoneInfo(LOCAL_TZ_NAME))
    except Exception:
        return dt


def _ics_datetime(params: str, value: str):
    """Return (local YYYY-MM-DD, local HH:MM or None) for a DTSTART value."""
    value = value.strip()
    try:
        if "VALUE=DATE" in params.upper() or len(value) == 8:
            return datetime.strptime(value[:8], "%Y%m%d").strftime("%Y-%m-%d"), None
        if value.endswith("Z"):
            dt = _to_local(datetime.strptime(value, "%Y%m%dT%H%M%SZ"), "UTC")
        else:
            # City Winery feeds use TZID=America/Chicago (already local time).
            dt = datetime.strptime(value[:15], "%Y%m%dT%H%M%S")
            tz = re.search(r"TZID=([^;:]+)", params)
            if tz and tz.group(1) != LOCAL_TZ_NAME:
                dt = _to_local(dt, tz.group(1))
        return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
    except ValueError:
        return None, None


def parse_ics(text: str) -> dict:
    """Parse VEVENTs into {uid: {...}}."""
    events, current = {}, None
    for line in _unfold_ics(text):
        if line == "BEGIN:VEVENT":
            current = {}
            continue
        if line == "END:VEVENT":
            if current and current.get("uid"):
                events[current["uid"]] = current
            current = None
            continue
        if current is None or ":" not in line:
            continue

        name_params, value = line.split(":", 1)
        name, _, params = name_params.partition(";")
        name = name.upper()

        if name == "UID":
            current["uid"] = value.strip()
        elif name == "SUMMARY":
            current["title"] = _ics_unescape(value).strip()
        elif name == "DTSTART":
            current["event_date"], current["event_time"] = _ics_datetime(params, value)
        elif name == "URL":
            current["event_url"] = value.strip()
        elif name == "LOCATION":
            current["location"] = _ics_unescape(value).strip()
        elif name == "STATUS":
            current["status"] = value.strip().lower()
        elif name == "DESCRIPTION":
            desc = _ics_unescape(value)
            # The feed appends "Ticket URL: ..." - already available as event_url.
            desc = re.sub(r"\n?Ticket URL:\s*\S+\s*$", "", desc).strip()
            current["description"] = desc or None
    return events


# ── RSS parsing ────────────────────────────────────────────────────────────

def parse_rss(text: str) -> dict:
    """Parse RSS items into {guid: {image_url, categories, event_url, title}}."""
    items = {}
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise CityWineryFeedError(f"City Winery RSS feed could not be read: {e}") from e

    for item in root.iter("item"):
        guid = (item.findtext("guid") or "").strip()
        if not guid:
            continue
        enclosure = item.find("enclosure")
        items[guid] = {
            "title": (item.findtext("title") or "").strip(),
            "event_url": (item.findtext("link") or "").strip() or None,
            "image_url": enclosure.get("url") if enclosure is not None else None,
            "categories": [c.text.strip() for c in item.findall("category") if c.text and c.text.strip()],
        }
    return items


# ── Merge into the app's standard event format ────────────────────────────

def merge_events(ics_events: dict, rss_items: dict, venue_name: str) -> list:
    """Combine iCal (times) and RSS (image, categories) by event id."""
    merged = []
    for uid in list(ics_events) + [g for g in rss_items if g not in ics_events]:
        ics = ics_events.get(uid, {})
        rss = rss_items.get(uid, {})
        title = ics.get("title") or rss.get("title")
        if not title:
            continue

        event_date = ics.get("event_date")
        categories = rss.get("categories") or []
        merged.append({
            "id": str(uuid.uuid4()),
            # Stable id so "Save to My Events" detects duplicates.
            "ticketmaster_id": f"citywinery-{uid}",
            "title": title,
            "event_date": event_date,
            "event_time": ics.get("event_time"),
            "day_of_week": (DAY_NAMES[datetime.strptime(event_date, "%Y-%m-%d").weekday()]
                            if event_date else None),
            "description": ics.get("description"),
            "event_url": ics.get("event_url") or rss.get("event_url"),
            "image_url": rss.get("image_url"),
            "price_min": None,
            "price_max": None,
            "category": " - ".join(categories[:2]) if categories else None,
            "venue_name": venue_name,
            "status": ics.get("status"),
            "source": "city_winery",
            "attractions": [],
        })

    merged.sort(key=lambda e: (e.get("event_date") or "9999-99-99", e.get("event_time") or ""))
    return merged


# ── Download ───────────────────────────────────────────────────────────────

_ssl_context = ssl_context  # shared helper (kept name for existing callers)


async def _download(session: aiohttp.ClientSession, url: str) -> str:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status != 200:
                raise CityWineryFeedError(f"City Winery feed returned HTTP {response.status} for {url}")
            return await response.text()
    except aiohttp.ClientConnectorCertificateError as e:
        raise CityWineryFeedError(
            "Could not verify City Winery's security certificate (network/proxy issue)."
        ) from e
    except aiohttp.ClientError as e:
        raise CityWineryFeedError(f"Network error contacting City Winery: {e}") from e


async def scrape_city_winery(url: Optional[str] = None, city: Optional[str] = None) -> list:
    """Return upcoming City Winery events for St. Louis or Chicago.

    url:  saved venue URL (used to pick the city), e.g. .../events/chicago
    city: 'st_louis' or 'chicago' (overrides url)
    """
    city_key = city if city in CITIES else city_key_from_url(url)

    # Short cache: paging through search results re-runs the search for every
    # page, so reuse a recent download instead of fetching both feeds again.
    cached = _cache.get(city_key)
    if cached and time.monotonic() - cached[0] < CACHE_SECONDS:
        return [dict(e) for e in cached[1]]

    urls = feed_urls(city_key)
    connector = aiohttp.TCPConnector(ssl=_ssl_context())
    async with aiohttp.ClientSession(connector=connector, headers=REQUEST_HEADERS) as session:
        ics_text = await _download(session, urls["ics"])
        rss_text = await _download(session, urls["rss"])

    events = merge_events(parse_ics(ics_text), parse_rss(rss_text), CITIES[city_key]["venue_name"])
    _cache[city_key] = (time.monotonic(), events)
    return [dict(e) for e in events]
