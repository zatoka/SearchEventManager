"""
AXS scraper for events.
"""
import re
import os
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


async def scrape_axs(url: str) -> list:
    """
    Scrapes events from AXS venue page.
    
    Returns a list of event dicts.
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
            print(f"[AXS] Navigating to {url}")
            await page.goto(url, timeout=60000, wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # Extract events
            events = await page.evaluate("""
                () => {
                    const events = [];
                    
                    // Look for event listings
                    const eventCards = document.querySelectorAll('.event-listing, .event-item, article, [class*="event"]');
                    
                    eventCards.forEach(card => {
                        try {
                            const titleEl = card.querySelector('.event-title, h2, h3, [class*="title"]');
                            const title = titleEl ? titleEl.innerText.trim() : null;
                            
                            if (!title) return;
                            
                            const dateEl = card.querySelector('.event-date, time, [class*="date"]');
                            const eventDate = dateEl ? dateEl.getAttribute('datetime') || dateEl.innerText.trim() : null;
                            
                            const timeEl = card.querySelector('.event-time, [class*="time"]');
                            const eventTime = timeEl ? timeEl.innerText.trim() : null;
                            
                            const linkEl = card.querySelector('a[href*="/event/"]');
                            const eventUrl = linkEl ? linkEl.href : window.location.href;
                            
                            const imgEl = card.querySelector('img');
                            const imageUrl = imgEl ? imgEl.src : null;
                            
                            events.push({
                                title,
                                event_date: eventDate,
                                event_time: eventTime,
                                description: null,
                                event_url: eventUrl,
                                image_url: imageUrl,
                                price_min: null,
                                price_max: null,
                                category: null
                            });
                        } catch (e) {}
                    });
                    
                    return events;
                }
            """)

            print(f"[AXS] Found {len(events)} events")
            return events or []

        except Exception as e:
            raise Exception(f"AXS scraper error: {e}")
        finally:
            await browser.close()
