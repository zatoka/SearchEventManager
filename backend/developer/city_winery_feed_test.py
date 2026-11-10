"""
City Winery feed test: download the events page source, find the feed links
it advertises, download the feeds, and run the parser.

Usage (from the backend folder, Git Bash):
    ./venv/Scripts/python.exe developer/city_winery_feed_test.py            # St. Louis
    ./venv/Scripts/python.exe developer/city_winery_feed_test.py chicago
    ./venv/Scripts/python.exe developer/city_winery_feed_test.py all

Raw downloads (page HTML, iCal, RSS) and the parsed JSON are saved in
developer/results/ for review. Read-only: nothing is written to the database.
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import aiohttp

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from scrapers.city_winery_feed import (  # noqa: E402
    CITIES, REQUEST_HEADERS, _download, _ssl_context, discover_feed_urls,
    feed_urls, merge_events, parse_ics, parse_rss,
)

RESULTS = HERE / "results"


async def run_city(session, city_key: str) -> list:
    info = CITIES[city_key]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"\n=== {info['venue_name']} ===")

    # 1) Page source -> feed links
    page = await _download(session, info["page_url"])
    (RESULTS / f"citywinery-{city_key}-page-{stamp}.html").write_text(page, encoding="utf-8")
    links = discover_feed_urls(page)
    print(f"Page source: {len(page):,} chars | feed links found: {sorted(links)}")
    if not {"ics", "rss"} <= set(links):
        print("  Feed links not found in page; using known feed URLs.")
        links = {**feed_urls(city_key), **links}
    for kind, url in sorted(links.items()):
        print(f"  {kind}: {url}")

    # 2) Download feeds
    ics_text = await _download(session, links["ics"])
    rss_text = await _download(session, links["rss"])
    (RESULTS / f"citywinery-{city_key}-events-{stamp}.ics").write_text(ics_text, encoding="utf-8")
    (RESULTS / f"citywinery-{city_key}-rss-{stamp}.xml").write_text(rss_text, encoding="utf-8")

    # 3) Parse + merge
    ics_events = parse_ics(ics_text)
    rss_items = parse_rss(rss_text)
    events = merge_events(ics_events, rss_items, info["venue_name"])
    matched = len(set(ics_events) & set(rss_items))
    print(f"Parsed: iCal {len(ics_events)} | RSS {len(rss_items)} | matched by id {matched} | merged {len(events)}")

    out_file = RESULTS / f"citywinery-{city_key}-parsed-{stamp}.json"
    out_file.write_text(json.dumps(events, indent=2), encoding="utf-8")

    # 4) Quality summary
    def count(field):
        return sum(1 for e in events if e.get(field))
    print(f"Fields present: date {count('event_date')} | time {count('event_time')} | "
          f"image {count('image_url')} | category {count('category')} | ticket link {count('event_url')}")
    if events:
        print(f"Date range: {events[0]['event_date']} -> {events[-1]['event_date']}")
    statuses = {}
    for e in events:
        statuses[e.get("status")] = statuses.get(e.get("status"), 0) + 1
    print(f"Status: {statuses}")

    print("\nFirst 10 events:")
    for e in events[:10]:
        print(f"  {e['event_date']} {e['event_time'] or '--:--'} ({(e['day_of_week'] or '')[:3]}) | "
              f"{e['title'][:60]:<60} | {e['category'] or '-'}")
    print(f"\nParsed JSON saved: {out_file}")
    return events


async def main():
    arg = (sys.argv[1] if len(sys.argv) > 1 else "st_louis").lower().replace("-", "_").replace(" ", "_")
    keys = list(CITIES) if arg == "all" else ["chicago" if "chicago" in arg else "st_louis"]
    RESULTS.mkdir(exist_ok=True)

    connector = aiohttp.TCPConnector(ssl=_ssl_context())
    async with aiohttp.ClientSession(connector=connector, headers=REQUEST_HEADERS) as session:
        for key in keys:
            try:
                await run_city(session, key)
            except Exception as e:
                print(f"ERROR ({key}): {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
