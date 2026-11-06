"""
CRUD routes for the user's selected venues.

The venues table is the single source of truth. Ticketmaster venue discovery
remains dynamic and does not write to the database until a venue is selected.
"""
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException

from database import get_db
from models import VenueCreate, VenueUpdate, VenueResponse
from scrapers.ticketmaster_venues import search_venues, search_venues_by_region


router = APIRouter(prefix="/venues", tags=["venues"])


def _row_to_venue(row) -> dict | None:
    """Convert a database row to a venue response dictionary."""
    if row is None:
        return None

    return {
        "id": row["id"],
        "name": row["name"],
        "url": row["url"],
        "address": row["address"],
        "scraper_type": row["scraper_type"],
        "notes": row["notes"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "ticketmaster_id": row["ticketmaster_id"],
        "city_id": row["city_id"],
        "postal_code": row["postal_code"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "timezone": row["timezone"],
    }


@router.get("/", response_model=list[VenueResponse])
async def list_venues():
    """Return all venues saved by the user."""
    db = await get_db()
    async with db.execute("SELECT * FROM venues ORDER BY name") as cursor:
        rows = await cursor.fetchall()
    return [_row_to_venue(row) for row in rows]


# Backward-compatible endpoint while the frontend is being updated.
# The venues table now contains only the user's selected venues.
@router.get("/my", response_model=list[VenueResponse])
async def list_my_venues():
    """Return the user's saved venues (same collection as GET /venues/)."""
    return await list_venues()


@router.post("/", response_model=VenueResponse, status_code=201)
async def create_venue(payload: VenueCreate):
    """Save a selected or manually entered venue."""
    db = await get_db()
    venue_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    await db.execute(
        """INSERT INTO venues (
            id, name, url, address, scraper_type, notes,
            ticketmaster_id, city_id, postal_code,
            latitude, longitude, timezone,
            created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            venue_id,
            payload.name,
            payload.url,
            payload.address,
            payload.scraper_type,
            payload.notes,
            payload.ticketmaster_id,
            payload.city_id,
            payload.postal_code,
            payload.latitude,
            payload.longitude,
            payload.timezone,
            now,
            now,
        ),
    )
    await db.commit()

    async with db.execute(
        "SELECT * FROM venues WHERE id = ?", (venue_id,)
    ) as cursor:
        row = await cursor.fetchone()

    return _row_to_venue(row)


# Backward-compatible endpoint while Venues.jsx is being updated.
# Creating the venue already saves it, so this endpoint only validates the ID.
@router.post("/my/{venue_id}")
async def add_my_venue(venue_id: str):
    """Compatibility endpoint; a venue is selected when it is created."""
    db = await get_db()
    async with db.execute(
        "SELECT id FROM venues WHERE id = ?", (venue_id,)
    ) as cursor:
        venue = await cursor.fetchone()

    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    return {"message": "Venue is already saved", "venue_id": venue_id}


@router.delete("/my/{venue_id}")
async def remove_my_venue(venue_id: str):
    """Remove a saved venue."""
    db = await get_db()

    try:
        async with db.execute(
            "SELECT id FROM venues WHERE id = ?", (venue_id,)
        ) as cursor:
            venue = await cursor.fetchone()

        if not venue:
            raise HTTPException(status_code=404, detail="Venue not found")

        # Venue event results are temporary and are not stored in the database.
        await db.execute("DELETE FROM venues WHERE id = ?", (venue_id,))
        await db.commit()

        return {"message": "Venue removed", "venue_id": venue_id}

    except Exception:
        await db.rollback()
        raise


# --------------------------------------------------
# Ticketmaster geographic venue discovery (read-only)
# --------------------------------------------------

@router.get("/ticketmaster/search-by-region")
async def search_ticketmaster_venues_by_region(
    region: str,
    keyword: str | None = None,
    size: int = 100,
    page: int = 0,
):
    """
    Search Ticketmaster venues within a predefined metro region.
    Supported regions: saint_louis, chicago.
    Search results are temporary until the user selects a venue.
    """
    if region not in ("saint_louis", "chicago"):
        raise HTTPException(
            status_code=400,
            detail="Invalid region. Use saint_louis or chicago.",
        )

    if size < 1 or size > 100:
        raise HTTPException(
            status_code=400,
            detail="Size must be between 1 and 100.",
        )

    if page < 0:
        raise HTTPException(
            status_code=400,
            detail="Page cannot be negative.",
        )

    try:
        return await search_venues_by_region(
            region=region,
            keyword=keyword,
            size=size,
            page=page,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/ticketmaster/search")
async def search_ticketmaster_venues(
    city: str,
    state_code: str,
    keyword: str | None = None,
    size: int = 100,
    page: int = 0,
):
    """Search Ticketmaster venues without importing them."""
    try:
        return await search_venues(
            city=city,
            state_code=state_code,
            keyword=keyword,
            size=size,
            page=page,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/{venue_id}", response_model=VenueResponse)
async def get_venue(venue_id: str):
    """Return one saved venue."""
    db = await get_db()
    async with db.execute(
        "SELECT * FROM venues WHERE id = ?", (venue_id,)
    ) as cursor:
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Venue not found")

    return _row_to_venue(row)


@router.put("/{venue_id}", response_model=VenueResponse)
async def update_venue(venue_id: str, payload: VenueUpdate):
    """Update a saved venue."""
    db = await get_db()

    async with db.execute(
        "SELECT * FROM venues WHERE id = ?", (venue_id,)
    ) as cursor:
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Venue not found")

    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates = [f"{key} = ?" for key in update_data]
    values = list(update_data.values())
    updates.append("updated_at = ?")
    values.extend([datetime.utcnow().isoformat(), venue_id])

    await db.execute(
        f"UPDATE venues SET {', '.join(updates)} WHERE id = ?",
        values,
    )
    await db.commit()

    async with db.execute(
        "SELECT * FROM venues WHERE id = ?", (venue_id,)
    ) as cursor:
        updated_row = await cursor.fetchone()

    return _row_to_venue(updated_row)


@router.delete("/{venue_id}", status_code=204)
async def delete_venue(venue_id: str):
    """Delete a saved venue."""
    db = await get_db()

    async with db.execute(
        "SELECT id FROM venues WHERE id = ?", (venue_id,)
    ) as cursor:
        venue = await cursor.fetchone()

    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    try:
        # Venue event results are temporary and are not stored in the database.
        await db.execute("DELETE FROM venues WHERE id = ?", (venue_id,))
        await db.commit()
    except Exception:
        await db.rollback()
        raise
