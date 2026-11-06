"""
City Winery scraper for St. Louis venue.

City Winery uses tickets.citywinery.com for ticketing.
Events are JavaScript-rendered, so we use Playwright.

Example event URLs:
- https://tickets.citywinery.com/event/android-paranoid-radiohead-tribute-yrkubl
- https://tickets.citywinery.com/event/kenny-lattimore-um49ys
"""
import re
import uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


def _parse_date(date_text: str) -> str:
    """
    Parse date from various formats.
    Examples:
    - "August 22nd at 7:30pm"
    - "January 24-31, 2027"
    - "Oct 15"
    """
    if not date_text:
        return None
    
    # Clean up the text
    date_text = date_text.strip()
    
    # Try various patterns
    patterns = [
        # "January 24-31, 2027" -> take first date
        r'(\w+\s+\d{1,2})(?:-\d{1,2})?,?\s*(\d{4})?',
        # "August 22nd" or "Aug 22"
        r'(\w+\s+\d{1,2})(?:st|nd|rd|th)?',
        # "Oct 15, 2026"
        r'(\w+\s+\d{1,2},?\s*\d{4})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, date_text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            # Add year if not present
            if not re.search(r'\d{4}', date_str):
                date_str += f" {datetime.now().year}"
            
            try:
                # Try to parse
                dt = datetime.strptime(date_str.strip(), '%B %d %Y')
                return dt.strftime('%Y-%m-%d')
            except:
                try:
                    dt = datetime.strptime(date_str.strip(), '%b %d %Y')
                    return dt.strftime('%Y-%m-%d')
                except:
                    continue
    
    return None


def _scrape_city_winery_sync(url: str) -> list:
    """
    Synchronous version of City Winery scraper using sync_playwright.
    This runs in a thread pool to avoid Windows asyncio issues.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
        )
        page = context.new_page()

        try:
            print(f"[City Winery] Navigating to {url}")
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            
            # Wait for content to load
            page.wait_for_timeout(5000)

            # Extract events using JavaScript
            events = page.evaluate("""
                () => {
                    const events = [];
                    const seenUrls = new Set();
                    
                    // Find all event links - City Winery uses various structures
                    // Try different selectors
                    const selectors = [
                        'a[href*="/event/"]',
                        '.event-card a',
                        '.event-item a',
                        '.event-listing a'
                    ];
                    
                    let links = [];
                    for (const selector of selectors) {
                        const found = document.querySelectorAll(selector);
                        if (found.length > 0) {
                            links = found;
                            break;
                        }
                    }
                    
                    links.forEach(link => {
                        try {
                            const eventUrl = link.href;
                            
                            // Skip duplicates and non-event URLs
                            if (seenUrls.has(eventUrl)) return;
                            if (!eventUrl.includes('/event/')) return;
                            
                            seenUrls.add(eventUrl);
                            
                            // Get title - try various methods
                            let title = link.getAttribute('title') || 
                                       link.textContent.trim() ||
                                       link.innerText.trim();
                            
                            // Clean up title
                            title = title.replace(/\\s+/g, ' ').trim();
                            
                            // Skip if title is too short or generic
                            if (!title || title.length < 3) return;
                            if (title.toLowerCase().includes('sign in')) return;
                            if (title.toLowerCase().includes('log in')) return;
                            
                            // Get image if available
                            const img = link.querySelector('img');
                            const imageUrl = img ? img.src : null;
                            
                            // Try to find date - look for date elements nearby
                            let dateText = '';
                            
                            // Check parent elements for date info
                            let parent = link.closest('.event-card, .event-item, .event, article, li, div');
                            if (parent) {
                                // Look for date-related elements
                                const dateSelectors = [
                                    '.date', '.event-date', '.datetime', 
                                    'time', '[class*="date"]', '[class*="time"]'
                                ];
                                for (const sel of dateSelectors) {
                                    const dateEl = parent.querySelector(sel);
                                    if (dateEl) {
                                        dateText = dateEl.textContent || dateEl.innerText;
                                        break;
                                    }
                                }
                                
                                // If no date element found, try to extract from text
                                if (!dateText) {
                                    const text = parent.textContent || parent.innerText;
                                    // Look for month names
                                    const monthMatch = text.match(/(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\\s+\\d{1,2}/i);
                                    if (monthMatch) {
                                        dateText = monthMatch[0];
                                    }
                                }
                            }
                            
                            events.push({
                                title: title,
                                event_url: eventUrl,
                                image_url: imageUrl,
                                date_text: dateText.trim()
                            });
                        } catch (err) {
                            // Skip this event
                        }
                    });
                    
                    return events;
                }
            """)

            print(f"[City Winery] Found {len(events)} event links")

            # Process events
            processed_events = []
            for event in events:
                # Parse date
                event_date = _parse_date(event.get('date_text', ''))
                
                # Create event record
                processed_events.append({
                    'id': str(uuid.uuid4()),
                    'title': event['title'],
                    'event_date': event_date,
                    'event_url': event['event_url'],
                    'image_url': event.get('image_url'),
                    'venue_name': 'City Winery St. Louis',
                    'venue_id': 'city-winery-st-louis',
                    'source': 'city_winery',
                    'status': 'active',
                    'category': 'Music',
                })

            return processed_events

        except PlaywrightTimeout as e:
            print(f"[City Winery] Timeout error: {e}")
            return []
        except Exception as e:
            print(f"[City Winery] Error: {e}")
            return []
        finally:
            browser.close()


async def scrape_city_winery_st_louis() -> list:
    """
    Scrape events from City Winery St. Louis.
    
    Returns:
        List of event dictionaries
    """
    import asyncio
    
    # Use the main events page
    url = "https://citywinery.com/pages/events/st-louis"
    
    # Run in thread pool to avoid Windows asyncio issues
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as executor:
        events = await loop.run_in_executor(executor, _scrape_city_winery_sync, url)
    
    return events


# For testing
if __name__ == "__main__":
    import asyncio
    events = asyncio.run(scrape_city_winery_st_louis())
    print(f"\nFound {len(events)} events:")
    for e in events:
        print(f"  - {e['title']}")
        print(f"    Date: {e['event_date']}")
        print(f"    URL: {e['event_url']}")
        print()
