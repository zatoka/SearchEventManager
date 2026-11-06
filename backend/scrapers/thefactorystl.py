"""
The Factory STL scraper.
Scrapes events from https://thefactorystl.com/
"""
import asyncio
import re
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


async def scrape_thefactorystl(url: str = "https://thefactorystl.com/") -> list:
    """
    Scrapes events from The Factory STL website.
    
    Args:
        url: The website URL (default: https://thefactorystl.com/)
    
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
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
        )
        page = await context.new_page()

        try:
            print(f"[TheFactorySTL] Navigating to {url}")
            await page.goto(url, timeout=60000, wait_until="networkidle")
            await page.wait_for_timeout(5000)

            # Extract events from the main page
            # The dates are shown as "Sep 22", "Sep 25", etc. near each event
            events = await page.evaluate("""
                () => {
                    const results = [];
                    
                    // Find all event info links
                    const eventLinks = document.querySelectorAll('a[href*="/events/"]');
                    
                    eventLinks.forEach(link => {
                        const href = link.href;
                        // Skip nav links
                        if (href.includes('private-events') || href.includes('#events')) return;
                        
                        // Extract event slug from URL for title
                        const slug = href.split('/events/')[1]?.replace('/', '') || '';
                        let title = slug
                            .replace(/-/g, ' ')
                            .replace(/\\b\\w/g, c => c.toUpperCase());
                        
                        // Find parent container to get date
                        let container = link.parentElement;
                        for (let i = 0; i < 6; i++) {
                            if (container) container = container.parentElement;
                        }
                        
                        // Look for date in container - format: "Sep 22"
                        let eventDate = null;
                        let dateText = '';
                        if (container) {
                            const text = container.innerText;
                            const dateMatch = text.match(/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\s*(\\d{1,2})/i);
                            if (dateMatch) {
                                dateText = dateMatch[0];
                            }
                        }
                        
                        // Find image
                        let imageUrl = null;
                        if (container) {
                            const img = container.querySelector('img');
                            if (img) imageUrl = img.src;
                        }
                        
                        results.push({
                            title,
                            date_text: dateText,
                            event_time: null,
                            description: null,
                            event_url: href,
                            image_url: imageUrl,
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
            
            # Convert date_text to ISO format in Python
            month_map = {
                'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12',
                'January': '01', 'February': '02', 'March': '03', 'April': '04',
                'June': '06', 'July': '07', 'August': '08', 'September': '09',
                'October': '10', 'November': '11', 'December': '12'
            }
            
            for event in events:
                if event.get('date_text'):
                    # Clean up whitespace and normalize
                    date_text = event['date_text'].replace('\r', ' ').replace('\n', ' ').strip()
                    match = re.match(r'(\w+)\s*(\d{1,2})', date_text)
                    if match:
                        month_name = match.group(1).title()  # Normalize to Title case (Sep)
                        day = match.group(2).zfill(2)
                        month = month_map.get(month_name) or month_map.get(month_name[:3], '01')
                        event['event_date'] = f"2026-{month}-{day}"
                    else:
                        event['event_date'] = None
                else:
                    event['event_date'] = None

            print(f"[TheFactorySTL] Found {len(events)} events")
            return events

        except PlaywrightTimeout as e:
            raise Exception(f"TheFactorySTL scraper timed out: {e}")
        except Exception as e:
            raise Exception(f"TheFactorySTL scraper error: {e}")
        finally:
            await browser.close()


# For testing
if __name__ == "__main__":
    events = asyncio.run(scrape_thefactorystl())
    for e in events[:10]:
        print("-" * 60)
        print(f"Title: {e['title']}")
        print(f"Date: {e.get('event_date', 'N/A')}")
        print(f"URL: {e['event_url']}")
        print(f"Image: {e.get('image_url', 'N/A')[:60] if e.get('image_url') else 'N/A'}...")
