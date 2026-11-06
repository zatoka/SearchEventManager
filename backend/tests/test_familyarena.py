"""
Test script for Family Arena scraper.
"""
import asyncio
from playwright.async_api import async_playwright


async def check_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('https://familyarena.com/calendar/', timeout=60000)
        await page.wait_for_timeout(5000)
        
        # Check what elements are on the page
        print("=== Checking page structure ===")
        counts = await page.evaluate("""
            () => {
                return {
                    articles: document.querySelectorAll('article').length,
                    event_links: document.querySelectorAll('a[href*="/event/"]').length,
                    time_elements: document.querySelectorAll('time').length
                };
            }
        """)
        
        print(f"Articles: {counts['articles']}")
        print(f"Event links: {counts['event_links']}")
        print(f"Time elements: {counts['time_elements']}")
        
        # Get events
        print("\n=== Getting events ===")
        events = await page.evaluate("""
            () => {
                const results = [];
                const links = document.querySelectorAll('a[href*="/event/"]');
                
                links.forEach(link => {
                    const title = link.innerText.trim();
                    const href = link.href;
                    
                    if (!title || !href) return;
                    
                    // Find the closest article container
                    let container = link.closest('article');
                    if (!container) container = link.closest('[class*="event"]');
                    if (!container) container = link.parentElement?.parentElement?.parentElement;
                    
                    // Get date from time element
                    let eventDate = null;
                    let eventTime = null;
                    if (container) {
                        const timeEl = container.querySelector('time');
                        if (timeEl) {
                            eventDate = timeEl.getAttribute('datetime');
                            const timeText = timeEl.innerText.trim();
                            // Extract time like "7:00 pm"
                            const timeMatch = timeText.match(/@(\\s*\\d{1,2}:\\d{2}\\s*(am|pm))/i);
                            if (timeMatch) eventTime = timeMatch[1].trim();
                        }
                    }
                    
                    // Get image
                    let imageUrl = null;
                    if (container) {
                        const img = container.querySelector('img');
                        if (img) imageUrl = img.src;
                    }
                    
                    results.push({
                        title: title,
                        event_url: href,
                        event_date: eventDate,
                        event_time: eventTime,
                        image_url: imageUrl
                    });
                });
                
                return results;
            }
        """)
        
        print(f"Found {len(events)} events:")
        for e in events:
            print(f"\n  Title: {e['title'][:60]}")
            print(f"  Date: {e['event_date']} {e['event_time']}")
            print(f"  URL: {e['event_url']}")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(check_page())
