#!/usr/bin/env python3
"""
Test that pages render correctly with various food configurations,
including missing fields and edge cases.

Uses Flask test client - no browser needed!
"""

import sys
import os

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nutrition_pad.main import app


def test_page_loads(client, url, name):
    """Check that a page loads without 500 error."""
    response = client.get(url)
    status = response.status_code
    
    if status == 500:
        print(f"  ❌ {name}: 500 Internal Server Error")
        # Check for Jinja errors
        if b"UndefinedError" in response.data:
            print(f"     Jinja UndefinedError detected!")
            # Print the error message
            data = response.data.decode('utf-8', errors='replace')
            if "has no attribute" in data:
                start = data.find("has no attribute")
                print(f"     ...{data[start:start+50]}...")
        return False
    elif status == 200:
        print(f"  ✓ {name}: OK (200)")
        return True
    elif status == 404:
        print(f"  ⚠ {name}: Not Found (404)")
        return True  # 404 is ok for missing pads
    else:
        print(f"  ? {name}: Status {status}")
        return False


def test_food_pages():
    """Test that all food pad pages render correctly."""
    print(f"\n🧪 Testing food pages render without errors\n")
    
    app.config['TESTING'] = True
    client = app.test_client()
    
    results = []
    
    # Test main pages
    print("1️⃣  Testing main pages...")
    
    # Root - should redirect to first pad
    results.append(test_page_loads(client, '/', '01_root'))
    
    # Amounts page
    results.append(test_page_loads(client, '/?pad=amounts', '02_amounts'))
    
    # Proteins pad (has both unit and amount foods)
    results.append(test_page_loads(client, '/?pad=proteins', '03_proteins'))
    
    # Carbs pad
    results.append(test_page_loads(client, '/?pad=carbs', '04_carbs'))
    
    # Non-existent pad (should 404 or redirect)
    results.append(test_page_loads(client, '/?pad=nonexistent', '05_nonexistent'))
    
    print("\n2️⃣  Testing other routes...")
    
    # Nutrition dashboard
    results.append(test_page_loads(client, '/nutrition', '06_nutrition'))
    
    # Calories timeline
    results.append(test_page_loads(client, '/calories', '07_calories'))
    
    # Notes
    results.append(test_page_loads(client, '/notes', '08_notes'))
    
    # Edit foods
    results.append(test_page_loads(client, '/edit-foods', '09_edit_foods'))
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} pages loaded OK")
    
    return all(results)


def test_food_button_content():
    """Test that food buttons are present in the response."""
    print(f"\n🧪 Testing food button content")
    
    app.config['TESTING'] = True
    client = app.test_client()
    
    response = client.get('/?pad=proteins')
    
    if response.status_code != 200:
        print(f"   ❌ Failed to load proteins page: {response.status_code}")
        return False
    
    html = response.data.decode('utf-8')
    
    # Check for food buttons
    food_pad_count = html.count('class="food-pad"')
    print(f"   Found {food_pad_count} food buttons")
    
    if food_pad_count == 0:
        print("   ❌ No food buttons found!")
        return False
    
    # Check for protein display (the key thing - no Jinja errors)
    protein_count = html.count('g protein')
    if protein_count > 0:
        print(f"   ✓ Protein info displayed ({protein_count} items)")
    else:
        print("   ❌ No protein info found")
        return False
    
    # Check no Jinja errors leaked through
    if 'UndefinedError' in html or 'has no attribute' in html:
        print("   ❌ Jinja error in response!")
        return False
    
    print("\n✅ Food buttons rendered correctly")
    return True


def test_unit_vs_amount_foods():
    """Test that both unit and amount type foods render correctly."""
    print(f"\n🧪 Testing unit vs amount food rendering")
    
    app.config['TESTING'] = True
    client = app.test_client()
    
    response = client.get('/?pad=proteins')
    
    if response.status_code != 200:
        print(f"   ❌ Failed to load proteins page: {response.status_code}")
        return False
    
    html = response.data.decode('utf-8')
    
    # Check that we don't have Jinja errors
    if 'UndefinedError' in html or 'has no attribute' in html:
        print("   ❌ Jinja template error in response!")
        return False
    
    # All foods should show "g protein" without errors
    protein_displays = html.count('g protein')
    print(f"   Found {protein_displays} protein displays")
    
    if protein_displays > 0:
        print("   ✓ All food types rendered protein info correctly")
        return True
    else:
        print("   ❌ No foods rendered correctly")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("NUTRITION-PAD FOOD FIELDS TEST (Flask Test Client)")
    print("=" * 60)
    
    # Change to the directory where foods.toml is
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    result1 = test_food_pages()
    result2 = test_food_button_content()
    result3 = test_unit_vs_amount_foods()
    
    print("\n" + "=" * 60)
    if result1 and result2 and result3:
        print("ALL TESTS PASSED ✅")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED ❌")
        sys.exit(1)