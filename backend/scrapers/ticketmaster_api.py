"""
Ticketmaster Discovery API integration - Saint Louis area focused.

Uses the official Ticketmaster Discovery API instead of web scraping.
Defaults to Saint Louis, MO area for all searches.
API docs: https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/
"""
import aiohttp
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, List

from config import (
    get_ticketmaster_api_key,
    TICKETMASTER_BASE_URL,
    DEFAULT_CITY,
    DEFAULT_STATE_CODE,
    LOG_API_CALLS,
    LOG_FORMAT,
    LOG_DATE_FORMAT,
    get_current_log_file
)

from scrapers.ticketmaster_venues import (
    REGIONS,
    calculate_distance,
    encode_geohash
)

# ── Logging Setup (Daily Log Files) ──────────────────────────────────────────
logger = logging.getLogger("ticketmaster_api")
logger.setLevel(logging.INFO)

# Console handler - always enabled
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
logger.addHandler(console_handler)

# File handler will be created dynamically per API call to ensure daily rotation
_current_file_handler = None


def _get_file_handler():
    """Get or create the file handler for today's log file."""
    global _current_file_handler
    
    log_file = get_current_log_file()
    
    # Check if we need a new handler (new day or first time)
    if _current_file_handler is None:
        _current_file_handler = logging.FileHandler(log_file, encoding='utf-8')
        _current_file_handler.setLevel(logging.INFO)
        _current_file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        logger.addHandler(_current_file_handler)
    else:
        # Check if the log file path changed (new day)
        current_log_path = _current_file_handler.baseFilename if hasattr(_current_file_handler, 'baseFilename') else None
        if current_log_path != str(log_file):
            # Remove old handler and create new one for new day
            logger.removeHandler(_current_file_handler)
            _current_file_handler.close()
            _current_file_handler = logging.FileHandler(log_file, encoding='utf-8')
            _current_file_handler.setLevel(logging.INFO)
            _current_file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
            logger.addHandler(_current_file_handler)
    
    return _current_file_handler


def log_api_call(endpoint: str, params: dict, response_data: dict, status_code: int, duration_ms: float):
    """Log API call details to daily log file."""
    if not LOG_API_CALLS:
        return
    
    # Ensure we have a file handler for today
    _get_file_handler()
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "endpoint": endpoint,
        "params": {k: v for k, v in params.items() if k != "apikey"},  # Hide API key in logs
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "events_found": len(response_data.get("_embedded", {}).get("events", [])),
        "total_results": response_data.get("page", {}).get("totalElements", 0)
    }
    
    logger.info(json.dumps(log_entry))

# Day of week mapping
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_ABBREVS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Classification categories (from Ticketmaster)
CLASSIFICATIONS = ["Music", "Sports", "Arts & Theatre", "Film", "Miscellaneous"]


def get_week_number(date_str: str) -> Optional[int]:
    """Get the ISO week number from a date string."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.isocalendar()[1]
    except (ValueError, TypeError):
        return None


def get_week_range(year: int, week: int) -> tuple:
    """Get start/end dates for an ISO week. Returns (start_date, end_date) as YYYY-MM-DD strings."""
    jan4 = datetime(year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.weekday())
    target_monday = week1_monday + timedelta(weeks=week - 1)
    target_sunday = target_monday + timedelta(days=6)
    return target_monday.strftime("%Y-%m-%d"), target_sunday.strftime("%Y-%m-%d")


def filter_events_by_week(events: List[dict], week_number: int) -> List[dict]:
    """Filter events by ISO week number."""
    if not week_number:
        return events
    
    filtered = []
    for event in events:
        event_date = event.get("event_date")
        if event_date:
            event_week = get_week_number(event_date)
            if event_week == week_number:
                filtered.append(event)
    
    return filtered


def get_day_of_week(date_str: str) -> Optional[str]:
    """
    Get the day of week name from a date string.
    
    Parameters:
        date_str: Date in YYYY-MM-DD format
    
    Returns:
        Day name (e.g., "Monday") or None if invalid
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return DAY_NAMES[date_obj.weekday()]
    except (ValueError, TypeError):
        return None


