"""
MetroTix scraper for Jazz St. Louis and other venues.

MetroTix is a ticketing platform used by several St. Louis venues.
Example HTML structure:
  <a href="https://www.metrotix.com/events/detail/jsl-marcus-roberts" title="More Info for MARCUS ROBERTS &amp; THE MODERN JAZZ GENERATION">
    <img src="https://www.metrotix.com/assets/img/MarcusRoberts_thumbnail-f22d9b3a1a.jpg" alt="More Info for MARCUS ROBERTS &amp; THE MODERN JAZZ GENERATION"/>
  </a>
  <div class="info clearfix">
    <div class="date">
      <span class="m-date__rangeFirst"><span class="m-date__month">November </span><span class="m-date__day">18</span></span>
      <span class="m-date__separator"> - </span>
      <span class="m-date__rangeLast"><span class="m-date__day">21</span><span class="m-date__year">, 2026</span></span>
    </div>
  </div>
"""
import re
import asyncio
import uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


def _scrape_metrotix_sync(url: str) -> list:
    """
    Synchronous version of MetroTix scraper using sync_playwright.
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
            print(f"[MetroTix] Navigating to {url}")
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            
            # Wait for content to load
            page.wait_for_timeout(3000)

            # Extract events using JavaScript
            events = page.evaluate("""
                () => {
                    const events = [];
                    const seenUrls = new Set();
                    
                    // Find all event items (MetroTix uses .eventItem class)
                    const eventItems = document.querySelectorAll('.eventItem, .event-listing, .event-card');
                    
                    eventItems.forEach(item => {
                        try {
                            // Find the event link inside this item
                            const link = item.querySelector('a[href*="/events/detail/"]');
                            if (!link) return;
                            
                            const eventUrl = link.href;
                            
                            // Skip duplicates
                            if (seenUrls.has(eventUrl)) return;
                            seenUrls.add(eventUrl);
                            
                            // Get title - extract from title attribute or alt text
                            let title = link.getAttribute('title') || '';
                            const img = link.querySelector('img');
                            
                            // Extract actual title from "More Info for EVENT NAME" pattern
                            const titleMatch = title.match(/More Info for (.+)/i);
                            if (titleMatch) {
                                title = titleMatch[1].trim();
                            } else if (img && img.alt) {
                                const altMatch = img.alt.match(/More Info for (.+)/i);
                                title = altMatch ? altMatch[1].trim() : img.alt.trim();
                            }
                            
                            // Skip if no valid title
                            if (!title || title.length < 2) return;
                            
                            // Get image URL
                            const imageUrl = img ? img.src : null;
                            
                            // Find date info inside the .info .date element
                            let dateText = '';
                            const dateEl = item.querySelector('.info .date');
                            if (dateEl) {
                                dateText = dateEl.innerText || dateEl.textContent;
                            }
                            
                            events.push({
                                title: title,
                                event_url: eventUrl,
                                image_url: imageUrl,
                                date_text: dateText.trim()
                            });
                        } catch (e) {
                            // Skip this item
                        }
                    });
                    
                    return events;
                }
            """)

            print(f"[MetroTix] Found {len(events)} event links")
            
            # Process events and parse dates
            result = []
            for event in events:
                date_text = event.get('date_text', '')
                date_info = _parse_date_from_text(date_text)
                
                # Generate unique ID from event URL
                event_id = event.get('event_url', '').split('/')[-1] or str(uuid.uuid4())
                
                event['ticketmaster_id'] = event_id
                event['event_date'] = date_info.get('date')
                event['event_time'] = date_info.get('time')
                event['day_of_week'] = date_info.get('day_of_week')
                event['venue_name'] = 'Jazz St. Louis'
                event['category'] = 'Music - Jazz'
                event['description'] = None
                event['price_min'] = None
                event['price_max'] = None
                
                result.append(event)
            
            # Sort by date (earliest first), then by time
            result.sort(key=lambda e: (e.get("event_date") or "9999-99-99", e.get("event_time") or ""))
            
            return result

        except PlaywrightTimeout as e:
            raise Exception(f"MetroTix scraper timed out: {e}")
        except Exception as e:
            raise Exception(f"MetroTix scraper error: {e}")
        finally:
            browser.close()


async def scrape_metrotix(url: str) -> list:
    """
    Scrape events from MetroTix venue page.
    
    Parameters:
        url: MetroTix venue URL (e.g., https://www.metrotix.com/events/venue/jazz-st-louis)
    
    Returns:
        List of event dicts with standard format
    """
    # Run sync version in thread pool to avoid Windows asyncio issues with Playwright
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as executor:
        result = await loop.run_in_executor(executor, _scrape_metrotix_sync, url)
    return result


def _parse_date_from_text(text: str) -> dict:
    """Parse date and time from MetroTix date text.
    
    Examples:
        "November 18 - 21, 2026" (date range)
        "Wed. November  4, 2026 /  7:30 PM"
    """
    if not text:
        return {'date': None, 'time': None, 'day_of_week': None}
    
    result = {'date': None, 'time': None, 'day_of_week': None}
    
    # Pattern: "Wed. November  4, 2026 /  7:30 PM"
    full_pattern = r'(\w+\.?)\s+(\w+)\s+(\d+),?\s+(\d{4})\s*/?\s*(\d+:\d+\s*(?:AM|PM))?'
    match = re.search(full_pattern, text)
    
    if match:
        day_name, month, day, year, time = match.groups()
        try:
            date_str = f"{month} {day}, {year}"
            date_obj = datetime.strptime(date_str, '%B %d, %Y')
            result['date'] = date_obj.strftime('%Y-%m-%d')
            result['time'] = time.strip() if time else None
            result['day_of_week'] = date_obj.strftime('%A')
        except ValueError:
            pass
    
    # If no time found yet, try simpler date pattern
    if result['date'] is None:
        # Pattern: "November 18, 2026" or "November  18 - 21, 2026"
        simple_pattern = r'(\w+)\s+(\d+)(?:\s*-\s*\d+)?,?\s+(\d{4})'
        match = re.search(simple_pattern, text)
        if match:
            month, day, year = match.groups()
            try:
                date_str = f"{month} {day}, {year}"
                date_obj = datetime.strptime(date_str, '%B %d, %Y')
                result['date'] = date_obj.strftime('%Y-%m-%d')
                result['day_of_week'] = date_obj.strftime('%A')
            except ValueError:
                pass
    
    return result


# Convenience function for Jazz St. Louis
async def scrape_jazz_st_louis() -> list:
    """Scrape Jazz St. Louis events from MetroTix."""
    return await scrape_metrotix('https://www.metrotix.com/events/venue/jazz-st-louis')
