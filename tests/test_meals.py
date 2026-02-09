#!/usr/bin/env python3
"""
Full-stack tests for the meals feature.

Tests the complete flow: create meal, list meals, log meal, verify entries.
"""

import sys
import os
import json
import shutil
from datetime import date

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from nutrition_pad.main import app
    from nutrition_pad.data import MEALS_FILE, LOGS_DIR, get_today_log_file
    FLASK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import Flask modules: {e}")
    print("Skipping Flask-dependent tests. Install with: pip install flask toml")
    FLASK_AVAILABLE = False


MEALS_BACKUP = MEALS_FILE + '.test_backup' if FLASK_AVAILABLE else None


def backup_meals():
    """Back up meals.json before tests"""
    if os.path.exists(MEALS_FILE):
        shutil.copy2(MEALS_FILE, MEALS_BACKUP)


def restore_meals():
    """Restore meals.json after tests"""
    if MEALS_BACKUP and os.path.exists(MEALS_BACKUP):
        shutil.copy2(MEALS_BACKUP, MEALS_FILE)
        os.remove(MEALS_BACKUP)
    elif MEALS_BACKUP and os.path.exists(MEALS_FILE):
        # No backup means file didn't exist before — remove what tests created
        os.remove(MEALS_FILE)


def remove_test_entries_from_log():
    """Remove any entries with meal_uid starting with 'meallog_' that were created during tests"""
    log_file = get_today_log_file()
    if not os.path.exists(log_file):
        return
    with open(log_file, 'r') as f:
        entries = json.load(f)
    # Keep entries that don't have a test marker
    cleaned = [e for e in entries if not e.get('name', '').startswith('__test_meal_')]
    if len(cleaned) != len(entries):
        with open(log_file, 'w') as f:
            json.dump(cleaned, f, indent=2)


def test_meals_routes_exist():
    """Test that all meal routes exist and don't 500"""
    print("\n🧪 Test: meal routes exist")

    app.config['TESTING'] = True
    client = app.test_client()

    routes = [
        ('GET', '/meals/build', 'Meals build page'),
        ('GET', '/api/meals', 'List meals API'),
        ('POST', '/meals/create', 'Create meal (no data)'),
        ('POST', '/log-meal', 'Log meal (no data)'),
    ]

    ok = True
    for method, path, name in routes:
        try:
            if method == 'GET':
                response = client.get(path)
            else:
                response = client.post(path, json={})

            if response.status_code == 404:
                print(f"  ❌ {name}: Route not found (404)")
                ok = False
            elif response.status_code == 500:
                print(f"  ❌ {name}: Server error (500)")
                ok = False
            else:
                print(f"  ✓ {name}: OK (status {response.status_code})")
        except Exception as e:
            print(f"  ❌ {name}: Exception - {e}")
            ok = False

    return ok


def test_create_meal_validation():
    """Test that meal creation validates input"""
    print("\n🧪 Test: meal creation validation")

    app.config['TESTING'] = True
    client = app.test_client()

    ok = True

    # No name
    response = client.post('/meals/create', json={'name': '', 'items': [{'name': 'x'}]})
    data = json.loads(response.data)
    if response.status_code != 400:
        print(f"  ❌ Empty name should return 400 (got {response.status_code})")
        ok = False
    else:
        print(f"  ✓ Empty name rejected (400)")

    # No items
    response = client.post('/meals/create', json={'name': 'Test', 'items': []})
    if response.status_code != 400:
        print(f"  ❌ Empty items should return 400 (got {response.status_code})")
        ok = False
    else:
        print(f"  ✓ Empty items rejected (400)")

    # No data at all
    response = client.post('/meals/create', data='not json', content_type='text/plain')
    if response.status_code != 400:
        print(f"  ❌ No JSON should return 400 (got {response.status_code})")
        ok = False
    else:
        print(f"  ✓ Non-JSON body rejected (400)")

    return ok