def filter_events_by_day(events: List[dict], day_filter: str) -> List[dict]:
    """
    Filter events by day of week.
    
    Parameters:
        events: List of event dicts
        day_filter: Day name or abbreviation (e.g., "Monday", "Mon", "Sat")
    
    Returns:
        Filtered list of events
    """
    if not day_filter:
        return events
    
    # Normalize the filter (accept full name or abbreviation)
    day_filter = day_filter.strip().lower()
    
    # Map abbreviation to full name
    day_map = {
        "mon": "Monday", "monday": "Monday",
        "tue": "Tuesday", "tues": "Tuesday", "tuesday": "Tuesday",
        "wed": "Wednesday", "wednesday": "Wednesday",
        "thu": "Thursday", "thurs": "Thursday", "thursday": "Thursday",
        "fri": "Friday", "friday": "Friday",
        "sat": "Saturday", "saturday": "Saturday",
        "sun": "Sunday", "sunday": "Sunday"
    }
    
    target_day = day_map.get(day_filter)
    if not target_day:
        return events
    
    # Filter events
    filtered = []
    for event in events:
        event_date = event.get("event_date")
        if event_date:
            event_day = get_day_of_week(event_date)
            if event_day == target_day:
                filtered.append(event)
    
    return filtered


async def search_events(
    keyword: Optional[str] = None,
    classification_name: Optional[str] = None,
    venue_name: Optional[str] = None,
    ticketmaster_venue_id: Optional[str] = None,
    start_date_time: Optional[str] = None,
    end_date_time: Optional[str] = None,
    day_of_week: Optional[str] = None,
    week_number: Optional[int] = None,
    size: int = 100,
    page: int = 0,
    return_metadata: bool = False,
    city: str = DEFAULT_CITY,
    state_code: str = DEFAULT_STATE_CODE,
    region: str = "saint_louis"

) -> list:
    """
    Search for events using Ticketmaster Discovery API.
    All in one endpoint with all filters.
    
    Parameters:
        keyword: Keyword search (artist, event name, etc.)
        classification_name: Filter by classification (e.g., "Music", "Sports", "Arts & Theatre")
        venue_name: Filter by venue name
        ticketmaster_venue_id: Exact Ticketmaster venue ID
        start_date_time: Filter start date (ISO 8601 format)
        end_date_time: Filter end date (ISO 8601 format)
        day_of_week: Filter by day (e.g., "Monday", "Mon", "Sat")
        week_number: Filter by ISO week number (1-53)
        size: Number of results per page (max 100)
        page: Page number (starts at 0)
        city: City name (default: Saint Louis)
        state_code: State code (default: MO)
    
    Returns:
        List of event dicts matching the standard event schema
    """
    import time
    
    endpoint = f"{TICKETMASTER_BASE_URL}/events.json"
    
    # When filtering by venue, fetch more results since it's client-side filtering
    fetch_size = min(size, 100)
    if venue_name:
        fetch_size = 100  # Always fetch max when venue filtering
    
    params = {
        "apikey": get_ticketmaster_api_key(),
        "size": fetch_size,
        "page": page
    }

    # A specific Ticketmaster venue ID takes precedence over city/state.
    # This supports venues outside the default Saint Louis region.
    if region not in REGIONS:
        raise ValueError(f"Unknown region: {region}")

    center = REGIONS[region]

    if ticketmaster_venue_id:
        params["venueId"] = ticketmaster_venue_id
    else:
        params["geoPoint"] = encode_geohash(
            center["latitude"],
            center["longitude"]
        )
        params["radius"] = center["radius"]
        params["unit"] = "miles"

    if keyword:
        params["keyword"] = keyword
    if classification_name:
        params["classificationName"] = classification_name
    if venue_name:
        # Filter by venue name client-side after fetching
        # Ticketmaster API doesn't have a reliable venueName filter
        pass
    if start_date_time:
        params["startDateTime"] = start_date_time
    if end_date_time:
        params["endDateTime"] = end_date_time
    
    start_time = time.time()
    
    events_data = []
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(endpoint, params=params) as response:
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status == 401:
                    log_api_call(endpoint, params, {"error": "Invalid API key"}, response.status, duration_ms)
                    raise Exception("Invalid Ticketmaster API key")
                elif response.status == 429:
                    log_api_call(endpoint, params, {"error": "Rate limit exceeded"}, response.status, duration_ms)
                    raise Exception("Rate limit exceeded - please wait before retrying")
                elif response.status != 200:
                    text = await response.text()
                    log_api_call(endpoint, params, {"error": text}, response.status, duration_ms)
                    raise Exception(f"API error {response.status}: {text}")
                
                data = await response.json()
                
                # Log successful API call
                log_api_call(endpoint, params, data, response.status, duration_ms)
            
            # Extract events from page 0
            # Extract pagination information from Ticketmaster
            page_info = data.get("page", {})
            total_results = page_info.get("totalElements", 0)
            total_pages = page_info.get("totalPages", 0)
            current_page = page_info.get("number", page)

            # Extract events from the requested page
            events_data = data.get("_embedded", {}).get("events", [])

        except aiohttp.ClientError as e:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call(endpoint, params, {"error": str(e)}, 0, duration_ms)
            raise Exception(f"Network error: {e}")
    
    # Convert to standard format
    events = []
    for event in events_data:
        event_dict = _parse_event(event)
        if event_dict:
            events.append(event_dict)
    ######
    # Apply geographic filter only to regional searches
    if not ticketmaster_venue_id:
        center = REGIONS[region]
        filtered_events = []

        for event in events:
            lat = event.get("venue_latitude")
            lon = event.get("venue_longitude")

            if lat is None or lon is None:
                continue

            try:
                distance = calculate_distance(
                    center["latitude"],
                    center["longitude"],
                    lat,
                    lon
                )

                if distance <= center["radius"]:
                    filtered_events.append(event)

            except (TypeError, ValueError):
                continue

        events = filtered_events

    # Sort by date (earliest first), then by time
    events.sort(key=lambda e: (
        e.get("event_date") or "9999-99-99",
        e.get("event_time") or ""
    ))

    # Apply client-side filters
    if venue_name:
        venue_lower = venue_name.lower()
        events = [
            e for e in events
            if venue_lower in e.get("venue_name", "").lower()
        ]

    if day_of_week:
        events = filter_events_by_day(events, day_of_week)

    if week_number:
        events = filter_events_by_week(events, week_number)

    if return_metadata:
        return {
            "events": events,
            "total": total_results,
            "total_pages": total_pages,
            "page": current_page
       }

    return events


