"""
Family Arena calendar scraper.
Scrapes events from https://familyarena.com/calendar/
"""
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


async def scrape_familyarena(url: str = "https://familyarena.com/calendar/") -> list:
    """
    Scrapes events from Family Arena calendar page.
    
    Args:
        url: The calendar URL (default: https://familyarena.com/calendar/)
    
    Returns a list of event dicts with:
      - title (str)
      - event_date (str) - ISO format date
      - event_time (str)
      - description (str)
      - event_url (str)
      - image_url (str)
      - price_min (float) - None for Family Arena
      - price_max (float) - None for Family Arena
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
            print(f"[FamilyArena] Navigating to {url}")
            await page.goto(url, timeout=60000, wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # Extract events using The Events Calendar structure
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
                        
                        // Get description
                        let description = null;
                        if (container) {
                            const descEl = container.querySelector('.tribe-events-calendar-list__event-description p, .description p');
                            if (descEl) description = descEl.innerText.trim();
                        }
                        
                        // Get image
                        let imageUrl = null;
                        if (container) {
                            const img = container.querySelector('img');
                            if (img) imageUrl = img.src;
                        }
                        
                        // Get category from CSS classes
                        let category = null;
                        if (container) {
                            const classList = container.className || '';
                            const catMatch = classList.match(/tribe_events_cat-([a-z-]+)/);
                            if (catMatch) {
                                category = catMatch[1].replace(/-/g, ' ');
                            }
                        }
                        
                        results.push({
                            title: title,
                            event_date: eventDate,
                            event_time: eventTime,
                            description: description ? description.slice(0, 500) : null,
                            event_url: href,
                            image_url: imageUrl,
                            price_min: null,
                            price_max: null,
                            category: category
                        });
                    });
                    
                    return results;
                }
            """)

            print(f"[FamilyArena] Found {len(events)} events")
            return events or []

        except PlaywrightTimeout as e:
            raise Exception(f"FamilyArena scraper timed out: {e}")
        except Exception as e:
            raise Exception(f"FamilyArena scraper error: {e}")
        finally:
            await browser.close()


# For testing
if __name__ == "__main__":
    events = asyncio.run(scrape_familyarena())
    for e in events:
        print("-" * 60)
        print(f"Title: {e['title']}")
        print(f"Date: {e['event_date']}")
        print(f"Time: {e['event_time']}")
        print(f"Category: {e['category']}")
        print(f"URL: {e['event_url']}")
        print(f"Image: {e['image_url'][:80] if e['image_url'] else 'N/A'}...")
