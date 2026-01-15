#!/usr/bin/env python3
"""
Command-line tool to show notes and unknown entries from nutrition-pad logs.
Can read from local files or remote server.
"""

import os
import json
import argparse
import random
import string
from datetime import date, datetime, timedelta

LOGS_DIR = 'daily_logs'
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


def save_config(config):
    """Save server configuration"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def fetch_from_server(server, days):
    """Fetch notes from remote server"""
    try:
        import urllib.request
        
        url = f"http://{server}/api/notes?days={days}"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.load(response)
            return data.get('dates', [])
    except Exception as e:
        print(f"Error fetching from server: {e}")
        return None


def backfill_ids_for_file(filepath):
    """Add IDs to entries in a log file that don't have them. Returns True if modified."""
    try:
        with open(filepath, 'r') as f:
            entries = json.load(f)
    except (json.JSONDecodeError, IOError):
        return False
    
    modified = False
    for entry in entries:
        if 'id' not in entry or not entry['id']:
            # Generate ID based on timestamp if available
            if entry.get('timestamp'):
                try:
                    ts = datetime.fromisoformat(entry['timestamp'])
                    timestamp_part = ts.strftime('%Y%m%d%H%M%S')
                except:
                    timestamp_part = datetime.now().strftime('%Y%m%d%H%M%S')
            else:
                timestamp_part = datetime.now().strftime('%Y%m%d%H%M%S')
            
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            entry['id'] = f"{timestamp_part}{suffix}"
            modified = True
    
    if modified:
        with open(filepath, 'w') as f:
            json.dump(entries, f, indent=2)
    
    return modified


def backfill_all_ids():
    """Backfill IDs for all historic log files."""
    if not os.path.exists(LOGS_DIR):
        print("No logs directory found")
        return 0
    
    files_modified = 0
    files_checked = 0
    
    for filename in sorted(os.listdir(LOGS_DIR)):
        # Only process daily log files (YYYY-MM-DD.json), not notes files
        if filename.endswith('.json') and not filename.endswith('_notes.json'):
            filepath = os.path.join(LOGS_DIR, filename)
            files_checked += 1
            
            if backfill_ids_for_file(filepath):
                print(f"  ✓ Added IDs to: {filename}")
                files_modified += 1
    
    return files_checked, files_modified


def load_notes_local(date_str):
    """Load notes for a specific date from local files"""
    notes_file = os.path.join(LOGS_DIR, f'{date_str}_notes.json')
    if not os.path.exists(notes_file):
        return []
    
    try:
        with open(notes_file, 'r') as f:
            return json.load(f)
    except:
        return []


def load_unknowns_local(date_str):
    """Load unknown entries for a specific date from local files"""
    log_file = os.path.join(LOGS_DIR, f'{date_str}.json')
    if not os.path.exists(log_file):
        return []
    
    try:
        with open(log_file, 'r') as f:
            log_entries = json.load(f)
        
        unknowns = []
        for i, entry in enumerate(log_entries):
            if 'unknown' in entry.get('food', '').lower() or 'unknown' in entry.get('name', '').lower():
                entry['index'] = i
                unknowns.append(entry)
        
        return unknowns
    except:
        return []