async def get_venue_events(venue_name: str) -> list:
    """
    Get events for a specific venue by name (Saint Louis area only).
    
    Parameters:
        venue_name: Name of the venue to search for
    
    Returns:
        List of events at the venue
    """
    return await search_events(keyword=venue_name)


async def get_event_by_id(event_id: str) -> Optional[dict]:
    """
    Get detailed information about a specific event.
    
    Parameters:
        event_id: Ticketmaster event ID
    
    Returns:
        Event dict or None if not found
    """
    import time
    
    endpoint = f"{TICKETMASTER_BASE_URL}/events/{event_id}.json"
    params = {"apikey": get_ticketmaster_api_key()}
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(endpoint, params=params) as response:
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status == 404:
                    log_api_call(endpoint, params, {"error": "Not found"}, 404, duration_ms)
                    return None
                elif response.status != 200:
                    text = await response.text()
                    log_api_call(endpoint, params, {"error": text}, response.status, duration_ms)
                    raise Exception(f"API error {response.status}: {text}")
                
                data = await response.json()
                
                # Log successful API call
                log_api_call(endpoint, params, data, response.status, duration_ms)
                
        except aiohttp.ClientError as e:
            duration_ms = (time.time() - start_time) * 1000
            log_api_call(endpoint, params, {"error": str(e)}, 0, duration_ms)
            raise Exception(f"Network error: {e}")
    
    return _parse_event(data)


