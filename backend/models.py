"""
Pydantic models for API request/response.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Venue ──────────────────────────────────────────────────────────────────────

class VenueCreate(BaseModel):
    name: str
    url: Optional[str] = None
    address: Optional[str] = None
    scraper_type: Optional[str] = None
    notes: Optional[str] = None

    # Geographic and Ticketmaster information
    ticketmaster_id: Optional[str] = None
    city_id: Optional[int] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None


class VenueUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    address: Optional[str] = None
    scraper_type: Optional[str] = None
    notes: Optional[str] = None

    ticketmaster_id: Optional[str] = None
    city_id: Optional[int] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None


class VenueResponse(BaseModel):
    id: str
    name: str
    url: Optional[str] = None
    address: Optional[str] = None
    scraper_type: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    ticketmaster_id: Optional[str] = None
    city_id: Optional[int] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None

# ── Event ──────────────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    venue_id: str
    title: str
    event_date: Optional[str] = None
    event_time: Optional[str] = None
    description: Optional[str] = None
    event_url: Optional[str] = None
    image_url: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    category: Optional[str] = None


class EventResponse(BaseModel):
    id: str
    venue_id: str
    venue_name: Optional[str] = None
    title: str
    event_date: Optional[str] = None
    event_time: Optional[str] = None
    description: Optional[str] = None
    event_url: Optional[str] = None
    image_url: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    category: Optional[str] = None
    fetched_at: Optional[str] = None


# ── Search ────────────────────────────────────────────────────────────────────

class SearchFilters(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    venue_id: Optional[str] = None
    category: Optional[str] = None
    search_text: Optional[str] = None