def test_create_and_list_meal():
    """Test creating a meal and listing it"""
    print("\n🧪 Test: create meal and list it")

    app.config['TESTING'] = True
    client = app.test_client()

    meal_payload = {
        'name': '__test_meal_create_list',
        'items': [
            {
                'pad': 'proteins', 'food': 'chicken_breast',
                'name': 'Chicken Breast', 'type': 'amount',
                'amount': 150, 'calories_per_gram': 1.46,
                'protein_per_gram': 0.27, 'fiber_per_gram': 0.0
            },
            {
                'pad': 'proteins', 'food': 'eggs',
                'name': 'Eggs', 'type': 'unit',
                'calories': 140, 'protein': 12, 'fiber': 0
            }
        ]
    }

    # Create
    response = client.post('/meals/create', json=meal_payload)
    if response.status_code != 200:
        print(f"  ❌ Create failed (status {response.status_code})")
        return False

    create_data = json.loads(response.data)
    if not create_data.get('success'):
        print(f"  ❌ Create response not successful: {create_data}")
        return False

    meal_id = create_data.get('meal_id')
    if not meal_id:
        print(f"  ❌ No meal_id in response")
        return False

    print(f"  ✓ Meal created (id: {meal_id})")

    # List
    response = client.get('/api/meals')
    if response.status_code != 200:
        print(f"  ❌ List failed (status {response.status_code})")
        return False

    list_data = json.loads(response.data)
    meals = list_data.get('meals', [])
    our_meal = next((m for m in meals if m['id'] == meal_id), None)

    if not our_meal:
        print(f"  ❌ Created meal not found in list")
        return False

    if our_meal['name'] != '__test_meal_create_list':
        print(f"  ❌ Meal name mismatch: {our_meal['name']}")
        return False

    if our_meal['item_count'] != 2:
        print(f"  ❌ Item count should be 2, got {our_meal['item_count']}")
        return False

    # 150g * 1.46 = 219 + 140 = 359
    expected_cal = 359
    if our_meal['total_calories'] != expected_cal:
        print(f"  ❌ Total calories should be {expected_cal}, got {our_meal['total_calories']}")
        return False

    # 150g * 0.27 = 40.5 + 12 = 52.5
    expected_prot = 52.5
    if our_meal['total_protein'] != expected_prot:
        print(f"  ❌ Total protein should be {expected_prot}, got {our_meal['total_protein']}")
        return False

    print(f"  ✓ Meal listed with correct totals ({expected_cal} kcal, {expected_prot}g protein)")
    return True


def test_log_meal_creates_entries():
    """Test that logging a meal creates header + food entries in daily log"""
    print("\n🧪 Test: log meal creates linked entries")

    app.config['TESTING'] = True
    client = app.test_client()

    # First create a meal
    meal_payload = {
        'name': '__test_meal_log_entries',
        'items': [
            {
                'pad': 'proteins', 'food': 'chicken_breast',
                'name': 'Chicken Breast', 'type': 'amount',
                'amount': 200, 'calories_per_gram': 1.46,
                'protein_per_gram': 0.27, 'fiber_per_gram': 0.0
            },
            {
                'pad': 'proteins', 'food': 'eggs',
                'name': 'Eggs', 'type': 'unit',
                'calories': 140, 'protein': 12, 'fiber': 0
            }
        ]
    }

    response = client.post('/meals/create', json=meal_payload)
    create_data = json.loads(response.data)
    meal_id = create_data['meal_id']

    # Log the meal
    response = client.post('/log-meal', json={
        'meal_id': meal_id,
        'nonce': 'test_meals_log_001'
    })

    if response.status_code != 200:
        print(f"  ❌ Log meal failed (status {response.status_code})")
        return False

    log_data = json.loads(response.data)
    if log_data.get('status') != 'success':
        print(f"  ❌ Log meal not successful: {log_data}")
        return False

    if log_data.get('items_logged') != 2:
        print(f"  ❌ Expected 2 items logged, got {log_data.get('items_logged')}")
        return False

    print(f"  ✓ Meal logged (items: {log_data['items_logged']}, calories: {log_data['total_calories']})")

    # Read today's log and verify entries
    log_file = get_today_log_file()
    if not os.path.exists(log_file):
        print(f"  ❌ Today's log file not found")
        return False

    with open(log_file, 'r') as f:
        entries = json.load(f)

    # Find entries with this meal's name prefix
    meal_entries = [e for e in entries if e.get('name', '').startswith('__test_meal_log_entries') or
                    (e.get('meal_uid') and e.get('food') in ['chicken_breast', 'eggs'] and
                     e.get('name', '').startswith('__test_meal_') is False)]

    # More reliable: find by meal header name
    headers = [e for e in entries if e.get('is_meal_header') and e.get('name') == '__test_meal_log_entries']
    if not headers:
        print(f"  ❌ No meal header entry found")
        return False

    header = headers[-1]  # Take the latest one
    meal_uid = header.get('meal_uid')

    if not meal_uid:
        print(f"  ❌ Header entry has no meal_uid")
        return False

    if not meal_uid.startswith('meallog_'):
        print(f"  ❌ meal_uid should start with 'meallog_', got: {meal_uid}")
        return False

    print(f"  ✓ Header entry found (meal_uid: {meal_uid})")

    # Check header properties
    ok = True
    if header.get('pad') != '_meal':
        print(f"  ❌ Header pad should be '_meal', got: {header.get('pad')}")
        ok = False
    if header.get('calories') != 0:
        print(f"  ❌ Header calories should be 0, got: {header.get('calories')}")
        ok = False
    if not header.get('is_meal_header'):
        print(f"  ❌ Header should have is_meal_header=True")
        ok = False
    if ok:
        print(f"  ✓ Header entry has correct properties (pad=_meal, calories=0, is_meal_header=True)")

    # Find linked food entries
    linked = [e for e in entries if e.get('meal_uid') == meal_uid and not e.get('is_meal_header')]
    if len(linked) != 2:
        print(f"  ❌ Expected 2 linked food entries, found {len(linked)}")
        return False

    print(f"  ✓ Found {len(linked)} linked food entries")

    # Verify chicken breast entry (200g * 1.46 = 292 kcal, 200g * 0.27 = 54g protein)
    chicken = next((e for e in linked if e.get('food') == 'chicken_breast'), None)
    if not chicken:
        print(f"  ❌ Chicken breast entry not found")
        return False

    if chicken.get('calories') != 292.0:
        print(f"  ❌ Chicken calories should be 292.0, got: {chicken.get('calories')}")
        ok = False
    if chicken.get('protein') != 54.0:
        print(f"  ❌ Chicken protein should be 54.0, got: {chicken.get('protein')}")
        ok = False
    if chicken.get('amount_display') != '200g':
        print(f"  ❌ Chicken amount_display should be '200g', got: {chicken.get('amount_display')}")
        ok = False
    if ok:
        print(f"  ✓ Chicken entry correct (292 kcal, 54g protein, 200g)")

    # Verify eggs entry (unit type)
    eggs = next((e for e in linked if e.get('food') == 'eggs'), None)
    if not eggs:
        print(f"  ❌ Eggs entry not found")
        return False

    if eggs.get('calories') != 140:
        print(f"  ❌ Eggs calories should be 140, got: {eggs.get('calories')}")
        ok = False
    if eggs.get('protein') != 12:
        print(f"  ❌ Eggs protein should be 12, got: {eggs.get('protein')}")
        ok = False
    if eggs.get('amount_display') != '1 unit':
        print(f"  ❌ Eggs amount_display should be '1 unit', got: {eggs.get('amount_display')}")
        ok = False
    if ok:
        print(f"  ✓ Eggs entry correct (140 kcal, 12g protein, 1 unit)")

    return ok


