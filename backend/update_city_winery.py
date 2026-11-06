import asyncio
from database import get_db

async def update():
    db = await get_db()
    await db.execute("UPDATE venues SET scraper_type = 'city_winery' WHERE name LIKE '%City Winery%'")
    await db.commit()
    print("Updated City Winery scraper_type to 'city_winery'")

if __name__ == "__main__":
    asyncio.run(update())
