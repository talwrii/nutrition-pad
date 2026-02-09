#!/usr/bin/env python3
"""
Test backdating entries via /log 'at' parameter.
Runs against isolated test server started by ./run-tests
"""

import sys
import os
import json
from datetime import date, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError

# Test server started by run-tests
BASE_URL = os.environ.get('TEST_SERVER', 'http://127.0.0.1:5099')


def test_backdate_entry():
    """POST /log with 'at' saves to correct date"""
    print("\n🧪 Test: backdate entry with 'at' parameter")

    yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    at_timestamp = f"{yesterday}T14:30:00"

    # POST backdated entry
    data = json.dumps({
        'pad': 'proteins',
        'food': 'eggs',
        'nonce': 'test_backdate',
        'at': at_timestamp
    }).encode()
    req = Request(f'{BASE_URL}/log', data=data,
                  headers={'Content-Type': 'application/json'})

    with urlopen(req, timeout=5) as resp:
        assert resp.status == 200, f"Log failed: {resp.status}"
    print(f"  ✓ POST /log with at={at_timestamp}")

    # GET /api/entries and verify
    with urlopen(f'{BASE_URL}/api/entries?days=2', timeout=5) as resp:
        result = json.loads(resp.read())

    yesterday_data = next((d for d in result['dates'] if d['date'] == yesterday), None)
    assert yesterday_data, f"No entries for {yesterday}"

    entries = yesterday_data['entries']
    eggs = next((e for e in entries if e['food'] == 'eggs' and e['time'] == '14:30'), None)
    assert eggs, f"No eggs at 14:30"

    print(f"  ✓ Entry in /api/entries at {yesterday} 14:30")
    return True


if __name__ == '__main__':
    print(f"\n{'='*50}")
    print(f"  BACKDATE TEST (server: {BASE_URL})")
    print('='*50)

    try:
        success = test_backdate_entry()
    except (AssertionError, URLError) as e:
        print(f"  ❌ {e}")
        success = False

    print(f"\n{'='*50}")
    print(f"  {'PASSED' if success else 'FAILED'}")
    print('='*50)
    sys.exit(0 if success else 1)
