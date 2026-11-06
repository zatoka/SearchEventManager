"""
Ticketmaster scraper for events.
"""
import re
import os
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


async def scrape_ticketmaster(url: str) -> list:
    """
    Scrapes events from Ticketmaster venue page.
    
    Returns a list of event dicts with:
      - title (str)
      - event_date (str)
      - event_time (str)
      - description (str)
      - event_url (str)
      - image_url (str)
      - price_min (float)
      - price_max (float)
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
            print(f"[Ticketmaster] Navigating to {url}")
            await page.goto(url, timeout=60000, wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # Extract events
            events = await page.evaluate("""
                () => {
                    const events = [];
                    
                    // Look for event listings (Ticketmaster structure varies by venue)
                    const eventCards = document.querySelectorAll('[data-testid="event-listing"], .event-listing, .event-card, article');
                    
                    eventCards.forEach(card => {
                        try {
                            // Title
                            const titleEl = card.querySelector('[data-testid="event-title"], .event-title, h2, h3');
                            const title = titleEl ? titleEl.innerText.trim() : null;
                            
                            if (!title) return;
                            
                            // Date
                            const dateEl = card.querySelector('[data-testid="event-date"], .event-date, time');
                            const eventDate = dateEl ? dateEl.getAttribute('datetime') || dateEl.innerText.trim() : null;
                            
                            // Time
                            const timeEl = card.querySelector('[data-testid="event-time"], .event-time');
                            const eventTime = timeEl ? timeEl.innerText.trim() : null;
                            
                            // URL
                            const linkEl = card.querySelector('a[href*="/event/"]');
                            const eventUrl = linkEl ? linkEl.href : null;
                            
                            // Image
                            const imgEl = card.querySelector('img');
                            const imageUrl = imgEl ? imgEl.src : null;
                            
                            // Price
                            const priceEl = card.querySelector('[data-testid="event-price"], .price');
                            let priceMin = null;
                            let priceMax = null;
                            if (priceEl) {
                                const priceText = priceEl.innerText;
                                const prices = priceText.match(/\\$[\\d,]+/g);
                                if (prices) {
                                    const nums = prices.map(p => parseFloat(p.replace(/[$,]/g, '')));
                                    priceMin = Math.min(...nums);
                                    priceMax = Math.max(...nums);
                                }
                            }
                            
                            events.push({
                                title,
                                event_date: eventDate,
                                event_time: eventTime,
                                description: null,
                                event_url: eventUrl,
                                image_url: imageUrl,
                                price_min: priceMin,
                                price_max: priceMax,
                                category: null
                            });
                        } catch (e) {
                            // Skip this card
                        }
                    });
                    
                    return events;
                }
            """)

            print(f"[Ticketmaster] Found {len(events)} events")
            return events or []

        except PlaywrightTimeout as e:
            raise Exception(f"Ticketmaster scraper timed out: {e}")
        except Exception as e:
            raise Exception(f"Ticketmaster scraper error: {e}")
        finally:
            await browser.close()
