#!/usr/bin/env python3
"""
Resolve unknown food entries to a specific food.
Usage:
    nutrition-unknown <entry_id> <food_key>
    nutrition-unknown 20260118000401kiqz arabic_flatbread
    
    # Resolve multiple at once:
    nutrition-unknown 20260118000401kiqz,20260118123321luzw,20260118125936wr6x arabic_flatbread
"""
import os
import sys
import json
import argparse

CONFIG_DIR = os.path.expanduser('~/.nutrition-pad')
SERVER_CONFIG_FILE = os.path.join(CONFIG_DIR, 'notes.config')

def load_server_config():
    """Load server configuration"""
    if not os.path.exists(SERVER_CONFIG_FILE):
        return {'server': 'localhost:5000'}
    try:
        with open(SERVER_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'server': 'localhost:5000'}

def post_to_server(server, endpoint, data):
    """Post data to server"""
    try:
        import urllib.request
        url = f"http://{server}{endpoint}"
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=json_data,
                                     headers={'Content-Type': 'application/json'},
                                     method='POST')
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.load(response)
    except Exception as e:
        print(f"Error communicating with server: {e}", file=sys.stderr)
        return None

def fetch_food_from_server(server, food_key):
    """Fetch food data from server by ID"""
    try:
        import urllib.request
        url = f"http://{server}/api/foods/by-id/{food_key}"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.load(response)
            if data.get('food'):
                return data.get('food')
    except Exception as e:
        pass
    return None

def main():
    parser = argparse.ArgumentParser(
        description='Resolve unknown food entries',
        epilog='Server configured with: nutrition-client set-server HOST:PORT'
    )
    parser.add_argument('entry_ids', help='Entry ID(s) to resolve (comma-separated)')
    parser.add_argument('food_key', help='Food key to resolve to')
    
    args = parser.parse_args()
    
    entry_ids = args.entry_ids.split(',')
    food_key = args.food_key
    
    # Load server config
    server_config = load_server_config()
    server = server_config.get('server', 'localhost:5000')
    
    # Verify the food exists
    print(f"Connecting to server: {server}")
    food_data = fetch_food_from_server(server, food_key)
    
    if not food_data:
        print(f"❌ Food '{food_key}' not found on server", file=sys.stderr)
        print(f"\nTry: nutrition-food search {food_key}", file=sys.stderr)
        return 1
    
    food_name = food_data.get('name', food_key)
    print(f"Resolving to: {food_name}")
    
    # Send resolve request
    result = post_to_server(server, '/api/resolve-unknown', {
        'entry_ids': entry_ids,
        'food_key': food_key
    })
    
    if result is None:
        print(f"\n❌ Failed to communicate with server: {server}", file=sys.stderr)
        print(f"   Make sure the server is running", file=sys.stderr)
        print(f"   Check config: nutrition-client show", file=sys.stderr)
        return 1
    
    if not result.get('success'):
        print(f"❌ {result.get('error', 'Unknown error')}", file=sys.stderr)
        return 1
    
    # Show results
    updated_count = result.get('updated_count', 0)
    total_requested = result.get('total_requested', len(entry_ids))
    
    if result.get('updated_entries'):
        for entry_info in result['updated_entries']:
            print(f"  ✓ {entry_info['calories']} cal, {entry_info['protein']}g protein")
    
    print(f"Updated {updated_count}/{total_requested} entries")
    
    if updated_count < total_requested:
        missing = total_requested - updated_count
        print(f"⚠️  {missing} entry/entries not found in server logs", file=sys.stderr)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())