def test_log_meal_not_found():
    """Test logging a non-existent meal returns 404"""
    print("\n🧪 Test: log non-existent meal returns 404")

    app.config['TESTING'] = True
    client = app.test_client()

    response = client.post('/log-meal', json={
        'meal_id': 'meal_nonexistent_999',
        'nonce': 'test_404'
    })

    if response.status_code != 404:
        print(f"  ❌ Expected 404, got {response.status_code}")
        return False

    print(f"  ✓ Non-existent meal returns 404")
    return True


def test_meals_build_page_renders():
    """Test that the meals build page renders correctly"""
    print("\n🧪 Test: meals build page renders")

    app.config['TESTING'] = True
    client = app.test_client()

    response = client.get('/meals/build')
    if response.status_code != 200:
        print(f"  ❌ Build page failed (status {response.status_code})")
        return False

    html = response.data.decode('utf-8')

    ok = True
    if 'Building Meal' not in html:
        print(f"  ❌ Missing 'Building Meal' title")
        ok = False
    if 'meal-name' not in html:
        print(f"  ❌ Missing meal name input")
        ok = False
    if 'doneMeal' not in html:
        print(f"  ❌ Missing doneMeal function")
        ok = False
    if 'sessionStorage' not in html:
        print(f"  ❌ Missing sessionStorage usage")
        ok = False

    if ok:
        print(f"  ✓ Build page renders with expected elements")
    return ok


def test_meals_tab_on_index():
    """Test that the meals tab appears on the food pads page"""
    print("\n🧪 Test: meals tab on food pads page")

    app.config['TESTING'] = True
    client = app.test_client()

    response = client.get('/?pad=meals')
    if response.status_code != 200:
        print(f"  ❌ Index with pad=meals failed (status {response.status_code})")
        return False

    html = response.data.decode('utf-8')

    ok = True
    if 'pad=meals' not in html:
        print(f"  ❌ Missing meals tab link")
        ok = False
    if 'logMeal' not in html:
        print(f"  ❌ Missing logMeal function")
        ok = False

    if ok:
        print(f"  ✓ Meals tab present on food pads page")
    return ok


