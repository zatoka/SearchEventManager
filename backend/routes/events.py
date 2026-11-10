"""
Routes for events and scraping.
"""


from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
import uuid
import json

from database import get_db
from models import EventResponse, SearchFilters
from scrapers import SCRAPER_MAP, URL_SCRAPERS

router = APIRouter(tags=["events"])



@router.post("/venues/{venue_id}/fetch", response_model=list[EventResponse])
async def fetch_events(venue_id: str):
    """Fetch fresh events for a saved venue without caching them in the database."""
    db = await get_db()

    async with db.execute("SELECT * FROM venues WHERE id = ?", (venue_id,)) as cursor:
        venue = await cursor.fetchone()

    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    scraper_type = venue["scraper_type"]

    try:
        # Ticketmaster Discover venues have a real Ticketmaster venue ID.
        # Search by that ID instead of scraping the venue website URL.
        if scraper_type == "ticketmaster" and venue["ticketmaster_id"]:
            from scrapers.ticketmaster_api import search_events as tm_search_events

            events = await tm_search_events(
                ticketmaster_venue_id=venue["ticketmaster_id"],
                size=100,
                page=0
            )
        elif scraper_type in URL_SCRAPERS:
            # No-browser scrapers (City Winery feeds, MetroTix HTML)
            events = await _fetch_url_scraper(scraper_type, venue["url"], venue["name"])
        else:
            # Preserve existing behavior for legacy MetroTix, City Winery,
            # and older Ticketmaster records without a Ticketmaster ID.
            scraper = SCRAPER_MAP.get(scraper_type)

            if not scraper:
                raise HTTPException(
                    status_code=400,
                    detail=f"No scraper for type: {scraper_type}"
                )

            events = await scraper(venue["url"])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Results are temporary: return them to the frontend, but do not
    # insert/update the legacy events table or commit any event records.
    fetched_at = datetime.utcnow().isoformat()
    return [
        {
            "id": str(uuid.uuid4()),
            "venue_id": venue_id,
            "venue_name": venue["name"],
            **event_data,
            "fetched_at": fetched_at
        }
        for event_data in events
    ]


# ── Ticketmaster API Search ─────────────────────────────────────────────────

from scrapers.ticketmaster_api import (
    search_events as tm_search_events,
    DAYS_OF_WEEK,
    DAYS_ABBREVIATED,
    CLASSIFICATION_LIST
)

# City Winery uses its own genre tags (e.g. "Blues-Jazz", "Comedy", "Wine").
# Map them onto the Ticketmaster category dropdown values.
_FEED_NON_MUSIC = ("comedy", "wine", "podcast", "book", "poetry", "drag", "brunch")
_FEED_CATEGORY_KEYWORDS = {
    "arts & theatre": ("comedy", "drag", "poetry", "book", "podcast", "theatre", "theater"),
    "miscellaneous": ("wine", "brunch"),
    "film": ("film", "movie"),
    "sports": ("sport",),
}


def _feed_category_matches(category: str, classification: str) -> bool:
    text = (category or "").lower()
    wanted = classification.strip().lower()
    if wanted == "music":
        return not any(word in text for word in _FEED_NON_MUSIC)
    keywords = _FEED_CATEGORY_KEYWORDS.get(wanted, (wanted,))
    return any(word in text for word in keywords)


async def _fetch_url_scraper(scraper_type, url, venue_name=None):
    """Run a no-browser URL scraper (see scrapers.URL_SCRAPERS) for a saved venue."""
    if scraper_type == "city_winery_feed":
        return await SCRAPER_MAP[scraper_type](url=url)

    if scraper_type == "metrotix_html":
        events = await SCRAPER_MAP[scraper_type](url, venue_name)
        # Show the venue name the user saved (MetroTix labels e.g. "Sheldon").
        if venue_name:
            for event in events:
                event["venue_name"] = venue_name
        return events

    raise ValueError(f"Not a URL scraper: {scraper_type}")


