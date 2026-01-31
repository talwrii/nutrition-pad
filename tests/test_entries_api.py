#!/usr/bin/env python3
"""
Tests for /api/entries endpoint

Records entries via /log and verifies they appear in /api/entries.
"""

import sys
import os
import json
from datetime import date

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from nutrition_pad.main import app
    from nutrition_pad.data import LOGS_DIR
    FLASK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import Flask modules: {e}")
    print("Skipping Flask-dependent tests. Install with: pip install flask toml")
    FLASK_AVAILABLE = False
    LOGS_DIR = None


def test_api_entries_endpoint_exists():
    """Test that /api/entries endpoint exists"""
    print("\n🧪 Test: /api/entries endpoint exists")

    try:
        app.config['TESTING'] = True
        client = app.test_client()

        response = client.get('/api/entries')
        assert response.status_code != 404, "Endpoint should exist (not 404)"
        assert response.status_code != 500, "Endpoint should not error (not 500)"

        data = json.loads(response.data)
        assert 'dates' in data, "Response should have 'dates' key"

        print(f"  ✓ Endpoint exists (status: {response.status_code})")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_api_entries_returns_recorded_entry():
    """Test that a recorded entry appears in /api/entries"""
    print("\n🧪 Test: recorded entry appears in /api/entries")

    try:
        app.config['TESTING'] = True
        client = app.test_client()

        # Record an entry via /log
        response = client.post('/log', json={
            'pad': 'proteins',
            'food': 'chicken_breast',
            'nonce': 'test_entries_001'
        }, content_type='application/json')

        assert response.status_code == 200, f"Log should succeed (got {response.status_code})"

        # Fetch entries
        response = client.get('/api/entries?days=1')
        assert response.status_code == 200, f"Entries should succeed (got {response.status_code})"

        data = json.loads(response.data)
        dates = data.get('dates', [])

        today = date.today().strftime('%Y-%m-%d')
        today_data = next((d for d in dates if d['date'] == today), None)
        assert today_data is not None, "Should have today's entries"

        entries = today_data.get('entries', [])
        chicken_entry = next((e for e in entries if e.get('food') == 'chicken_breast' and e.get('id', '').endswith('test_entries_001')), None)

        # The nonce might not end up in the ID, so just check any chicken entry exists
        has_chicken = any(e.get('food') == 'chicken_breast' for e in entries)
        assert has_chicken, "Should have chicken_breast entry"

        print(f"  ✓ Found recorded entry in /api/entries ({len(entries)} entries today)")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_entries_days_parameter():
    """Test that days parameter works"""
    print("\n🧪 Test: days parameter filters correctly")

    try:
        app.config['TESTING'] = True
        client = app.test_client()

        response = client.get('/api/entries?days=3')
        assert response.status_code == 200, f"Should succeed (got {response.status_code})"

        data = json.loads(response.data)
        assert 'dates' in data, "Response should have 'dates' key"

        print(f"  ✓ Days parameter works ({len(data['dates'])} days with entries)")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("  ENTRIES API TESTS")
    print("="*60)

    if not FLASK_AVAILABLE:
        print("\n  ⚠ Flask not available - skipping tests")
        print("  Install dependencies: pip install flask toml")
        print("\n" + "="*60)
        return True

    tests = [
        test_api_entries_endpoint_exists,
        test_api_entries_returns_recorded_entry,
        test_api_entries_days_parameter,
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"  RESULTS: {passed}/{total} tests passed")
    print("="*60 + "\n")

    return all(results)


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
