"""
Geographic region, county, and city API.
"""

from fastapi import APIRouter
from database import get_db

router = APIRouter(prefix="/regions", tags=["regions"])


@router.get("/")
async def list_regions():
    """Return regions with their counties and cities."""

    db = await get_db()

    async with db.execute("""
        SELECT
            r.id AS region_id,
            r.name AS region_name,
            r.country_code,
            c.id AS city_id,
            c.name AS city_name,
            c.state_code,
            c.county
        FROM regions r
        LEFT JOIN cities c ON c.region_id = r.id
        ORDER BY r.name, c.county, c.name
    """) as cursor:
        rows = await cursor.fetchall()

    regions = {}

    for row in rows:
        region_id = row["region_id"]

        if region_id not in regions:
            regions[region_id] = {
                "id": region_id,
                "name": row["region_name"],
                "country_code": row["country_code"],
                "counties": {}
            }

        if row["city_id"] is not None:
            county = row["county"] or "Unassigned"

            if county not in regions[region_id]["counties"]:
                regions[region_id]["counties"][county] = []

            regions[region_id]["counties"][county].append({
                "id": row["city_id"],
                "name": row["city_name"],
                "state_code": row["state_code"]
            })

    result = []

    for region in regions.values():
        region["counties"] = [
            {
                "name": county,
                "cities": cities
            }
            for county, cities in region["counties"].items()
        ]
        result.append(region)

    return result
