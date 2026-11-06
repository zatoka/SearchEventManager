"""Test City Winery scraper."""
import asyncio
import sys
sys.path.insert(0, '.')

from scrapers.city_winery import scrape_city_winery_st_louis

async def test():
    print('Scraping City Winery St. Louis events...\n')
    
    events = await scrape_city_winery_st_louis()
    
    print(f'Found {len(events)} events\n')
    
    for e in events[:10]:
        print(f"  - {e['title']}")
        print(f"    Date: {e['event_date']}")
        print(f"    URL: {e.get('event_url', 'N/A')}")
        print(f"    Image: {e.get('image_url', 'N/A')}")
        print()

if __name__ == "__main__":
    asyncio.run(test())
