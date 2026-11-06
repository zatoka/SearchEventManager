"""
Test Ticketmaster scraper for The Factory STL.
"""
import asyncio
import sys
sys.path.insert(0, '..')
from scrapers.ticketmaster import scrape_ticketmaster

events = asyncio.run(scrape_ticketmaster('https://www.ticketmaster.com/the-factory-tickets-chesterfield/venue/270545'))
print(f'Found {len(events)} events')
for e in events[:10]:
    title = e.get('title', 'N/A')[:50] if e.get('title') else 'N/A'
    date = e.get('event_date', 'N/A')
    print(f"  {title} - {date}")
