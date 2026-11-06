import asyncio
from database import get_db


async def main():
    db = await get_db()

    print("\n--- SAVED MY EVENTS ---\n")

    async with db.execute("""
        SELECT title, event_date, event_time
        FROM my_events
        ORDER BY event_date
        LIMIT 15
    """) as cursor:
        rows = await cursor.fetchall()

    if not rows:
        print("No saved events found.")
    else:
        for row in rows:
            print(dict(row))

    print(f"\nTotal events displayed: {len(rows)}")

    await db.close()


if __name__ == "__main__":
    asyncio.run(main())

