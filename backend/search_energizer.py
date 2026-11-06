"""Search for events at Energizer Park."""
import asyncio
import sys
sys.path.insert(0, '.')

from scrapers.ticketmaster_api import search_events

async def main():
    print('Searching for events at Energizer Park...\n')
    
    # Try different classifications
    classifications = ["Sports", "Music", "Arts & Theatre", None]
    
    for classification in classifications:
        print(f'\n{"="*60}')
        print(f'Classification: {classification or "All"}')
        print(f'{"="*60}\n')
        
        events = await search_events(
            classification_name=classification,
            venue_name="Energizer Park",
            size=100
        )
        
        print(f'Found {len(events)} events\n')
        
        for e in events[:5]:  # Show max 5 per classification
            print(f"  - {e['title']}")
            print(f"    Venue: {e.get('venue_name', 'N/A')}")
            print(f"    Date: {e['event_date']}")
            print()

if __name__ == "__main__":
    asyncio.run(main())
