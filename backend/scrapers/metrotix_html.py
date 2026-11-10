"""
MetroTix venue events without a browser (scraper type "metrotix_html").

MetroTix venue pages (e.g. https://www.metrotix.com/events/venue/sheldon-the)
are server-rendered: the first 8 events are in the page HTML as
<div class="eventItem ..."> blocks. The rest load through the page's
"Load More Events" button, which calls:

    /events/events_ajax/{offset}?category=0&venue=53&team=0&per_page=8&came_from_page=event-list-page

and returns a JSON string containing more eventItem HTML. The venue id,
category, team and increment come from that button's data-* attributes.

Plain HTTP (aiohttp) and regex parsing only - no Playwright.
"""
import html as html_lib
import json
import re
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

import aiohttp

from scrapers.http_utils import BROWSER_HEADERS, ssl_context

BASE_URL = "https://www.metrotix.com"
MAX_LOAD_MORE_PAGES = 30          # safety cap: 30 x 8 = 240 events
CACHE_SECONDS = 10 * 60
_cache: dict = {}

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], start=1)}
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class MetroTixError(Exception):
    """MetroTix could not be reached or returned an unexpected page."""


# ── Parsing ────────────────────────────────────────────────────────────────

def _text(fragment: str) -> str:
    """Strip tags, decode entities, collapse whitespace."""
    return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", " ", fragment or ""))).strip()


def _split_event_items(page: str) -> list:
    """Return the HTML of each <div class="eventItem ..."> block."""
    starts = [m.start() for m in re.finditer(r'<div class="eventItem\b', page)]
    blocks = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(page)
        blocks.append(page[start:end])
    return blocks


