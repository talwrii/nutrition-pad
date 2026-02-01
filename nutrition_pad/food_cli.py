#!/usr/bin/env python3
"""
Command-line tool to manage foods in nutrition-pad.
Can work with local config or remote server.
"""
import os
import sys
import json
import argparse
import toml

CONFIG_FILE = 'foods.toml'
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

def load_local_config():
    """Load local foods.toml"""
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} not found", file=sys.stderr)
        return None

    try:
        with open(CONFIG_FILE, 'r') as f:
            return toml.load(f)
    except Exception as e:
        print(f"Error loading {CONFIG_FILE}: {e}", file=sys.stderr)
        return None

def get_all_foods_from_config(config):
    """Extract all foods from config structure"""
    foods = []

    for pad_key, pad_data in config.get('pads', {}).items():
        if pad_key == 'amounts':
            continue

        pad_name = pad_data.get('name', pad_key)

        for food_key, food in pad_data.get('foods', {}).items():
            food_entry = {
                'pad_key': pad_key,
                'pad_name': pad_name,
                'food_key': food_key,
                'name': food.get('name', food_key),
                'type': food.get('type', 'amount'),
                '_raw': food  # Keep original for --raw output
            }

            if food.get('type') == 'unit':
                food_entry['calories'] = food.get('calories', 0)
                food_entry['protein'] = food.get('protein', 0)
            else:
                food_entry['calories_per_gram'] = food.get('calories_per_gram', 0)
                food_entry['protein_per_gram'] = food.get('protein_per_gram', 0)

            foods.append(food_entry)

    return foods

def find_food_by_id(foods, food_id):
    """Find a food by its ID (food_key), returns (food_entry, pad_key) or (None, None)"""
    for food in foods:
        if food['food_key'] == food_id:
            return food, food['pad_key']
    return None, None

def cmd_search(args):
    """Search for foods"""
    query = args.query.lower()

    if args.local:
        config = load_local_config()
        if not config:
            return 1

        foods = get_all_foods_from_config(config)
    else:
        server_config = load_server_config()
        server = server_config.get('server', 'localhost:5000')

        data = fetch_from_server(server, f'/api/foods/search?q={query}')
        if data is None:
            print("\nUse --local to search local files instead", file=sys.stderr)
            return 1

        foods = data.get('foods', [])

    # Filter by query
    matches = [f for f in foods if query in f['name'].lower() or query in f['food_key'].lower()]

    if not matches:
        print(f"No foods found matching: {query}")
        return 0

    print(f"\nFound {len(matches)} food(s):\n")
    for food in matches:
        print(f"  {food['pad_name']} / {food['name']}")
        print(f"    Key: {food['pad_key']}/{food['food_key']}")
        print(f"    Type: {food['type']}")

        if food['type'] == 'unit':
            print(f"    Nutrition: {food.get('calories', 0)} cal, {food.get('protein', 0)}g protein per unit")
        else:
            print(f"    Nutrition: {food.get('calories_per_gram', 0)} cal/g, {food.get('protein_per_gram', 0)}g protein/g")

        print()

    return 0

def cmd_list(args):
    """List all foods"""
    if args.local:
        config = load_local_config()
        if not config:
            return 1

        foods = get_all_foods_from_config(config)
    else:
        server_config = load_server_config()
        server = server_config.get('server', 'localhost:5000')

        data = fetch_from_server(server, '/api/foods')
        if data is None:
            print("\nUse --local to list local files instead", file=sys.stderr)
            return 1

        foods = data.get('foods', [])

    # Group by pad
    pads = {}
    for food in foods:
        pad_name = food['pad_name']
        if pad_name not in pads:
            pads[pad_name] = []
        pads[pad_name].append(food)

    print(f"\nTotal: {len(foods)} food(s) in {len(pads)} pad(s)\n")

    for pad_name in sorted(pads.keys()):
        print(f"[{pad_name}]")
        pad_foods = sorted(pads[pad_name], key=lambda f: f['name'])
        
        # Calculate max widths for alignment
        max_name = max(len(f['name']) for f in pad_foods)
        
        for food in pad_foods:
            type_str = "U" if food['type'] == 'unit' else "A"
            name = food['name']
            food_id = food['food_key']
            # Pad name to align IDs
            print(f"  [{type_str}] {name:<{max_name}}  {food_id}")

    return 0

