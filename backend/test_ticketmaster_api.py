"""
Test script for Ticketmaster Discovery API integration.
Run this to verify your API key and see Saint Louis events.
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta

# The key is read from %APPDATA%\search-events-manager\.env (see config.py).
from config import get_ticketmaster_api_key, TICKETMASTER_BASE_URL

DEFAULT_CITY = "Saint Louis"
DEFAULT_STATE_CODE = "MO"

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_day_of_week(date_str):
    if not date_str:
        return None
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return DAY_NAMES[date_obj.weekday()]
    except (ValueError, TypeError):
        return None


def filter_events_by_day(events, day_filter):
    if not day_filter:
        return events
    
    day_filter = day_filter.strip().lower()
    
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
    
    filtered = []
    for event in events:
        event_date = event.get("event_date")
        if event_date:
            event_day = get_day_of_week(event_date)
            if event_day == target_day:
                filtered.append(event)
    
    return filtered


async def search_events(keyword=None, classification_name=None, start_date_time=None, 
                        end_date_time=None, day_of_week=None, size=100, page=0,
                        city=DEFAULT_CITY, state_code=DEFAULT_STATE_CODE):
    endpoint = f"{TICKETMASTER_BASE_URL}/events.json"
    
    params = {
        "apikey": get_ticketmaster_api_key(),
        "city": city,
        "stateCode": state_code,
        "size": min(size, 100),
        "page": page
    }
    
    if keyword:
        params["keyword"] = keyword
    if classification_name:
        params["classificationName"] = classification_name
    if start_date_time:
        params["startDateTime"] = start_date_time
    if end_date_time:
        params["endDateTime"] = end_date_time
    
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint, params=params) as response:
            if response.status == 401:
                raise Exception("Invalid Ticketmaster API key")
            elif response.status == 429:
                raise Exception("Rate limit exceeded")
            elif response.status != 200:
                text = await response.text()
                raise Exception(f"API error {response.status}: {text}")
            data = await response.json()
    
    events_data = data.get("_embedded", {}).get("events", [])
    events = []
    
    for event in events_data:
        event_dict = parse_event(event)
        if event_dict:
            events.append(event_dict)
    
    if day_of_week:
        events = filter_events_by_day(events, day_of_week)
    
    return events


def parse_event(event):
    try:
        title = event.get("name")
        if not title:
            return None
        
        dates = event.get("dates", {}).get("start", {})
        event_date = dates.get("localDate")
        event_time = dates.get("localTime")
        
        if event_time and len(event_time) >= 5:
            event_time = event_time[:5]
        
        description = event.get("info") or event.get("pleaseNote")
        event_url = event.get("url")
        
        image_url = None
        images = event.get("images", [])
        if images:
            for img in images:
                if img.get("width", 0) >= 640:
                    image_url = img.get("url")
                    break
            if not image_url and images:
                image_url = images[0].get("url")
        
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
        
        category = None
        classifications = event.get("classifications", [])
        if classifications:
            segment = classifications[0].get("segment", {})
            genre = classifications[0].get("genre", {})
            parts = []
            if segment.get("name"):
                parts.append(segment["name"])
            if genre.get("name"):
                parts.append(genre["name"])
            category = " - ".join(parts) if parts else None
        
        venue_name = None
        embedded = event.get("_embedded", {})
        venues = embedded.get("venues", [])
        if venues:
            venue_name = venues[0].get("name")
        
        day_of_week = get_day_of_week(event_date) if event_date else None
        
        return {
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
            "ticketmaster_id": event.get("id")
        }
    except Exception as e:
        print(f"Error parsing event: {e}")
        return None


async def test_basic_search():
    print("\n" + "=" * 60)
    print("TEST 1: Basic Saint Louis Event Search")
    print("=" * 60)
    
    events = await search_events(size=10)
    
    print(f"\nFound {len(events)} events in Saint Louis area:\n")
    
    for i, event in enumerate(events[:10], 1):
        print(f"{i}. {event['title']}")
        print(f"   Date: {event['event_date']} at {event['event_time'] or 'TBD'}")
        print(f"   Venue: {event.get('venue_name', 'N/A')}")
        print(f"   Day: {event.get('day_of_week', 'N/A')}")
        print(f"   Category: {event.get('category', 'N/A')}")
        if event.get('price_min'):
            print(f"   Price: ${event['price_min']:.0f} - ${event['price_max']:.0f}")
        print()


async def test_day_of_week_filter():
    print("\n" + "=" * 60)
    print("TEST 2: Day of Week Filter (Saturday)")
    print("=" * 60)
    
    events = await search_events(day_of_week="Saturday", size=50)
    
    print(f"\nFound {len(events)} Saturday events:\n")
    
    for i, event in enumerate(events[:5], 1):
        print(f"{i}. {event['title']}")
        print(f"   Date: {event['event_date']} ({event.get('day_of_week', 'N/A')})")
        print()


async def main():
    print("\n" + "#" * 60)
    print("# TICKETMASTER DISCOVERY API TEST")
    print("# Saint Louis, MO Area")
    print("#" * 60)
    
    try:
        await test_basic_search()
        await test_day_of_week_filter()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\nERROR: {e}\n")
        raise


if __name__ == "__main__":
    asyncio.run(main())
