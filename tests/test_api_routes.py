#!/usr/bin/env python3
"""
Tests for critical API routes

Ensures routes exist and don't return 500 errors.
Prevents accidental deletion of routes during refactoring.
"""

import sys
import os

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from nutrition_pad.main import app
    FLASK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import Flask modules: {e}")
    print("Skipping Flask-dependent tests. Install with: pip install flask toml")
    FLASK_AVAILABLE = False


def test_route_exists(client, method, path, name):
    """Test that a route exists and doesn't 500"""
    try:
        if method == 'GET':
            response = client.get(path)
        elif method == 'POST':
            response = client.post(path, json={})
        else:
            raise ValueError(f"Unknown method: {method}")

        status = response.status_code

        # Route should exist (not 404 for critical routes)
        # and should not crash (not 500)
        if status == 404:
            print(f"  ❌ {name}: Route not found (404)")
            return False
        elif status == 500:
            print(f"  ❌ {name}: Server error (500)")
            return False
        else:
            print(f"  ✓ {name}: OK (status {status})")
            return True

    except Exception as e:
        print(f"  ❌ {name}: Exception - {e}")
        return False


def test_critical_routes():
    """Test that all critical routes exist"""
    print("\n🧪 Testing critical routes\n")

    app.config['TESTING'] = True
    client = app.test_client()

    # Critical routes that must exist
    routes = [
        ('GET', '/', 'Main page'),
        ('GET', '/today', 'Today log page'),
        ('GET', '/nutrition', 'Nutrition dashboard'),
        ('GET', '/edit-foods', 'Edit foods page'),
        ('POST', '/log', 'Log food entry'),
        ('POST', '/delete-entry', 'Delete entry'),
        ('GET', '/api/foods', 'List foods API'),
        ('GET', '/api/foods/search?q=test', 'Search foods API'),
        ('POST', '/api/resolve-unknown', 'Resolve unknown API'),
        ('GET', '/api/entries', 'List entries API'),
    ]

    results = []
    for method, path, name in routes:
        results.append(test_route_exists(client, method, path, name))

    return all(results)


def test_css_classes_exist():
    """Test that critical CSS classes are in the HTML"""
    print("\n🧪 Testing CSS classes for Nexus 10 compatibility\n")

    try:
        app.config['TESTING'] = True
        client = app.test_client()

        response = client.get('/')
        html = response.data.decode('utf-8')

        # Check for float-based CSS (not aspect-ratio which breaks Nexus 10)
        assert 'food-btn' in html or 'food-grid' in html, \
            "Should have food button/grid classes"

        # Verify we're NOT using aspect-ratio (broken on old browsers)
        assert 'aspect-ratio' not in html, \
            "Should NOT use aspect-ratio CSS (breaks Nexus 10)"

        # Verify we're using float-based layout
        # (This is in the inline CSS in main.py)
        assert 'float: left' in html or 'float:left' in html, \
            "Should use float-based layout for Nexus 10 compatibility"

        print(f"  ✓ Float-based CSS present (Nexus 10 compatible)")
        print(f"  ✓ No aspect-ratio CSS (would break old browsers)")
        return True

    except AssertionError as e:
        print(f"  ❌ CSS check failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("  API ROUTES & CSS TESTS")
    print("="*60)

    if not FLASK_AVAILABLE:
        print("\n  ⚠ Flask not available - skipping tests")
        print("  Install dependencies: pip install flask toml")
        print("\n" + "="*60)
        return True  # Don't fail if Flask isn't installed

    results = []
    results.append(test_critical_routes())
    results.append(test_css_classes_exist())

    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"  RESULTS: {passed}/{total} test suites passed")
    print("="*60 + "\n")

    return all(results)


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
