#!/usr/bin/env python3
"""
Command-line tool to manage foods in nutrition-pad.
Works with the nutrition-pad server via API.
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

def fetch_text_from_server(server, endpoint):
    """Fetch text data from server"""
    try:
        import urllib.request

        url = f"http://{server}{endpoint}"
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.read().decode('utf-8')
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

def get_server():
    """Get server address from config"""
    server_config = load_server_config()
    return server_config.get('server', 'localhost:5000')

def cmd_search(args):
    """Search for foods"""
    query = args.query.lower()
    server = get_server()

    data = fetch_from_server(server, f'/api/foods/search?q={query}')
    if data is None:
        return 1

    foods = data.get('foods', [])
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
    server = get_server()

    data = fetch_from_server(server, '/api/foods')
    if data is None:
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

    server = get_server()

    if pad_key:
        data = fetch_from_server(server, f'/api/foods/{pad_key}/{food_id}')
    else:
        data = fetch_from_server(server, f'/api/foods/by-id/{food_id}')

    if data is None:
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

        known_keys = {'name', 'display_name', 'type', 'calories', 'protein', 'fiber',
                       'calories_per_gram', 'protein_per_gram', 'fiber_per_gram',
                       'scale', 'pad', 'active', '_pad_key', '_food_key'}
        extra = {k: v for k, v in food.items() if k not in known_keys}
        for k, v in extra.items():
            print(f"  {k}: {v}")
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

    server = get_server()

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
    server = get_server()

    text = fetch_text_from_server(server, '/api/foods/raw')
    if text is None:
        return 1

    print(text, end='')
    return 0


def cmd_replace(args):
    """Replace a food entry by piping in new TOML"""
    print("Enter TOML configuration (Ctrl+D when done):", file=sys.stderr)
    toml_content = sys.stdin.read()

    if not toml_content.strip():
        print("Error: No TOML content provided", file=sys.stderr)
        return 1

    try:
        import toml
        parsed = toml.loads(toml_content)
    except Exception as e:
        print(f"Error parsing TOML: {e}", file=sys.stderr)
        return 1

    # Extract pad_key and food_key from the TOML path
    pads = parsed.get('pads', {})
    if not pads:
        print("Error: TOML must have [pads.<pad>.foods.<food>] structure", file=sys.stderr)
        return 1

    pad_key = list(pads.keys())[0]
    foods = pads[pad_key].get('foods', {})
    if not foods:
        print(f"Error: No foods found under pads.{pad_key}", file=sys.stderr)
        return 1

    food_key = list(foods.keys())[0]
    new_food = foods[food_key]

    # Fetch current config
    server = get_server()
    text = fetch_text_from_server(server, '/api/foods/raw')
    if text is None:
        return 1

    try:
        import toml
        config = toml.loads(text)
    except Exception as e:
        print(f"Error parsing server config: {e}", file=sys.stderr)
        return 1

    # Check food exists
    if pad_key not in config.get('pads', {}) or food_key not in config['pads'][pad_key].get('foods', {}):
        print(f"Error: {pad_key}/{food_key} not found on server", file=sys.stderr)
        return 1

    # Replace
    config['pads'][pad_key]['foods'][food_key] = new_food

    # Push back
    new_content = toml.dumps(config)
    result = post_to_server(server, '/edit-foods', {'content': new_content})
    if result is None:
        return 1

    if result.get('success'):
        print(f"Replaced: {new_food.get('name', food_key)} ({pad_key}/{food_key})")
        return 0
    else:
        print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        return 1


def cmd_edit(args):
    """Fetch foods.toml, open in $EDITOR, push back to server"""
    import subprocess
    import tempfile

    server = get_server()

    text = fetch_text_from_server(server, '/api/foods/raw')
    if text is None:
        return 1

    editor = os.environ.get('EDITOR', 'vi')

    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write(text)
        tmpfile = f.name

    try:
        result = subprocess.run([editor, tmpfile])
        if result.returncode != 0:
            print(f"Editor exited with code {result.returncode}", file=sys.stderr)
            return 1

        with open(tmpfile, 'r') as f:
            new_content = f.read()

        if new_content == text:
            print("No changes made")
            return 0

        # Validate TOML before pushing
        try:
            import toml
            toml.loads(new_content)
        except Exception as e:
            print(f"Error: Invalid TOML: {e}", file=sys.stderr)
            print(f"Your edits are saved at: {tmpfile}", file=sys.stderr)
            return 1

        result = post_to_server(server, '/edit-foods', {'content': new_content})
        if result is None:
            print(f"Your edits are saved at: {tmpfile}", file=sys.stderr)
            return 1

        if result.get('success'):
            print("Config updated successfully")
            os.unlink(tmpfile)
            return 0
        else:
            print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
            print(f"Your edits are saved at: {tmpfile}", file=sys.stderr)
            return 1
    except KeyboardInterrupt:
        print(f"\nAborted. Your edits are saved at: {tmpfile}", file=sys.stderr)
        return 1


def cmd_add(args):
    """Add food from stdin TOML.

    TOML must use full path format: [pads.<pad_key>.foods.<food_key>]

    Example:
        [pads.other.foods.my-new-food]
        name = "My New Food"
        type = "unit"
        calories = 100
        protein = 10
    """
    # Read TOML from stdin
    print("Enter TOML configuration (Ctrl+D when done):", file=sys.stderr)
    toml_content = sys.stdin.read()

    if not toml_content.strip():
        print("Error: No TOML content provided", file=sys.stderr)
        return 1

    # Parse TOML
    try:
        import toml
        parsed = toml.loads(toml_content)
    except Exception as e:
        print(f"Error parsing TOML: {e}", file=sys.stderr)
        return 1

    server = get_server()

    result = post_to_server(server, '/api/foods', {'toml_content': toml_content})

    if result is None:
        return 1

    if result.get('success'):
        print(f"Food added successfully!")
        if result.get('pad_key') and result.get('food_key'):
            print(f"   Path: {result['pad_key']}/{result['food_key']}")
        return 0
    else:
        print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        return 1

def main():
    parser = argparse.ArgumentParser(description='Manage nutrition-pad foods')

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

    # Replace command
    replace_parser = subparsers.add_parser('replace', help='Replace a food from stdin TOML')

    # Edit command
    edit_parser = subparsers.add_parser('edit', help='Edit foods.toml in $EDITOR')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add food from stdin TOML (format: [pads.<pad>.foods.<key>])')

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
    elif args.command == 'replace':
        return cmd_replace(args)
    elif args.command == 'edit':
        return cmd_edit(args)
    elif args.command == 'add':
        return cmd_add(args)
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())
