# Scrapers package
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

SCRAPER_MAP = {
    "ticketmaster": scrape_ticketmaster,
    "ticketmaster_api": scrape_ticketmaster_api,
    "axs": scrape_axs,
    "familyarena": scrape_familyarena,
    "thefactorystl": scrape_thefactorystl,
    "metrotix": scrape_metrotix,
    "jazzstl": scrape_jazz_st_louis,
    "city_winery": scrape_city_winery_st_louis,
}
