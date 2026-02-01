#!/usr/bin/env python3
"""
Command-line tool to show food log entries from nutrition-pad.
"""

import os
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


def display_data(dates_data):
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
            total_cal += cal
            total_protein += protein

            print(f"  [{time_str}] {name} ({amount}) — {cal} kcal, {protein}g protein")

        print(f"\n  TOTAL: {total_cal:.0f} kcal, {total_protein:.1f}g protein")
        print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description='Show food log entries from nutrition-pad',
        epilog='Server configuration: Use "nutrition-client set-server HOST:PORT" to configure server'
    )
    parser.add_argument('--days', type=int, default=1, help='Number of days to show (default: 1 = today only)')
    args = parser.parse_args()

    config = load_config()
    server = config.get('server', 'localhost:5000')

    dates_data = fetch_from_server(server, args.days)

    if dates_data is None:
        print(f"\n❌ Error: Could not fetch from server: {server}")
        print(f"Config file: {CONFIG_FILE}")
        print("\nOptions:")
        print(f"  1. Check that the server is running")
        return

    if not dates_data:
        print("No entries found")
        return

    display_data(dates_data)


if __name__ == '__main__':
    main()