def _filter_feed_events(events, end_date, keyword, classification, day_of_week):
    """Apply the Ticketmaster page filters to feed-based (non-Ticketmaster) events."""
    from scrapers.ticketmaster_api import filter_events_by_day

    last_day = end_date[:10]
    events = [
        e for e in events
        if not e.get("event_date") or e["event_date"] <= last_day
    ]
    if keyword:
        kw = keyword.lower()
        events = [
            e for e in events
            if kw in (e.get("title") or "").lower()
            or kw in (e.get("category") or "").lower()
        ]
    if classification:
        events = [
            e for e in events
            if _feed_category_matches(e.get("category"), classification)
        ]
    if day_of_week:
        events = filter_events_by_day(events, day_of_week)
    return events


@router.get("/ticketmaster/search")
async def ticketmaster_search(
    region: str = Query("saint_louis", description="Search region"),
    keyword: str = Query(None, description="Search keyword"),
    classification: str = Query(None, description="Event category"),
    venue: str = Query(None, description="Filter by venue name"),
    venue_id: str = Query(None, description="Saved venue database ID"),
    venue_mode: str = Query("all", description="all, my_venues, or individual"),
    scraper: str = Query(None, description="Scraper type"),
    day_of_week: str = Query(None, description="Filter by day"),
    week_number: int = Query(None, description="ISO week number", ge=1, le=53),
    days_ahead: int = Query(90, description="Days to search ahead", ge=1, le=365),
    size: int = Query(50, description="Number of results", ge=1, le=100),
    page: int = Query(0, description="Page number", ge=0)
):
    """
    Search events using regional search or a specific saved venue.

    If venue_id is provided, its Ticketmaster venue ID takes priority
    over the regional search.
    """
    from datetime import datetime, timedelta

    start_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    end_date = (
        datetime.utcnow() + timedelta(days=days_ahead)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        # Look up the selected saved venue
        ticketmaster_venue_id = None
        selected_venue = None

        if venue_id:
            db = await get_db()

            async with db.execute(
                """
                SELECT id, name, scraper_type, ticketmaster_id, url
                FROM venues
                WHERE id = ?
                """,
                (venue_id,)
            ) as cursor:
                selected_venue = await cursor.fetchone()

            if not selected_venue:
                raise HTTPException(
                    status_code=404,
                    detail=f"Saved venue ID {venue_id} was not found"
                )

            venue = selected_venue["name"]
            scraper = selected_venue["scraper_type"]

            if scraper == "ticketmaster":
                ticketmaster_venue_id = selected_venue["ticketmaster_id"]

                if not ticketmaster_venue_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{venue} does not have a Ticketmaster venue ID"
                    )
        # My Venues Only - search every saved Ticketmaster venue,
        # plus saved City Winery (feed) venues
        if venue_mode == "my_venues" and not venue_id:
            db = await get_db()

            async with db.execute(
                """
                SELECT ticketmaster_id
                FROM venues
                WHERE scraper_type = 'ticketmaster'
                  AND ticketmaster_id IS NOT NULL
                  AND ticketmaster_id != ''
                """
            ) as cursor:
                saved_venues = await cursor.fetchall()

            combined_events = []
            seen_event_ids = set()

            for saved_venue in saved_venues:
                tm_venue_id = saved_venue["ticketmaster_id"]

                # Fetch the first page for this venue
                result = await tm_search_events(
                    keyword=keyword,
                    classification_name=classification,
                    ticketmaster_venue_id=tm_venue_id,
                    day_of_week=day_of_week,
                    week_number=week_number,
                    start_date_time=start_date,
                    end_date_time=end_date,
                    region=region,
                    size=100,
                    page=0,
                    return_metadata=True
                )

                venue_events = result["events"]

                # Fetch remaining pages for this venue
                for api_page in range(1, result["total_pages"]):
                    next_result = await tm_search_events(
                        keyword=keyword,
                        classification_name=classification,
                        ticketmaster_venue_id=tm_venue_id,
                        day_of_week=day_of_week,
                        week_number=week_number,
                        start_date_time=start_date,
                        end_date_time=end_date,
                        region=region,
                        size=100,
                        page=api_page,
                        return_metadata=True
                    )

                    venue_events.extend(next_result["events"])

                # Combine events and remove duplicates
                for event in venue_events:
                    event_id = event.get("ticketmaster_id")

                    if event_id and event_id not in seen_event_ids:
                        seen_event_ids.add(event_id)
                        combined_events.append(event)

            # Also include saved venues that use a no-browser URL scraper
            # (City Winery feeds, MetroTix HTML).
            placeholders = ", ".join("?" * len(URL_SCRAPERS))
            async with db.execute(
                f"""
                SELECT name, url, scraper_type
                FROM venues
                WHERE scraper_type IN ({placeholders})
                """,
                tuple(sorted(URL_SCRAPERS))
            ) as cursor:
                feed_venues = await cursor.fetchall()

            if feed_venues:
                for feed_venue in feed_venues:
                    try:
                        feed_events = await _fetch_url_scraper(
                            feed_venue["scraper_type"], feed_venue["url"], feed_venue["name"]
                        )
                    except Exception as e:
                        # One unreachable source should not fail the whole search.
                        print(f"[My Venues] Skipping {feed_venue['name']}: {e}")
                        continue

                    feed_events = _filter_feed_events(
                        feed_events, end_date, keyword, classification, day_of_week
                    )
                    for event in feed_events:
                        event_id = event.get("ticketmaster_id")
                        if event_id and event_id not in seen_event_ids:
                            seen_event_ids.add(event_id)
                            combined_events.append(event)

            # Sort combined results by date and time
            combined_events.sort(
                key=lambda e: (
                    e.get("event_date") or "9999-99-99",
                    e.get("event_time") or ""
                )
            )

            # Apply pagination to the combined results
            total = len(combined_events)
            total_pages = (total + size - 1) // size

            start_index = page * size
            end_index = start_index + size

            return {
                "events": combined_events[start_index:end_index],
                "total": total,
                "total_pages": total_pages,
                "page": page
            }

        # MetroTix venue search
        if scraper == "metrotix" and venue:
            db = await get_db()

            async with db.execute(
                "SELECT url FROM venues WHERE name = ?",
                (venue,)
            ) as cursor:
                venue_row = await cursor.fetchone()

            if venue_row:
                from scrapers.metrotix import scrape_metrotix
                from scrapers.ticketmaster_api import filter_events_by_day

                events = await scrape_metrotix(venue_row["url"])

                if day_of_week:
                    events = filter_events_by_day(events, day_of_week)

                for event in events:
                    if not event.get("ticketmaster_id"):
                        event["ticketmaster_id"] = (
                            event.get("event_url", "").split("/")[-1]
                            or str(uuid.uuid4())
                        )

                return {"total": len(events), "events": events}

        # No-browser URL scrapers: City Winery feeds, MetroTix HTML
        if scraper in URL_SCRAPERS:
            if selected_venue:
                source_url, source_name = selected_venue["url"], selected_venue["name"]
            elif scraper == "city_winery_feed":
                # No saved venue selected: pick the City Winery city by region.
                source_url = "chicago" if region == "chicago" else None
                source_name = None
            else:
                raise HTTPException(status_code=400, detail="Select a saved venue to search MetroTix")

            events = await _fetch_url_scraper(scraper, source_url, source_name)

            # Same date range, keyword, category and day filters as Ticketmaster.
            events = _filter_feed_events(
                events, end_date, keyword, classification, day_of_week
            )

            for event in events:
                if not event.get("ticketmaster_id"):
                    event["ticketmaster_id"] = (
                        event.get("event_url", "").split("/")[-1]
                        or str(uuid.uuid4())
                    )

            return {"total": len(events), "events": events}

        # City Winery search - legacy Playwright scraper (unchanged)
        if scraper in ("city_winery", "CW"):
            from scrapers.city_winery import scrape_city_winery_st_louis
            from scrapers.ticketmaster_api import filter_events_by_day

            events = await scrape_city_winery_st_louis()

            if day_of_week:
                events = filter_events_by_day(events, day_of_week)

            for event in events:
                if not event.get("ticketmaster_id"):
                    event["ticketmaster_id"] = (
                        event.get("event_url", "").split("/")[-1]
                        or str(uuid.uuid4())
                    )

            return {"total": len(events), "events": events}

        # Ticketmaster API search
        result = await tm_search_events(
            keyword=keyword,
            classification_name=classification,
            venue_name=venue,
            ticketmaster_venue_id=ticketmaster_venue_id,
            day_of_week=day_of_week,
            week_number=week_number,
            start_date_time=start_date,
            end_date_time=end_date,
            region=region,
            size=size,
            page=page,
            return_metadata=True
        )

        return result

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/ticketmaster/filters")
async def ticketmaster_filters():
    """Get available filter options for dropdowns."""
    return {
        "days_of_week": DAYS_OF_WEEK,
        "days_abbreviated": DAYS_ABBREVIATED,
        "classifications": CLASSIFICATION_LIST
    }



