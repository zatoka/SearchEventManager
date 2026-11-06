"""Test MetroTix scraper for Jazz St. Louis."""
import asyncio
import sys
sys.path.insert(0, '.')

from scrapers.metrotix import scrape_jazz_st_louis

async def test():
    print('Testing Jazz St. Louis scraper...')
    try:
        events = await scrape_jazz_st_louis()
        print(f'Found {len(events)} events\n')
        for e in events[:5]:
            print(f"  - {e['title']}")
            print(f"    Date: {e['event_date']} ({e.get('day_of_week', 'N/A')})")
            print(f"    Time: {e['event_time']}")
            print()
    except Exception as ex:
        print(f"Error: {ex}")

if __name__ == "__main__":
    asyncio.run(test())
