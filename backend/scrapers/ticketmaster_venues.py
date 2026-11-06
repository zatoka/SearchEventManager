"""
Ticketmaster Discovery API - Geographic Venue Search.
Supports Saint Louis and Chicago metropolitan areas.
"""

import aiohttp
import math
from typing import Optional

from config import get_ticketmaster_api_key, TICKETMASTER_BASE_URL


# --------------------------------------------------
# Geographic region configuration
# --------------------------------------------------

REGIONS = {
    "saint_louis": {
        "name": "Saint Louis Metro",
        "latitude": 38.6270,
        "longitude": -90.1994,
        "radius": 50,
    },
    "chicago": {
        "name": "Chicago Metro",
        "latitude": 41.8781,
        "longitude": -87.6298,
        "radius": 50,
    },
}


# --------------------------------------------------
# GeoHash encoder (no external dependency)
# --------------------------------------------------

def encode_geohash(latitude, longitude, precision=7):

    BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"

    lat_range = [-90.0, 90.0]
    lon_range = [-180.0, 180.0]

    geohash = []
    bit = 0
    ch = 0
    even = True

    while len(geohash) < precision:

        if even:
            mid = (lon_range[0] + lon_range[1]) / 2

            if longitude >= mid:
                ch |= 1 << (4 - bit)
                lon_range[0] = mid
            else:
                lon_range[1] = mid

        else:
            mid = (lat_range[0] + lat_range[1]) / 2

            if latitude >= mid:
                ch |= 1 << (4 - bit)
                lat_range[0] = mid
            else:
                lat_range[1] = mid

        even = not even

        if bit < 4:
            bit += 1
        else:
            geohash.append(BASE32[ch])
            bit = 0
            ch = 0

    return "".join(geohash)


# --------------------------------------------------
# Calculate distance between two geographic points
# --------------------------------------------------

def calculate_distance(lat1, lon1, lat2, lon2):

    earth_radius = 3958.7613

    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c


# --------------------------------------------------
# Parse Ticketmaster venue
# --------------------------------------------------

def parse_venue(venue, center):

    location = venue.get("location") or {}
    city = venue.get("city") or {}
    state = venue.get("state") or {}
    country = venue.get("country") or {}
    address_data = venue.get("address") or {}

    latitude = location.get("latitude")
    longitude = location.get("longitude")

    # Coordinates are required to verify the 50-mile boundary.
    if latitude is None or longitude is None:
        return None

    try:
        latitude = float(latitude)
        longitude = float(longitude)

        distance = calculate_distance(
            center["latitude"],
            center["longitude"],
            latitude,
            longitude
        )

    except (TypeError, ValueError):
        return None

    if distance > center["radius"]:
        return None

    address_parts = [
        address_data.get("line1"),
        address_data.get("line2")
    ]

    address = ", ".join(
        part for part in address_parts if part
    )

    return {
        "ticketmaster_id": venue.get("id"),
        "name": venue.get("name"),
        "url": venue.get("url"),
        "address": address,
        "city": city.get("name"),
        "state_code": state.get("stateCode"),
        "country_code": country.get("countryCode"),
        "postal_code": venue.get("postalCode"),
        "latitude": latitude,
        "longitude": longitude,
        "timezone": venue.get("timezone"),
        "distance_miles": round(distance, 2),
        "region": center["name"],
    }


# --------------------------------------------------
# Geographic Ticketmaster search
# --------------------------------------------------

async def search_venues_by_region(
    region: str,
    keyword: Optional[str] = None,
    size: int = 100,
    page: int = 0
):

    if region not in REGIONS:
        raise ValueError(
            f"Unknown region: {region}. "
            f"Available regions: {list(REGIONS.keys())}"
        )

    center = REGIONS[region]

    endpoint = f"{TICKETMASTER_BASE_URL}/venues.json"

    geohash = encode_geohash(
        center["latitude"],
        center["longitude"]
    )

    params = {
        "apikey": get_ticketmaster_api_key(),
        "geoPoint": geohash,
        "radius": center["radius"],
        "unit": "miles",
        "countryCode": "US",
        "size": min(size, 100),
        "page": page,
        "sort": "distance,asc",
    }

    if keyword:
        params["keyword"] = keyword

    async with aiohttp.ClientSession() as session:

        async with session.get(
            endpoint,
            params=params,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:

            if response.status != 200:
                error_text = await response.text()

                raise Exception(
                    f"Ticketmaster API error "
                    f"{response.status}: {error_text}"
                )

            data = await response.json()

    raw_venues = (
        data.get("_embedded", {})
        .get("venues", [])
    )

    venues = []

    for venue in raw_venues:

        parsed = parse_venue(venue, center)

        if parsed:
            venues.append(parsed)

    venues.sort(
        key=lambda v: v["distance_miles"]
    )

    page_info = data.get("page", {})

    return {
        "region": center["name"],
        "radius_miles": center["radius"],
        "total": page_info.get("totalElements", 0),
        "page": page_info.get("number", 0),
        "total_pages": page_info.get("totalPages", 0),
        "returned": len(venues),
        "venues": venues,
    }


# --------------------------------------------------
# Original city-based search (backward compatibility)
# --------------------------------------------------

async def search_venues(
    city: str = "Saint Louis",
    state_code: str = "MO",
    keyword: Optional[str] = None,
    size: int = 100,
    page: int = 0
):

    endpoint = f"{TICKETMASTER_BASE_URL}/venues.json"

    params = {
        "apikey": get_ticketmaster_api_key(),
        "city": city,
        "stateCode": state_code,
        "countryCode": "US",
        "size": min(size, 100),
        "page": page,
    }

    if keyword:
        params["keyword"] = keyword

    async with aiohttp.ClientSession() as session:

        async with session.get(
            endpoint,
            params=params,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:

            if response.status != 200:
                raise Exception(
                    f"Ticketmaster API error "
                    f"{response.status}: {await response.text()}"
                )

            data = await response.json()

    embedded = data.get("_embedded", {})
    raw_venues = embedded.get("venues", [])

    venues = []

    for venue in raw_venues:

        location = venue.get("location") or {}
        city_data = venue.get("city") or {}
        state_data = venue.get("state") or {}
        country_data = venue.get("country") or {}
        address_data = venue.get("address") or {}

        address = ", ".join(
            part for part in [
                address_data.get("line1"),
                address_data.get("line2")
            ] if part
        )

        venues.append({
            "ticketmaster_id": venue.get("id"),
            "name": venue.get("name"),
            "url": venue.get("url"),
            "address": address,
            "city": city_data.get("name"),
            "state_code": state_data.get("stateCode"),
            "country_code": country_data.get("countryCode"),
            "postal_code": venue.get("postalCode"),
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
            "timezone": venue.get("timezone"),
        })

    page_info = data.get("page", {})

    return {
        "total": page_info.get("totalElements", 0),
        "page": page_info.get("number", 0),
        "total_pages": page_info.get("totalPages", 0),
        "venues": venues,
    }