# ── My Events (Saved Events) ────────────────────────────────────────────────

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MyEventCreate(BaseModel):
    ticketmaster_id: str
    title: str
    event_date: Optional[str] = None
    event_time: Optional[str] = None
    day_of_week: Optional[str] = None
    venue_name: Optional[str] = None
    category: Optional[str] = None
    event_url: Optional[str] = None
    image_url: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    description: Optional[str] = None


@router.post("/my-events/")
async def save_my_event(event: MyEventCreate):
    """Save an event to My Events list."""
    db = await get_db()
    
    # Check if already saved
    async with db.execute(
        "SELECT id FROM my_events WHERE ticketmaster_id = ?", (event.ticketmaster_id,)
    ) as cursor:
        existing = await cursor.fetchone()
    
    if existing:
        raise HTTPException(status_code=400, detail="Event already saved")
    
    # Save event
    import uuid
    event_id = str(uuid.uuid4())
    saved_at = datetime.utcnow().isoformat()
    
    await db.execute(
        """INSERT INTO my_events 
           (id, ticketmaster_id, title, event_date, event_time, day_of_week, 
            venue_name, category, event_url, image_url, price_min, price_max, 
            description, saved_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (event_id, event.ticketmaster_id, event.title, event.event_date, 
         event.event_time, event.day_of_week, event.venue_name, event.category,
         event.event_url, event.image_url, event.price_min, event.price_max,
         event.description, saved_at)
    )
    
    await db.commit()
    
    return {"id": event_id, "message": "Event saved", "saved_at": saved_at}

@router.get("/my-events/")
async def list_my_events():
    """Remove expired saved events and return remaining events."""
    db = await get_db()

    # Current date and time
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    # Remove events from previous dates.
    await db.execute(
        "DELETE FROM my_events WHERE event_date < ?",
        (today,)
    )

    # Remove today's events only when their scheduled time has passed.
    # Events without a time are retained until the next day.
    await db.execute(
        """
        DELETE FROM my_events
        WHERE event_date = ?
          AND event_time IS NOT NULL
          AND event_time != ''
          AND event_time <= ?
        """,
        (today, current_time)
    )

    await db.commit()

    # Return remaining saved events.
    async with db.execute(
        "SELECT * FROM my_events ORDER BY event_date, event_time"
    ) as cursor:
        rows = await cursor.fetchall()

    events = []
    for row in rows:
        events.append({
            "id": row["id"],
            "ticketmaster_id": row["ticketmaster_id"],
            "title": row["title"],
            "event_date": row["event_date"],
            "event_time": row["event_time"],
            "day_of_week": row["day_of_week"],
            "venue_name": row["venue_name"],
            "category": row["category"],
            "event_url": row["event_url"],
            "image_url": row["image_url"],
            "price_min": row["price_min"],
            "price_max": row["price_max"],
            "description": row["description"],
            "saved_at": row["saved_at"]
        })

    return events




@router.delete("/my-events/{event_id}", status_code=204)
async def delete_my_event(event_id: str):
    """Remove a saved event."""
    db = await get_db()
    
    cursor = await db.execute("DELETE FROM my_events WHERE id = ?", (event_id,))
    await db.commit()
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Event not found")
