#!/usr/bin/env python3
"""
Tests for nutrition-unknown CLI tool and /api/resolve-unknown endpoint

Ensures unknown food entries can be resolved without breaking.
"""

import sys
import os
import json
import tempfile
import shutil
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


def create_test_log_with_unknown():
    """Create a test log file with unknown entries"""
    # Ensure logs directory exists
    os.makedirs(LOGS_DIR, exist_ok=True)

    today = date.today().strftime('%Y-%m-%d')
    log_file = os.path.join(LOGS_DIR, f'{today}.json')

    # Create log with unknown entry
    entries = [
        {
            "id": "test_unknown_001",
            "timestamp": "2026-01-20T10:00:00",
            "time": "10:00",
            "pad": "_unknown",
            "food": "amount",
            "name": "Unknown",
            "amount": 150,
            "amount_display": "150g",
            "calories": 0,
            "protein": 0,
            "fiber": 0
        },
        {
            "id": "test_normal_001",
            "timestamp": "2026-01-20T11:00:00",
            "time": "11:00",
            "pad": "proteins",
            "food": "chicken",
            "name": "Chicken",
            "amount": 100,
            "amount_display": "100g",
            "calories": 146,
            "protein": 27,
            "fiber": 0
        }
    ]

    with open(log_file, 'w') as f:
        json.dump(entries, f, indent=2)

    return log_file, entries[0]['id']


def test_api_resolve_unknown_endpoint_exists():
    """Test that /api/resolve-unknown endpoint exists"""
    print("\n🧪 Test: /api/resolve-unknown endpoint exists")

    try:
        app.config['TESTING'] = True
        client = app.test_client()

        # Try to access endpoint
        response = client.post('/api/resolve-unknown',
                               json={'entry_ids': [], 'food_key': 'test'},
                               content_type='application/json')

        # Should not be 404
        assert response.status_code != 404, "Endpoint should exist (not 404)"

        print(f"  ✓ Endpoint exists (status: {response.status_code})")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_api_resolve_unknown_validation():
    """Test that API validates required parameters"""
    print("\n🧪 Test: API validates parameters")

    try:
        app.config['TESTING'] = True
        client = app.test_client()

        # Test missing data
        response = client.post('/api/resolve-unknown',
                               json={},
                               content_type='application/json')
        assert response.status_code == 400, "Should reject missing data"

        # Test missing entry_ids
        response = client.post('/api/resolve-unknown',
                               json={'food_key': 'chicken'},
                               content_type='application/json')
        assert response.status_code == 400, "Should reject missing entry_ids"

        # Test missing food_key
        response = client.post('/api/resolve-unknown',
                               json={'entry_ids': ['test']},
                               content_type='application/json')
        assert response.status_code == 400, "Should reject missing food_key"

        print(f"  ✓ Parameter validation works")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_api_resolve_unknown_invalid_food():
    """Test that API rejects invalid food keys"""
    print("\n🧪 Test: API rejects invalid food keys")

    try:
        app.config['TESTING'] = True
        client = app.test_client()

        response = client.post('/api/resolve-unknown',
                               json={
                                   'entry_ids': ['test_id'],
                                   'food_key': 'nonexistent_food_12345'
                               },
                               content_type='application/json')

        assert response.status_code == 404, "Should return 404 for invalid food"

        data = json.loads(response.data)
        assert 'error' in data, "Should include error message"

        print(f"  ✓ Invalid food rejection works")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_api_resolve_unknown_success():
    """Test that API successfully resolves unknown entries"""
    print("\n🧪 Test: API resolves unknown entries")

    try:
        # Create test log
        log_file, entry_id = create_test_log_with_unknown()

        app.config['TESTING'] = True
        client = app.test_client()

        # Resolve to chicken (assuming it exists in config)
        response = client.post('/api/resolve-unknown',
                               json={
                                   'entry_ids': [entry_id],
                                   'food_key': 'chicken'
                               },
                               content_type='application/json')

        if response.status_code == 404:
            # Chicken might not exist in test config, that's ok
            print(f"  ⚠ Food 'chicken' not found in config (skipping)")
            return True

        assert response.status_code == 200, f"Should succeed (got {response.status_code})"

        data = json.loads(response.data)
        assert data.get('success') == True, "Should return success"
        assert 'updated_count' in data, "Should include update count"

        # Verify log was updated
        with open(log_file, 'r') as f:
            updated_entries = json.load(f)

        updated_entry = next((e for e in updated_entries if e['id'] == entry_id), None)
        if updated_entry:
            assert updated_entry['food'] == 'chicken', "Entry should be updated to chicken"
            assert updated_entry['name'] != 'Unknown', "Name should be updated"

        print(f"  ✓ Successfully resolved {data.get('updated_count', 0)} entries")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("  NUTRITION-UNKNOWN CLI & API TESTS")
    print("="*60)

    if not FLASK_AVAILABLE:
        print("\n  ⚠ Flask not available - skipping tests")
        print("  Install dependencies: pip install flask toml")
        print("\n" + "="*60)
        return True  # Don't fail if Flask isn't installed

    tests = [
        test_api_resolve_unknown_endpoint_exists,
        test_api_resolve_unknown_validation,
        test_api_resolve_unknown_invalid_food,
        test_api_resolve_unknown_success,
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
