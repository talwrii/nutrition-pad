#!/usr/bin/env python3
"""
Record food entries via command line.

Usage:
    nutrition-record <food_key>              # Record 1 unit or default amount
    nutrition-record <food_key> <count>      # Record N units (for unit foods)
    nutrition-record <food_key> <amount>     # Record N grams (for amount foods)
    nutrition-record --at 2026-02-08T12:30 <food_key>  # Backdate entry

Examples:
    nutrition-record celery                  # 1 celery stick
    nutrition-record celery 5                # 5 celery sticks
    nutrition-record chicken_breast 150      # 150g chicken breast
    nutrition-record --at 2026-02-08T18:00 kfc-mini-fillet  # Backdated
"""
import os
import sys
import json
import argparse
import random
import string

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

def fetch_from_server(server, endpoint):
    """Fetch data from server"""
    try:
        import urllib.request
        url = f"http://{server}{endpoint}"
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.load(response)
    except Exception as e:
        print(f"Error fetching from server: {e}", file=sys.stderr)
        return None

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
        print(f"Error posting to server: {e}", file=sys.stderr)
        return None

def generate_nonce():
    """Generate a random nonce for the request"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def main():
    parser = argparse.ArgumentParser(
        description='Record food entry',
        epilog='Server configured with: nutrition-client set-server HOST:PORT'
    )
    parser.add_argument('food_key', help='Food key to record')
    parser.add_argument('count', nargs='?', type=int, default=1,
                       help='Count (for unit foods) or amount in grams (for amount foods)')
    parser.add_argument('--at', dest='at_timestamp', metavar='TIMESTAMP',
                       help='Backdate entry (format: YYYY-MM-DDTHH:MM, e.g. 2026-02-08T12:30)')

    args = parser.parse_args()

    food_key = args.food_key
    count = args.count
    at_timestamp = args.at_timestamp

    # Load server config
    server_config = load_server_config()
    server = server_config.get('server', 'localhost:5000')

    print(f"Connecting to server: {server}")

    # Look up the food to get pad_key
    result = fetch_from_server(server, f'/api/foods/by-id/{food_key}')

    if not result or 'food' not in result:
        print(f"❌ Food '{food_key}' not found on server", file=sys.stderr)
        print(f"\nTry: nutrition-food search {food_key}", file=sys.stderr)
        return 1

    food_data = result['food']
    pad_key = result['pad_key']
    food_name = food_data.get('name', food_key)
    food_type = food_data.get('type', 'amount')

    # Record entries (one at a time for proper logging)
    total_calories = 0
    total_protein = 0

    for i in range(count):
        nonce = generate_nonce()

        payload = {
            'pad': pad_key,
            'food': food_key,
            'nonce': nonce
        }
        if at_timestamp:
            payload['at'] = at_timestamp

        log_result = post_to_server(server, '/log', payload)

        if log_result is None or log_result.get('status') != 'success':
            print(f"❌ Failed to record entry {i+1}/{count}", file=sys.stderr)
            return 1

    # Calculate totals for display
    if food_type == 'unit':
        calories_per = food_data.get('calories', 0)
        protein_per = food_data.get('protein', 0)
        total_calories = calories_per * count
        total_protein = protein_per * count
        amount_str = f"{count} unit{'s' if count > 1 else ''}"
    else:
        calories_per_gram = food_data.get('calories_per_gram', 0)
        protein_per_gram = food_data.get('protein_per_gram', 0)
        total_calories = calories_per_gram * count
        total_protein = protein_per_gram * count
        amount_str = f"{count}g"

    if at_timestamp:
        print(f"✅ Recorded {count}x {food_name} at {at_timestamp}")
    else:
        print(f"✅ Recorded {count}x {food_name}")
    print(f"   {amount_str}: {total_calories:.0f} cal, {total_protein:.1f}g protein")

    return 0

if __name__ == '__main__':
    sys.exit(main())
