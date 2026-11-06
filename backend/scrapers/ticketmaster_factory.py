"""
Ticketmaster venue scraper optimized for The Factory STL.
Uses a simpler approach that works with Ticketmaster's anti-bot measures.
"""
import asyncio
import re
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


async def scrape_ticketmaster_factory(url: str = "https://www.ticketmaster.com/the-factory-tickets-chesterfield/venue/270545") -> list:
    """
    Scrapes events from Ticketmaster venue page for The Factory STL.
    
    Args:
        url: The Ticketmaster venue URL
    
    Returns a list of event dicts with:
      - title (str)
      - event_date (str) - ISO format date
      - event_time (str)
      - description (str)
      - event_url (str)
      - image_url (str)
      - price_min (float) - None
      - price_max (float) - None
      - category (str)
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
        )
        page = await context.new_page()

        try:
            print(f"[TicketmasterFactory] Navigating to {url}")
            # Use 'domcontentloaded' instead of 'networkidle' for faster loading
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)

            # Extract events from the page
            events = await page.evaluate("""
                () => {
                    const results = [];
                    
                    // Look for event listings
                    const eventCards = document.querySelectorAll('[data-testid="event-listing"], .event-listing, article, [class*="event"]');
                    
                    // Also try finding by date patterns in text
                    const allText = document.body.innerText;
                    const datePattern = /(January|February|March|April|May|June|July|August|September|October|November|December)\\s*\\d{1,2},?\\s*\\d{4}/gi;
                    
                    // Find all links that might be events
                    document.querySelectorAll('a[href*="/event/"]').forEach(link => {
                        const href = link.href;
                        const title = link.innerText.trim();
                        
                        if (!title || !href) return;
                        
                        // Find parent container
                        let container = link.closest('article, [class*="event"]');
                        if (!container) container = link.parentElement?.parentElement?.parentElement;
                        
                        // Try to find date in container
                        let eventDate = null;
                        let eventTime = null;
                        
                        if (container) {
                            const text = container.innerText;
                            // Date pattern: "September 22, 2026"
                            const dateMatch = text.match(/(January|February|March|April|May|June|July|August|September|October|November|December)\\s*(\\d{1,2}),?\\s*(\\d{4})/i);
                            if (dateMatch) {
                                eventDate = dateMatch[0];
                            }
                            // Time pattern: "07:30 PM"
                            const timeMatch = text.match(/(\\d{1,2}:\\d{2}\\s*(AM|PM))/i);
                            if (timeMatch) {
                                eventTime = timeMatch[1];
                            }
                        }
                        
                        results.push({
                            title,
                            event_url: href,
                            event_date: eventDate,
                            event_time: eventTime,
                            description: null,
                            image_url: null,
                            price_min: null,
                            price_max: null,
                            category: null
                        });
                    });
                    
                    // Remove duplicates by URL
                    const seen = new Set();
                    return results.filter(e => {
                        if (seen.has(e.event_url)) return false;
                        seen.add(e.event_url);
                        return true;
                    });
                }
            """)

            print(f"[TicketmasterFactory] Found {len(events)} events")
            
            # Convert date strings to ISO format
            for event in events:
                if event.get('event_date'):
                    try:
                        # Parse "September 22, 2026" format
                        parsed = datetime.strptime(event['event_date'].replace(',', ''), '%B %d %Y')
                        event['event_date'] = parsed.strftime('%Y-%m-%d')
                    except:
                        pass

            return events or []

        except PlaywrightTimeout as e:
            raise Exception(f"TicketmasterFactory scraper timed out: {e}")
        except Exception as e:
            raise Exception(f"TicketmasterFactory scraper error: {e}")
        finally:
            await browser.close()


# For testing
if __name__ == "__main__":
    events = asyncio.run(scrape_ticketmaster_factory())
    for e in events[:10]:
        print("-" * 60)
        print(f"Title: {e['title']}")
        print(f"Date: {e.get('event_date', 'N/A')}")
        print(f"Time: {e.get('event_time', 'N/A')}")
        print(f"URL: {e['event_url']}")