def cmd_get(args):
    """Get specific food details"""
    food_id = args.food_id
    
    # Support both "food_id" and "pad_key/food_key" formats
    if '/' in food_id:
        parts = food_id.split('/')
        if len(parts) != 2:
            print("Error: Path must be in format: pad_key/food_key or just food_key", file=sys.stderr)
            return 1
        pad_key, food_id = parts
    else:
        pad_key = None

    if args.local:
        config = load_local_config()
        if not config:
            return 1

        if pad_key:
            # Direct lookup
            pad = config.get('pads', {}).get(pad_key)
            if not pad:
                print(f"Error: Pad '{pad_key}' not found", file=sys.stderr)
                return 1

            food = pad.get('foods', {}).get(food_id)
            if not food:
                print(f"Error: Food '{food_id}' not found in pad '{pad_key}'", file=sys.stderr)
                return 1
        else:
            # Search all pads for food_id
            foods = get_all_foods_from_config(config)
            food_entry, pad_key = find_food_by_id(foods, food_id)
            
            if not food_entry:
                print(f"Error: Food '{food_id}' not found", file=sys.stderr)
                return 1
            
            food = food_entry.get('_raw', food_entry)
    else:
        server_config = load_server_config()
        server = server_config.get('server', 'localhost:5000')

        if pad_key:
            data = fetch_from_server(server, f'/api/foods/{pad_key}/{food_id}')
        else:
            data = fetch_from_server(server, f'/api/foods/by-id/{food_id}')
        
        if data is None:
            print("\nUse --local to get from local files instead", file=sys.stderr)
            return 1

        food = data.get('food')
        pad_key = data.get('pad_key', pad_key)
        
        if not food:
            print(f"Error: Food not found", file=sys.stderr)
            return 1

    # Output
    if args.raw:
        # Raw TOML output
        print(f"[pads.{pad_key}.foods.{food_id}]")
        for k, v in food.items():
            if k.startswith('_'):
                continue
            if isinstance(v, str):
                print(f'{k} = "{v}"')
            elif isinstance(v, float):
                # Avoid unnecessary decimals
                if v == int(v):
                    print(f'{k} = {int(v)}')
                else:
                    print(f'{k} = {v}')
            else:
                print(f'{k} = {v}')
    else:
        # Human readable
        print(f"\n{food.get('name', food_id)}")
        print(f"  ID:   {food_id}")
        print(f"  Pad:  {pad_key}")
        print(f"  Type: {food.get('type', 'amount')}")

        if food.get('type') == 'unit':
            print(f"  Calories: {food.get('calories', 0)} per unit")
            print(f"  Protein:  {food.get('protein', 0)}g per unit")
        else:
            print(f"  Calories: {food.get('calories_per_gram', 0)} per gram")
            print(f"  Protein:  {food.get('protein_per_gram', 0)}g per gram")

        if food.get('scale') and food.get('scale') != 1.0:
            print(f"  Scale: {food.get('scale')}")
        print()

    return 0

def cmd_deactivate(args):
    """Deactivate a food (hide from button grid)"""
    food_id = args.food_id

    if '/' in food_id:
        parts = food_id.split('/')
        if len(parts) != 2:
            print("Error: Path must be in format: pad_key/food_key or just food_key", file=sys.stderr)
            return 1
        pad_key, food_id = parts
    else:
        pad_key = None

    if args.local:
        config = load_local_config()
        if not config:
            return 1

        # Find the food
        if pad_key:
            pad = config.get('pads', {}).get(pad_key)
            if not pad or food_id not in pad.get('foods', {}):
                print(f"Error: Food '{pad_key}/{food_id}' not found", file=sys.stderr)
                return 1
        else:
            for pk, pd in config.get('pads', {}).items():
                if pk == 'amounts':
                    continue
                if food_id in pd.get('foods', {}):
                    pad_key = pk
                    break
            if not pad_key:
                print(f"Error: Food '{food_id}' not found", file=sys.stderr)
                return 1

        food_name = config['pads'][pad_key]['foods'][food_id].get('name', food_id)
        config['pads'][pad_key]['foods'][food_id]['active'] = False

        with open(CONFIG_FILE, 'w') as f:
            toml.dump(config, f)

        print(f"Deactivated: {food_name} ({pad_key}/{food_id})")
        return 0

    server_config = load_server_config()
    server = server_config.get('server', 'localhost:5000')

    data = {'food_key': food_id}
    if pad_key:
        data['pad_key'] = pad_key

    result = post_to_server(server, '/api/foods/deactivate', data)

    if result is None:
        return 1

    if result.get('success'):
        print(f"Deactivated: {result.get('name', food_id)} ({result.get('pad_key')}/{food_id})")
        return 0
    else:
        print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        return 1


