"""
Import venues from CSV file into the database.

Usage:
    python import_venues.py                        # Uses default venues.csv
    python import_venues.py my_venues.csv          # Uses custom CSV file
    python import_venues.py --clear                # Clear existing venues first

Supported CSV formats:
    Format 1 (simple): name, url, scraper_type
    Format 2 (detailed): venue_name, venue_type, scraper, street_address, city, state, zip_code, official_website_url
                         scraper: TM = Ticketmaster API, MX = MetroTix
"""
import asyncio
import csv
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database import get_db


# MetroTix URLs for venues that use MetroTix scraper
METROTIX_URLS = {
    'jazz bistro saint louis': 'https://www.metrotix.com/events/venue/jazz-st-louis',
    'jazz st. louis': 'https://www.metrotix.com/events/venue/jazz-st-louis',
    'jazz bistro': 'https://www.metrotix.com/events/venue/jazz-st-louis',
    'the sheldon concert hall': 'https://www.metrotix.com/events/venue/sheldon-the',
    'the sheldon': 'https://www.metrotix.com/events/venue/sheldon-the',
    'sheldon': 'https://www.metrotix.com/events/venue/sheldon-the',
}


# Auto-detect scraper type based on venue name and URL
def detect_scraper_type(name: str, url: str) -> str:
    """Auto-detect scraper type based on venue name or URL."""
    url_lower = url.lower()
    name_lower = name.lower()
    
    if 'ticketmaster' in url_lower:
        return 'ticketmaster_api'
    elif 'axs.com' in url_lower:
        return 'axs'
    elif 'thefactorystl.com' in url_lower:
        return 'thefactorystl'
    elif 'familyarena.com' in url_lower:
        return 'familyarena'
    elif 'enterprisecenter.com' in url_lower or 'enterprise center' in name_lower:
        return 'ticketmaster_api'
    elif 'hollywood casino' in name_lower:
        return 'ticketmaster_api'
    elif 'stifel theatre' in name_lower or 'stifeltheatre' in url_lower:
        return 'ticketmaster_api'
    elif 'chaifetz' in name_lower:
        return 'axs'
    else:
        return 'ticketmaster_api'  # Default


def parse_scraper_type(scraper_code: str, name: str, url: str) -> tuple:
    """
    Parse scraper type from CSV code.
    
    Parameters:
        scraper_code: Code from CSV (TM, MX, CW, or empty)
        name: Venue name
        url: Venue URL
    
    Returns:
        (scraper_type, final_url)
    """
    code = scraper_code.strip().upper() if scraper_code else ''
    name_lower = name.lower()
    
    if code == 'MX':
        # MetroTix - use MetroTix URL
        metrotix_url = METROTIX_URLS.get(name_lower)
        if metrotix_url:
            return 'metrotix', metrotix_url
        else:
            print(f"[WARN] No MetroTix URL found for: {name}")
            return 'metrotix', url
    elif code == 'CW':
        # City Winery - use city_winery scraper
        return 'city_winery', url
    elif code == 'TM':
        return 'ticketmaster_api', url
    else:
        # Auto-detect
        return detect_scraper_type(name, url), url


async def import_venues(csv_file: str, clear_existing: bool = False):
    """
    Import venues from CSV file into the database.
    
    Supports multiple CSV formats:
    - Format 1: name, url, scraper_type
    - Format 2: venue_name, venue_type, street_address, city, state, zip_code, official_website_url
        
    Parameters:
        csv_file: Path to CSV file
        clear_existing: If True, delete all existing venues first
    """
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"[ERROR] File not found: {csv_file}")
        return 0, 0
    
    db = await get_db()
    
    # Clear existing venues if requested
    if clear_existing:
        print("[INFO] Clearing existing venues...")
        await db.execute("DELETE FROM venues")
        await db.commit()
    
    # Read CSV file
    venues_added = 0
    venues_skipped = 0
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
        reader = csv.DictReader(f)
        
        for row in reader:
            # Support multiple CSV formats
            # Format 1: name, url, scraper_type
            name = row.get('name', '').strip()
            url = row.get('url', '').strip()
            scraper_type = row.get('scraper_type', '').strip()
            
            # Format 2: venue_name, official_website_url, scraper
            if not name:
                name = row.get('venue_name', '').strip()
            if not url:
                url = row.get('official_website_url', '').strip()
            # Get scraper from CSV (TM, MX, or empty)
            scraper_code = row.get('scraper', '').strip() or row.get('sraper', '').strip()  # Handle typo too
            
            # Skip empty rows
            if not name:
                print(f"[SKIP] Missing name in row: {row}")
                venues_skipped += 1
                continue
            
            # Parse scraper type and get correct URL for MetroTix venues
            scraper_type, final_url = parse_scraper_type(scraper_code, name, url)
            
            # Check if venue already exists
            async with db.execute(
                "SELECT id FROM venues WHERE name = ?", (name,)
            ) as cursor:
                existing = await cursor.fetchone()
            
            if existing:
                print(f"[SKIP] Venue already exists: {name}")
                venues_skipped += 1
                continue
            
            # Insert venue
            import uuid
            venue_id = str(uuid.uuid4())
            
            await db.execute(
                "INSERT INTO venues (id, name, url, scraper_type) VALUES (?, ?, ?, ?)",
                (venue_id, name, final_url, scraper_type)
            )
            
            print(f"[ADD] {name} ({scraper_type}) -> {final_url}")
            venues_added += 1
    
    await db.commit()
    
    return venues_added, venues_skipped


async def main():
    """Main entry point."""
    # Default CSV file
    csv_file = "venues.csv"
    clear_existing = False
    
    # Parse arguments
    args = sys.argv[1:]
    
    for arg in args:
        if arg == '--clear':
            clear_existing = True
        elif arg.endswith('.csv'):
            csv_file = arg
        elif arg in ['-h', '--help']:
            print(__doc__)
            return
    
    print("=" * 60)
    print("VENUE IMPORT UTILITY")
    print("=" * 60)
    print(f"CSV File: {csv_file}")
    print(f"Clear Existing: {clear_existing}")
    print()
    
    # Check for default file or template
    if not os.path.exists(csv_file):
        template_file = "venues_template.csv"
        if os.path.exists(template_file):
            print(f"[INFO] {csv_file} not found, using template: {template_file}")
            csv_file = template_file
        else:
            print(f"[ERROR] CSV file not found: {csv_file}")
            print(f"[INFO] Create a CSV file with format:")
            print("       name,url,scraper_type")
            print("       Busch Stadium,https://...,ticketmaster_api")
            return
    
    # Import venues
    added, skipped = await import_venues(csv_file, clear_existing)
    
    print()
    print("=" * 60)
    print(f"IMPORT COMPLETE")
    print(f"  Venues Added:   {added}")
    print(f"  Venues Skipped: {skipped}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