def _parse_event(event: dict) -> Optional[dict]:
    """
    Parse Ticketmaster event data into standard format.
    
    Returns a dict with:
      - title (str)
      - event_date (str) - ISO date format
      - event_time (str) - HH:MM format
      - description (str)
      - event_url (str)
      - image_url (str)
      - price_min (float)
      - price_max (float)
      - category (str)
      - venue_name (str)
      - ticketmaster_id (str)
    """
    try:
        # Basic info
        title = event.get("name")
        if not title:
            return None
        
        # Date and time
        dates = event.get("dates", {}).get("start", {})
        event_date = dates.get("localDate")  # YYYY-MM-DD format
        event_time = dates.get("localTime")  # HH:MM:SS format
        
        # Convert time to HH:MM
        if event_time and len(event_time) >= 5:
            event_time = event_time[:5]
        
        # Description
        description = None
        if "info" in event:
            description = event["info"]
        elif "pleaseNote" in event:
            description = event["pleaseNote"]
        
        # URL
        event_url = event.get("url")
        
        # Image - get the best available
        image_url = None
        images = event.get("images", [])
        if images:
            # Prefer large images
            for img in images:
                if img.get("width", 0) >= 640:
                    image_url = img.get("url")
                    break
            if not image_url and images:
                image_url = images[0].get("url")
        
        # Price ranges
        price_min = None
        price_max = None
        price_ranges = event.get("priceRanges", [])
        if price_ranges:
            prices = []
            for pr in price_ranges:
                if "min" in pr:
                    prices.append(float(pr["min"]))
                if "max" in pr:
                    prices.append(float(pr["max"]))
            if prices:
                price_min = min(prices)
                price_max = max(prices)
        
        # Category/classification
        category = None
        classifications = event.get("classifications", [])
        if classifications:
            segment = classifications[0].get("segment", {})
            genre = classifications[0].get("genre", {})
            # Combine segment and genre (e.g., "Music - Rock")
            parts = []
            if segment.get("name"):
                parts.append(segment["name"])
            if genre.get("name"):
                parts.append(genre["name"])
            category = " - ".join(parts) if parts else None
        
        # Venue details
        venue_name = None
        venue_latitude = None
        venue_longitude = None

        embedded = event.get("_embedded", {})
        venues = embedded.get("venues", [])

        if venues:
            venue_data = venues[0]
            venue_name = venue_data.get("name")

            location = venue_data.get("location") or {}
            venue_latitude = location.get("latitude")
            venue_longitude = location.get("longitude")
        
        # Performers (attractions): name plus the MusicBrainz ID used to look up
        # setlists on setlist.fm, and the artist's YouTube link when available.
        attractions = []
        for attraction in embedded.get("attractions", []) or []:
            name = attraction.get("name")
            if not name:
                continue
            links = attraction.get("externalLinks") or {}
            mbid = ((links.get("musicbrainz") or [{}])[0] or {}).get("id")
            youtube_url = ((links.get("youtube") or [{}])[0] or {}).get("url")
            attractions.append({
                "name": name,
                "ticketmaster_attraction_id": attraction.get("id"),
                "mbid": mbid,
                "youtube_url": youtube_url,
            })

        # Day of week
        day_of_week = get_day_of_week(event_date) if event_date else None
        
        return {
            "attractions": attractions,
            "title": title,
            "event_date": event_date,
            "event_time": event_time,
            "day_of_week": day_of_week,
            "description": description,
            "event_url": event_url,
            "image_url": image_url,
            "price_min": price_min,
            "price_max": price_max,
            "category": category,
            "venue_name": venue_name,
            "venue_latitude": venue_latitude,
            "venue_longitude": venue_longitude,
            "ticketmaster_id": event.get("id")
        }
        
    except Exception as e:
        print(f"[TicketmasterAPI] Error parsing event: {e}")
        return None


# Convenience function matching the existing scraper interface
async def scrape_ticketmaster_api(
    keyword: Optional[str] = None,
    days_ahead: int = 90,
    day_of_week: Optional[str] = None
) -> list:
    """
    Scrape events from Ticketmaster using the Discovery API.
    
    This function matches the existing scraper interface for drop-in replacement.
    Always searches the Saint Louis, MO area.
    
    Parameters:
        keyword: Optional keyword filter
        days_ahead: Number of days to search ahead (default: 90)
        day_of_week: Filter by day (e.g., "Monday", "Mon", "Sat")
    
    Returns:
        List of event dicts in standard format
    """
    start_date = datetime.utcnow().isoformat() + "Z"
    end_date = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + "Z"
    
    return await search_events(
        keyword=keyword,
        day_of_week=day_of_week,
        start_date_time=start_date,
        end_date_time=end_date,
        size=100
    )


# Export constants for dropdown usage
DAYS_OF_WEEK = DAY_NAMES  # ["Monday", "Tuesday", ...]
DAYS_ABBREVIATED = DAY_ABBREVS  # ["Mon", "Tue", ...]
CLASSIFICATION_LIST = CLASSIFICATIONS  # ["Music", "Sports", ...]
