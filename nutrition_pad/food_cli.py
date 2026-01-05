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
                'type': food.get('type', 'amount')
            }
            
            if food.get('type') == 'unit':
                food_entry['calories'] = food.get('calories', 0)
                food_entry['protein'] = food.get('protein', 0)
            else:
                food_entry['calories_per_gram'] = food.get('calories_per_gram', 0)
                food_entry['protein_per_gram'] = food.get('protein_per_gram', 0)
            
            foods.append(food_entry)
    
    return foods

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
        for food in sorted(pads[pad_name], key=lambda f: f['name']):
            type_str = "U" if food['type'] == 'unit' else "A"
            print(f"  [{type_str}] {food['name']} ({food['food_key']})")
        print()
    
    return 0

def cmd_get(args):
    """Get specific food details"""
    parts = args.path.split('/')
    if len(parts) != 2:
        print("Error: Path must be in format: pad_key/food_key", file=sys.stderr)
        return 1
    
    pad_key, food_key = parts
    
    if args.local:
        config = load_local_config()
        if not config:
            return 1
        
        pad = config.get('pads', {}).get(pad_key)
        if not pad:
            print(f"Error: Pad '{pad_key}' not found", file=sys.stderr)
            return 1
        
        food = pad.get('foods', {}).get(food_key)
        if not food:
            print(f"Error: Food '{food_key}' not found in pad '{pad_key}'", file=sys.stderr)
            return 1
    else:
        server_config = load_server_config()
        server = server_config.get('server', 'localhost:5000')
        
        data = fetch_from_server(server, f'/api/foods/{pad_key}/{food_key}')
        if data is None:
            print("\nUse --local to get from local files instead", file=sys.stderr)
            return 1
        
        food = data.get('food')
        if not food:
            print(f"Error: Food not found", file=sys.stderr)
            return 1
    
    # Display as TOML
    print(f"[pads.{pad_key}.foods.{food_key}]")
    print(f'name = "{food.get("name", food_key)}"')
    print(f'type = "{food.get("type", "amount")}"')
    
    if food.get('type') == 'unit':
        print(f'calories = {food.get("calories", 0)}')
        print(f'protein = {food.get("protein", 0)}')
    else:
        print(f'calories_per_gram = {food.get("calories_per_gram", 0)}')
        print(f'protein_per_gram = {food.get("protein_per_gram", 0)}')
    
    if food.get('scale') and food.get('scale') != 1.0:
        print(f'scale = {food.get("scale")}')
    
    return 0

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
    get_parser.add_argument('path', help='Food path: pad_key/food_key')
    
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
    elif args.command == 'add':
        return cmd_add(args)
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())