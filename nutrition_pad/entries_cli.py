#!/usr/bin/env python3
"""
Command-line tool to show and manage food log entries from nutrition-pad.

Usage:
    nutrition-entries                    # List today's entries
    nutrition-entries list [--days N]    # List entries from last N days
    nutrition-entries delete <id>        # Delete entry by ID
"""

import os
import sys
import json
import argparse
from datetime import date

CONFIG_DIR = os.path.expanduser('~/.nutrition-pad')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'notes.config')


def load_config():
    """Load server configuration"""
    if not os.path.exists(CONFIG_FILE):
        return {'server': 'localhost:5000'}

    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'server': 'localhost:5000'}


def fetch_from_server(server, days):
    """Fetch entries from remote server"""
    try:
        import urllib.request

        url = f"http://{server}/api/entries?days={days}"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.load(response)
            return data.get('dates', [])
    except Exception as e:
        print(f"Error fetching from server: {e}")
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


def display_data(dates_data, show_id=False):
    """Display food log entries"""
    for date_info in dates_data:
        date_str = date_info['date']
        entries = date_info['entries']

        if not entries:
            continue

        try:
            target = date.fromisoformat(date_str)
            today = date.today()
            days_diff = (today - target).days
            if days_diff == 0:
                date_label = "TODAY"
            elif days_diff == 1:
                date_label = "YESTERDAY"
            else:
                date_label = f"{days_diff} DAYS AGO"
        except:
            date_label = date_str

        print(f"\n{'='*60}")
        print(f"{date_str} ({date_label})")
        print(f"{'='*60}")

        total_cal = 0
        total_protein = 0

        for entry in entries:
            time_str = entry.get('time', '??:??')
            name = entry.get('name', entry.get('food', '?'))
            amount = entry.get('amount_display', '?')
            cal = entry.get('calories', 0)
            protein = entry.get('protein', 0)
            entry_id = entry.get('id', '?')
            total_cal += cal
            total_protein += protein

            if show_id:
                print(f"  [{entry_id}] [{time_str}] {name} ({amount}) — {cal} kcal, {protein}g protein")
            else:
                print(f"  [{time_str}] {name} ({amount}) — {cal} kcal, {protein}g protein")

        print(f"\n  TOTAL: {total_cal:.0f} kcal, {total_protein:.1f}g protein")
        print(f"{'='*60}")


def cmd_list(args):
    """List entries"""
    config = load_config()
    server = config.get('server', 'localhost:5000')

    dates_data = fetch_from_server(server, args.days)

    if dates_data is None:
        print(f"\n❌ Error: Could not fetch from server: {server}")
        print(f"Config file: {CONFIG_FILE}")
        print("\nOptions:")
        print(f"  1. Check that the server is running")
        return 1

    if not dates_data:
        print("No entries found")
        return 0

    display_data(dates_data, show_id=args.id)
    return 0


def cmd_delete(args):
    """Delete an entry by ID"""
    config = load_config()
    server = config.get('server', 'localhost:5000')

    entry_id = args.entry_id

    # Extract date from ID to find and show the entry
    try:
        date_part = entry_id[:8]
        target_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
    except:
        print(f"❌ Invalid entry ID format: {entry_id}")
        return 1

    # Fetch and show the entry we're about to delete
    dates_data = fetch_from_server(server, 30)  # Look back a month
    entry_found = None
    if dates_data:
        for date_info in dates_data:
            if date_info['date'] == target_date:
                for entry in date_info['entries']:
                    if entry.get('id') == entry_id:
                        entry_found = entry
                        break
                break

    if entry_found:
        name = entry_found.get('name', entry_found.get('food', '?'))
        time_str = entry_found.get('time', '??:??')
        print(f"Deleting: [{time_str}] {name} from {target_date}")
    else:
        print(f"⚠️  Entry {entry_id} not found locally, attempting server delete...")

    payload = {'id': entry_id}
    result = post_to_server(server, '/delete-entry', payload)

    if result and result.get('status') == 'success':
        print(f"✅ Entry deleted")
        return 0
    else:
        error = result.get('error', 'Unknown error') if result else 'Server error'
        print(f"❌ Failed to delete: {error}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description='Show and manage food log entries from nutrition-pad',
        epilog='Server configuration: Use "nutrition-client set-server HOST:PORT" to configure server'
    )
    subparsers = parser.add_subparsers(dest='command')

    # List command
    list_parser = subparsers.add_parser('list', help='List entries')
    list_parser.add_argument('--days', type=int, default=1,
                            help='Number of days to show (default: 1 = today only)')
    list_parser.add_argument('--id', '-i', action='store_true',
                            help='Show entry IDs (for delete command)')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete an entry by ID')
    delete_parser.add_argument('entry_id', help='Entry ID (use "list --id" to see IDs)')

    args = parser.parse_args()

    # Default to list if no command given
    if args.command is None:
        args.command = 'list'
        args.days = 1
        args.id = False

    if args.command == 'list':
        return cmd_list(args)
    elif args.command == 'delete':
        return cmd_delete(args)


if __name__ == '__main__':
    sys.exit(main() or 0)
