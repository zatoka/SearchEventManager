"""
Test script for The Factory STL scraper.
"""
import asyncio
from playwright.async_api import async_playwright


async def check_event_page(page, url):
    """Get details from an individual event page."""
    await page.goto(url, timeout=60000)
    await page.wait_for_timeout(2000)
    
    data = await page.evaluate("""
        () => {
            const result = {};
            
            // Title from OG or h1
            const ogTitle = document.querySelector('meta[property="og:title"]');
            const h1 = document.querySelector('h1');
            result.title = ogTitle ? ogTitle.content : (h1 ? h1.innerText.trim() : '');
            
            // Description
            const ogDesc = document.querySelector('meta[property="og:description"]');
            result.description = ogDesc ? ogDesc.content : '';
            
            // Image
            const ogImage = document.querySelector('meta[property="og:image"]');
            result.image_url = ogImage ? ogImage.content : '';
            
            // Date - look for time element or date text
            const timeEl = document.querySelector('time');
            if (timeEl) {
                result.event_date = timeEl.getAttribute('datetime') || timeEl.innerText.trim();
            }
            
            // Look for date in page text
            const dateMatch = document.body.innerText.match(/(January|February|March|April|May|June|July|August|September|October|November|December)\\s*\\d{1,2},?\\s*\\d{4}/i);
            if (dateMatch) {
                result.date_text = dateMatch[0];
            }
            
            // Time
            const timeMatch = document.body.innerText.match(/(\\d{1,2}:\\d{2}\\s*(am|pm|AM|PM))/);
            if (timeMatch) {
                result.event_time = timeMatch[1];
            }
            
            return result;
        }
    """)
    
    data['event_url'] = url
    return data


async def check_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # First get list of events from main page
        await page.goto('https://thefactorystl.com/', timeout=60000)
        await page.wait_for_timeout(5000)
        
        # Get event URLs
        event_urls = await page.evaluate("""
            () => {
                const urls = [];
                document.querySelectorAll('a[href*="/events/"]').forEach(link => {
                    const href = link.href;
                    if (href.includes('private-events') || href.includes('#events')) return;
                    if (!urls.includes(href)) urls.push(href);
                });
                return urls;
            }
        """)
        
        print(f"Found {len(event_urls)} event URLs")
        
        # Get details from first 3 events
        events = []
        for i, url in enumerate(event_urls[:3]):
            print(f"\n--- Fetching event {i+1}: {url.split('/')[-2]} ---")
            try:
                event_data = await check_event_page(page, url)
                events.append(event_data)
                print(f"Title: {event_data.get('title', 'N/A')}")
                print(f"Date: {event_data.get('date_text', event_data.get('event_date', 'N/A'))}")
                print(f"Time: {event_data.get('event_time', 'N/A')}")
                print(f"Image: {event_data.get('image_url', 'N/A')[:60]}...")
            except Exception as e:
                print(f"Error: {e}")
        
        await browser.close()
        return events


if __name__ == "__main__":
    asyncio.run(check_page())
