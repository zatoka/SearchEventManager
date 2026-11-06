"""
Test Ticketmaster geographic venue search.
Saint Louis and Chicago - 50 mile radius.
"""

import asyncio
from scrapers.ticketmaster_venues import search_venues_by_region


async def test_region(region):

    print("\n" + "=" * 65)
    print(f"TESTING REGION: {region.upper()}")
    print("=" * 65)

    try:
        result = await search_venues_by_region(
            region=region,
            size=100,
            page=0
        )

        print(f"Region: {result['region']}")
        print(f"Radius: {result['radius_miles']} miles")
        print(f"Total Ticketmaster results: {result['total']}")
        print(f"Venues returned within radius: {result['returned']}")
        print(f"Total pages: {result['total_pages']}")

        print("\nVENUES FOUND:\n")

        for i, venue in enumerate(result["venues"], 1):

            print(f"{i}. {venue['name']}")
            print(f"   City: {venue['city']}")
            print(f"   Address: {venue['address']}")
            print(f"   Distance: {venue['distance_miles']} miles")
            print(f"   Ticketmaster ID: {venue['ticketmaster_id']}")
            print()

    except Exception as e:
        print(f"ERROR: {e}")


async def main():

    await test_region("saint_louis")
    await test_region("chicago")


if __name__ == "__main__":
    asyncio.run(main())