def display_data(dates_data):
    """Display notes and unknowns interspersed by time"""
    total_notes = 0
    total_unknowns = 0
    
    for date_info in dates_data:
        date_str = date_info['date']
        notes = date_info['notes']
        unknowns = date_info['unknowns']
        
        if not notes and not unknowns:
            continue
        
        # Calculate how many days ago
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
        
        # Combine notes and unknowns into a single list with type markers
        items = []
        
        for note in notes:
            items.append({
                'type': 'note',
                'time': note.get('time', '??:??'),
                'timestamp': note.get('timestamp', ''),
                'id': note.get('id', ''),
                'text': note.get('text', ''),
                'done': note.get('done', False),
                'resolved_to': note.get('resolved_to')
            })
        
        for i, unk in enumerate(unknowns):
            # Use stored ID if available, otherwise show missing
            unk_id = unk.get('id', '(no id - run --backfill)')
            items.append({
                'type': 'unknown',
                'time': unk.get('time', '??:??'),
                'timestamp': unk.get('timestamp', ''),
                'id': unk_id,
                'name': unk.get('name', 'Unknown'),
                'amount_display': unk.get('amount_display', '?'),
                'index': unk.get('index', i),
                'resolved_to': unk.get('resolved_to')
            })
        
        # Sort by time
        def sort_key(item):
            time_str = item.get('time', '99:99')
            try:
                parts = time_str.split(':')
                return int(parts[0]) * 60 + int(parts[1])
            except:
                return 9999
        
        items.sort(key=sort_key)
        
        # Display interspersed items
        print(f"\n{len(notes)} notes, {len(unknowns)} unknowns:")
        print("-" * 60)
        
        for item in items:
            time_str = item.get('time', '??:??')
            item_id = item.get('id', '')
            resolved = f" → {item.get('resolved_to')}" if item.get('resolved_to') else ""
            
            if item['type'] == 'note':
                status = "✓" if item.get('done') else "⏳"
                print(f"  [{time_str}] 📝 {status} {item['text']}{resolved}")
                print(f"           ID: {item_id}")
                total_notes += 1
            else:
                print(f"  [{time_str}] ❓ {item['name']} ({item['amount_display']}){resolved}")
                print(f"           ID: {item_id}")
                total_unknowns += 1
    
    print(f"\n{'='*60}")
    print(f"TOTAL: {total_notes} notes, {total_unknowns} unknowns")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Show notes and unknowns from nutrition-pad',
        epilog='Server configuration: Use "nutrition-client set-server HOST:PORT" to configure server'
    )
    parser.add_argument('--days', type=int, default=1, help='Number of days to show (default: 1 = today only)')
    parser.add_argument('--all', action='store_true', help='Show all available days')
    parser.add_argument('--local', action='store_true', help='Read from local files instead of server')
    parser.add_argument('--backfill', action='store_true', help='Add IDs to historic entries that lack them')
    args = parser.parse_args()
    
    # Handle backfill command
    if args.backfill:
        print("Backfilling IDs for historic log entries...")
        files_checked, files_modified = backfill_all_ids()
        print(f"\nChecked {files_checked} files, modified {files_modified}")
        return
    
    # Load config
    config = load_config()
    server = config.get('server', 'localhost:5000')
    
    # Determine days to fetch
    if args.all:
        days = 365  # Fetch up to a year
    else:
        days = args.days
    
    # Fetch from server OR local, NEVER both
    dates_data = []
    
    if args.local:
        # Explicitly read from local files
        if args.all:
            # Find all log files locally
            if not os.path.exists(LOGS_DIR):
                print("No logs directory found")
                return
            
            files = os.listdir(LOGS_DIR)
            dates = set()
            for f in files:
                if f.endswith('.json'):
                    date_part = f.replace('_notes.json', '').replace('.json', '')
                    if date_part and date_part[0].isdigit():
                        dates.add(date_part)
            
            dates = sorted(dates, reverse=True)
        else:
            # Generate dates for the specified number of days
            dates = []
            for days_ago in range(days):
                target_date = date.today() - timedelta(days=days_ago)
                dates.append(target_date.strftime('%Y-%m-%d'))
        
        # Load from local files
        for date_str in dates:
            notes = load_notes_local(date_str)
            unknowns = load_unknowns_local(date_str)
            
            if notes or unknowns:
                dates_data.append({
                    'date': date_str,
                    'notes': notes,
                    'unknowns': unknowns
                })
    else:
        # Fetch from server - do NOT fall back to local
        dates_data = fetch_from_server(server, days)
        
        if dates_data is None:
            print(f"\n❌ Error: Could not fetch from server: {server}")
            print(f"Config file: {CONFIG_FILE}")
            print("\nOptions:")
            print(f"  1. Check that the server is running")
            print(f"  2. Use --set-server to configure a different server")
            print(f"  3. Use --local to read from local files instead")
            return
    
    if not dates_data:
        print("No data found")
        return
    
    display_data(dates_data)


if __name__ == '__main__':
    main()