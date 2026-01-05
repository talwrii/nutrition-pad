#!/usr/bin/env python3
"""
Client configuration management for nutrition-pad.
Use this to configure server settings used by nutrition-notes and nutrition-food.
"""
import os
import sys
import json
import argparse

CONFIG_DIR = os.path.expanduser('~/.nutrition-pad')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'notes.config')

def load_config():
    """Load configuration"""
    if not os.path.exists(CONFIG_FILE):
        return {'server': 'localhost:5000'}
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'server': 'localhost:5000'}

def save_config(config):
    """Save configuration"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def cmd_set_server(args):
    """Set server address"""
    config = load_config()
    config['server'] = args.server
    save_config(config)
    
    print(f"✓ Server set to: {args.server}")
    print(f"  Config file: {CONFIG_FILE}")
    print(f"\nThis server will be used by:")
    print(f"  • nutrition-notes")
    print(f"  • nutrition-food")
    
    return 0

def cmd_show(args):
    """Show current configuration"""
    config = load_config()
    
    print(f"Configuration: {CONFIG_FILE}")
    print(f"\nCurrent settings:")
    print(f"  Server: {config.get('server', 'localhost:5000')}")
    
    return 0

def cmd_reset(args):
    """Reset configuration to defaults"""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
        print(f"✓ Configuration reset to defaults")
        print(f"  Server: localhost:5000")
    else:
        print("Configuration already at defaults")
    
    return 0

def main():
    parser = argparse.ArgumentParser(
        description='Manage nutrition-pad client configuration',
        epilog='This command manages settings used by nutrition-notes and nutrition-food'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # set-server command
    server_parser = subparsers.add_parser('set-server', help='Set server address')
    server_parser.add_argument('server', metavar='HOST:PORT', 
                              help='Server address (e.g., nutrition.tatw.name:80 or localhost:5000)')
    
    # show command
    show_parser = subparsers.add_parser('show', help='Show current configuration')
    
    # reset command
    reset_parser = subparsers.add_parser('reset', help='Reset configuration to defaults')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'set-server':
        return cmd_set_server(args)
    elif args.command == 'show':
        return cmd_show(args)
    elif args.command == 'reset':
        return cmd_reset(args)
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())