def _parse_date(block: str) -> Optional[str]:
    """First date of the event (single date or the start of a range), YYYY-MM-DD."""
    date_html = re.search(r'<div class="date">(.*?)</div>', block, re.S)
    if not date_html:
        return None
    part = date_html.group(1)
    months = [m.strip().lower() for m in re.findall(r'm-date__month">([^<]+)<', part)]
    days = re.findall(r'm-date__day">\s*(\d{1,2})\s*<', part)
    years = re.findall(r'm-date__year">\D*(\d{4})', part)
    if not months or not days or months[0] not in MONTHS:
        return None

    month, day = MONTHS[months[0]], int(days[0])
    if years:
        year = int(years[0])
    else:
        # No year shown: assume the next occurrence of that date.
        today = datetime.now()
        year = today.year + (1 if (month, day) < (today.month, today.day) else 0)
    try:
        return datetime(year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        return None


def _parse_time(text: str) -> Optional[str]:
    """'Doors 7:00pm Building' -> '19:00'."""
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*([ap])\.?m", text or "", re.I)
    if not m:
        return None
    hour = int(m.group(1)) % 12 + (12 if m.group(3).lower() == "p" else 0)
    return f"{hour:02d}:{int(m.group(2) or 0):02d}"


def parse_event_items(page: str, default_venue: Optional[str] = None) -> list:
    """Parse MetroTix eventItem blocks into the app's standard event format."""
    events = []
    for block in _split_event_items(page):
        detail = re.search(r'href="([^"]*/events/detail/([a-z0-9\-]+))"', block)
        if not detail:
            continue
        detail_url, slug = urljoin(BASE_URL, detail.group(1).replace("\\/", "/")), detail.group(2)

        title_html = re.search(r'<h3 class="title[^"]*"[^>]*>(.*?)</h3>', block, re.S)
        title = _text(title_html.group(1)) if title_html else ""
        if not title:
            alt = re.search(r'title="More Info for ([^"]+)"', block)
            title = html_lib.unescape(alt.group(1)).strip() if alt else ""
        if not title:
            continue

        tagline = re.search(r'<h4 class="tagline[^"]*">(.*?)</h4>', block, re.S)
        doors = re.search(r'<div class="doors">(.*?)</div>', block, re.S)
        venue = re.search(r'<div class="venue">(.*?)</div>', block, re.S)
        image = re.search(r'<img[^>]+src="([^"]+)"', block)
        tickets = re.search(r'href="(https://metrotix\.evenue\.net/[^"]+)"', block)

        venue_name = _text(venue.group(1)).replace("Venue:", "").strip() if venue else ""
        doors_text = _text(doors.group(1)) if doors else ""
        event_date = _parse_date(block)
        tagline_text = _text(tagline.group(1)) if tagline else ""

        description_parts = [p for p in (tagline_text, doors_text) if p]
        events.append({
            # Stable id for Save to My Events. Same format as the legacy
            # "metrotix" scraper (URL slug), so events saved earlier are
            # recognized as "already saved" instead of being duplicated.
            "ticketmaster_id": slug,
            "title": title,
            "event_date": event_date,
            "event_time": _parse_time(doors_text),   # MetroTix lists door time
            "day_of_week": (DAY_NAMES[datetime.strptime(event_date, "%Y-%m-%d").weekday()]
                            if event_date else None),
            "description": " · ".join(description_parts) or None,
            "event_url": detail_url,
            "ticket_url": tickets.group(1) if tickets else None,
            "image_url": urljoin(BASE_URL, image.group(1).replace("\\/", "/")) if image else None,
            "price_min": None,
            "price_max": None,
            "category": None,                        # MetroTix list pages do not show a category
            "venue_name": venue_name or default_venue or "MetroTix",
            "source": "metrotix",
            "attractions": [],
        })
    return events


def parse_load_more(page: str) -> Optional[dict]:
    """Read the Load More button's data-* attributes, or None if absent."""
    button = re.search(r'<button[^>]+id="loadMoreEvents"[^>]*>', page)
    if not button:
        return None
    attrs = dict(re.findall(r'data-([a-z\-]+)="([^"]*)"', button.group(0)))
    if not attrs.get("venue"):
        return None
    return {
        "venue": attrs.get("venue"),
        "category": attrs.get("category", "0"),
        "team": attrs.get("team", "0"),
        "offset": int(attrs.get("offset") or 8),
        "increment": int(attrs.get("increment") or 8),
        "camefrom": attrs.get("camefrom", "event-list-page"),
    }


# ── Download ───────────────────────────────────────────────────────────────

async def _get(session: aiohttp.ClientSession, url: str, params: Optional[dict] = None, ajax=False) -> str:
    headers = {"X-Requested-With": "XMLHttpRequest"} if ajax else None
    try:
        async with session.get(url, params=params, headers=headers,
                               timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status != 200:
                raise MetroTixError(f"MetroTix returned HTTP {response.status} for {url}")
            return await response.text()
    except aiohttp.ClientConnectorCertificateError as e:
        raise MetroTixError("Could not verify MetroTix's security certificate (network/proxy issue).") from e
    except aiohttp.ClientError as e:
        raise MetroTixError(f"Network error contacting MetroTix: {e}") from e


async def scrape_metrotix_html(url: str, venue_name: Optional[str] = None) -> list:
    """Return all upcoming events for a MetroTix venue page URL."""
    if not url or "metrotix.com" not in url:
        raise MetroTixError(f"Not a MetroTix venue URL: {url!r}")

    cached = _cache.get(url)
    if cached and time.monotonic() - cached[0] < CACHE_SECONDS:
        return [dict(e) for e in cached[1]]

    connector = aiohttp.TCPConnector(ssl=ssl_context())
    async with aiohttp.ClientSession(connector=connector, headers=BROWSER_HEADERS) as session:
        page = await _get(session, url)
        events = parse_event_items(page, venue_name)
        seen = {e["ticketmaster_id"] for e in events}

        more = parse_load_more(page)
        if more:
            offset = more["offset"]
            for _ in range(MAX_LOAD_MORE_PAGES):
                body = await _get(
                    session, f"{BASE_URL}/events/events_ajax/{offset}",
                    params={"category": more["category"], "venue": more["venue"],
                            "team": more["team"], "per_page": more["increment"],
                            "came_from_page": more["camefrom"]},
                    ajax=True,
                )
                try:
                    chunk = json.loads(body)
                    if not isinstance(chunk, str):
                        chunk = json.dumps(chunk)
                except json.JSONDecodeError:
                    chunk = body
                new = [e for e in parse_event_items(chunk, venue_name) if e["ticketmaster_id"] not in seen]
                if not new:
                    break
                events.extend(new)
                seen.update(e["ticketmaster_id"] for e in new)
                offset += more["increment"]

    events.sort(key=lambda e: (e.get("event_date") or "9999-99-99", e.get("event_time") or ""))
    _cache[url] = (time.monotonic(), events)
    return [dict(e) for e in events]