def test_meal_active_indicator_on_pages():
    """Test that meal-active indicator exists on today and nutrition pages"""
    print("\n🧪 Test: meal-active indicator on today + nutrition pages")

    app.config['TESTING'] = True
    client = app.test_client()

    ok = True
    for page, name in [('/today', 'Today page'), ('/nutrition', 'Nutrition dashboard')]:
        response = client.get(page)
        if response.status_code != 200:
            print(f"  ❌ {name} failed (status {response.status_code})")
            ok = False
            continue

        html = response.data.decode('utf-8')
        if 'meal-active-indicator' not in html:
            print(f"  ❌ {name}: missing meal-active-indicator div")
            ok = False
        elif 'checkMealMode' not in html:
            print(f"  ❌ {name}: missing checkMealMode function")
            ok = False
        else:
            print(f"  ✓ {name}: has meal-active indicator + checkMealMode")

    return ok


def test_meal_mode_intercept_on_index():
    """Test that meal mode intercept exists on food pads page"""
    print("\n🧪 Test: meal mode intercept on food pads page")

    app.config['TESTING'] = True
    client = app.test_client()

    response = client.get('/')
    html = response.data.decode('utf-8')

    ok = True
    if 'mealMode' not in html:
        print(f"  ❌ Missing mealMode variable")
        ok = False
    if 'addToMeal' not in html:
        print(f"  ❌ Missing addToMeal function")
        ok = False
    if 'restoreMealMode' not in html:
        print(f"  ❌ Missing restoreMealMode function")
        ok = False
    if 'meal-mode-indicator' not in html:
        print(f"  ❌ Missing meal-mode-indicator div")
        ok = False

    if ok:
        print(f"  ✓ Food pads page has meal mode intercept (mealMode, addToMeal, restoreMealMode)")
    return ok


def test_meal_mode_server_sync():
    """Test that meal mode syncs via server to all clients"""
    print("\n🧪 Test: meal mode server sync")

    app.config['TESTING'] = True
    client = app.test_client()

    ok = True

    # Initially meal mode should be off
    response = client.get('/poll-updates?since=0&amount_since=0')
    if response.status_code != 200:
        print(f"  ❌ Poll failed: {response.status_code}")
        return False
    data = response.get_json()
    if data.get('meal_mode') != False:
        print(f"  ❌ Initial meal_mode should be False, got: {data.get('meal_mode')}")
        ok = False
    else:
        print("  ✓ Initial meal_mode is False")

    # Set meal mode on
    response = client.post('/set-meal-mode', json={'active': True})
    if response.status_code != 200:
        print(f"  ❌ Set meal mode failed: {response.status_code}")
        return False
    data = response.get_json()
    if data.get('meal_mode') != True:
        print(f"  ❌ Response meal_mode should be True, got: {data.get('meal_mode')}")
        ok = False
    else:
        print("  ✓ Set meal_mode to True")

    # Poll should now show meal mode on
    response = client.get('/poll-updates?since=0&amount_since=0')
    data = response.get_json()
    if data.get('meal_mode') != True:
        print(f"  ❌ Poll meal_mode should be True, got: {data.get('meal_mode')}")
        ok = False
    else:
        print("  ✓ Poll returns meal_mode=True")

    # Set meal mode off
    response = client.post('/set-meal-mode', json={'active': False})
    if response.status_code != 200:
        print(f"  ❌ Set meal mode off failed: {response.status_code}")
        return False
    print("  ✓ Set meal_mode to False")

    # Poll should show meal mode off
    response = client.get('/poll-updates?since=0&amount_since=0')
    data = response.get_json()
    if data.get('meal_mode') != False:
        print(f"  ❌ Poll meal_mode should be False, got: {data.get('meal_mode')}")
        ok = False
    else:
        print("  ✓ Poll returns meal_mode=False after disabling")

    return ok


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  MEALS FEATURE TESTS")
    print("=" * 60)

    if not FLASK_AVAILABLE:
        print("\n  ⚠ Flask not available - skipping tests")
        print("  Install dependencies: pip install flask toml")
        print("\n" + "=" * 60)
        return True

    backup_meals()

    try:
        tests = [
            test_meals_routes_exist,
            test_meals_build_page_renders,
            test_create_meal_validation,
            test_create_and_list_meal,
            test_log_meal_creates_entries,
            test_log_meal_not_found,
            test_meals_tab_on_index,
            test_meal_active_indicator_on_pages,
            test_meal_mode_intercept_on_index,
            test_meal_mode_server_sync,
        ]

        results = []
        for test in tests:
            results.append(test())

        print("\n" + "=" * 60)
        passed = sum(results)
        total = len(results)
        print(f"  RESULTS: {passed}/{total} tests passed")
        print("=" * 60 + "\n")

        return all(results)

    finally:
        restore_meals()
        remove_test_entries_from_log()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
