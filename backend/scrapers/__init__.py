# Scrapers package
#
# Every scraper_type saved in the venues table maps to a function here.
# Nothing is removed: legacy browser-based types keep working for any venue
# that still uses them, but new venues should use a NO-BROWSER type.
from .ticketmaster import scrape_ticketmaster
from .ticketmaster_api import (
    search_events,
    get_venue_events,
    get_event_by_id,
    scrape_ticketmaster_api,
    DAYS_OF_WEEK,
    DAYS_ABBREVIATED,
    CLASSIFICATION_LIST
)
from .axs import scrape_axs
from .familyarena import scrape_familyarena
from .thefactorystl import scrape_thefactorystl
from .metrotix import scrape_metrotix, scrape_jazz_st_louis
from .city_winery import scrape_city_winery_st_louis
from .city_winery_feed import scrape_city_winery as scrape_city_winery_feed
from .metrotix_html import scrape_metrotix_html

SCRAPER_MAP = {
    # ── No browser (recommended) ──────────────────────────────────────────
    # "ticketmaster" uses the Ticketmaster API when the venue has a
    # ticketmaster_id (routes/events.py); the web-page fallback needs a browser.
    "ticketmaster": scrape_ticketmaster,
    "city_winery_feed": scrape_city_winery_feed,      # iCal/RSS feeds (St. Louis + Chicago)
    "metrotix_html": scrape_metrotix_html,            # MetroTix venue page + Load More

    # ── Legacy: need the Playwright browser (kept for existing records) ──
    "axs": scrape_axs,
    "familyarena": scrape_familyarena,
    "thefactorystl": scrape_thefactorystl,
    "metrotix": scrape_metrotix,
    "jazzstl": scrape_jazz_st_louis,
    "city_winery": scrape_city_winery_st_louis,

    # ── Legacy: Ticketmaster region keyword search (not venue-specific) ──
    "ticketmaster_api": scrape_ticketmaster_api,
}

# Venue-page/feed scrapers that take the saved venue URL and need no browser.
# routes/events.py uses these for venue search and "My Venues Only".
URL_SCRAPERS = {"city_winery_feed", "metrotix_html"}

# Types that never launch a browser (ticketmaster: when ticketmaster_id is set).
NO_BROWSER_SCRAPERS = {"ticketmaster"} | URL_SCRAPERS

LEGACY_BROWSER_SCRAPERS = {
    "axs", "familyarena", "thefactorystl", "metrotix", "jazzstl", "city_winery",
}
