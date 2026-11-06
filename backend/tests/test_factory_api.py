"""
Test The Factory STL REST API.
"""
import urllib.request
import json

# Try the WordPress REST API endpoint
url = 'https://thefactorystl.com/wp-json/wp/v2/event?per_page=5'
with urllib.request.urlopen(url) as response:
    data = json.loads(response.read().decode())

print(f'Got {len(data)} events from API')
if data:
    # Print first event structure
    event = data[0]
    print('First event:')
    title = event.get('title', {}).get('rendered', 'N/A')
    print(f'  Title: {title}')
    print(f'  Link: {event.get("link", "N/A")}')
    
    # Check for ACF or custom fields
    if 'acf' in event:
        print(f'  ACF fields: {list(event["acf"].keys())[:10]}')
    
    # Print all keys
    print(f'\nAll keys: {list(event.keys())}')
    
    # Check for date fields
    print('\nLooking for date fields...')
    for key in event.keys():
        if 'date' in key.lower() or 'time' in key.lower() or 'event' in key.lower():
            print(f'  {key}: {str(event[key])[:100]}')