def cmd_raw(args):
    """Dump the complete foods.toml file"""
    if args.local:
        if not os.path.exists(CONFIG_FILE):
            print(f"Error: {CONFIG_FILE} not found", file=sys.stderr)
            return 1
        with open(CONFIG_FILE, 'r') as f:
            print(f.read(), end='')
        return 0

    server_config = load_server_config()
    server = server_config.get('server', 'localhost:5000')

    try:
        import urllib.request
        url = f"http://{server}/api/foods/raw"
        with urllib.request.urlopen(url, timeout=10) as response:
            print(response.read().decode('utf-8'), end='')
        return 0
    except Exception as e:
        print(f"Error fetching from server: {e}", file=sys.stderr)
        print("\nUse --local to read local files instead", file=sys.stderr)
        return 1


def cmd_add(args):
    """Add food from stdin TOML"""
    # Read TOML from stdin
    print("Enter TOML configuration (Ctrl+D when done):", file=sys.stderr)
    toml_content = sys.stdin.read()

    if not toml_content.strip():
        print("Error: No TOML content provided", file=sys.stderr)
        return 1

    # Parse TOML
    try:
        parsed = toml.loads(toml_content)
    except Exception as e:
        print(f"Error parsing TOML: {e}", file=sys.stderr)
        return 1

    if args.local:
        print("Error: --local mode not supported for add (would overwrite entire config)", file=sys.stderr)
        print("Use the server to add foods safely", file=sys.stderr)
        return 1

    # Send to server
    server_config = load_server_config()
    server = server_config.get('server', 'localhost:5000')

    result = post_to_server(server, '/api/foods', {'toml_content': toml_content})

    if result is None:
        return 1

    if result.get('success'):
        print(f"✅ Food added successfully!")
        if result.get('pad_key') and result.get('food_key'):
            print(f"   Path: {result['pad_key']}/{result['food_key']}")
        return 0
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        return 1

def main():
    parser = argparse.ArgumentParser(description='Manage nutrition-pad foods')
    parser.add_argument('--local', action='store_true', help='Use local files instead of server')

    subparsers = parser.add_subparsers(dest='command', help='Command')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search for foods')
    search_parser.add_argument('query', help='Search query')

    # List command
    list_parser = subparsers.add_parser('list', help='List all foods')

    # Get command
    get_parser = subparsers.add_parser('get', help='Get specific food')
    get_parser.add_argument('food_id', help='Food ID (or pad_key/food_key)')
    get_parser.add_argument('--raw', action='store_true', help='Output as raw TOML')

    # Deactivate command
    deactivate_parser = subparsers.add_parser('deactivate', help='Deactivate a food')
    deactivate_parser.add_argument('food_id', help='Food ID (or pad_key/food_key)')

    # Raw command
    raw_parser = subparsers.add_parser('raw', help='Dump complete foods.toml')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add food from stdin TOML')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == 'search':
        return cmd_search(args)
    elif args.command == 'list':
        return cmd_list(args)
    elif args.command == 'get':
        return cmd_get(args)
    elif args.command == 'deactivate':
        return cmd_deactivate(args)
    elif args.command == 'raw':
        return cmd_raw(args)
    elif args.command == 'add':
        return cmd_add(args)
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())