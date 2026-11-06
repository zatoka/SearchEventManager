"""Test Energizer Park venue filter."""
import asyncio
import sys
sys.path.insert(0, '.')

from scrapers.ticketmaster_api import search_events

async def test():
    print('Searching Sports events, then filtering by Energizer Park...\n')
    
    # This is how the API route works - fetches all Sports, then filters client-side
    events = await search_events(
        classification_name="Sports",
        venue_name="Energizer Park",
        size=100
    )
    
    print(f'Found {len(events)} events\n')
    
    for e in events[:10]:
        print(f"  - {e['title']}")
        print(f"    Venue: {e.get('venue_name', 'N/A')}")
        print(f"    Date: {e['event_date']}")
        print()

if __name__ == "__main__":
    asyncio.run(test())
