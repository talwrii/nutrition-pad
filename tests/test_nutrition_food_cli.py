#!/usr/bin/env python3
"""
Tests for nutrition-food CLI tool

Ensures the CLI can search and list foods without breaking.
"""

import sys
import os
import json
import tempfile
from io import StringIO

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nutrition_pad.food_cli import get_all_foods_from_config, load_local_config, find_food_by_id
from nutrition_pad.data import load_config


def test_list_all_foods():
    """Test that listing all foods works"""
    print("\n🧪 Test: List all foods")

    try:
        config = load_local_config()
        foods = get_all_foods_from_config(config)
        assert isinstance(foods, list), "Should return a list"
        assert len(foods) > 0, "Should have at least one food"

        # Check structure of first food
        if foods:
            food = foods[0]
            assert 'name' in food, "Food should have name"
            assert 'pad_key' in food, "Food should have pad_key"
            assert 'food_key' in food, "Food should have food_key"

        print(f"  ✓ Found {len(foods)} foods")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_search_foods():
    """Test that searching foods works"""
    print("\n🧪 Test: Search foods")

    try:
        config = load_local_config()
        all_foods = get_all_foods_from_config(config)

        # Search for common food name (case insensitive)
        query = "chicken"
        results = [f for f in all_foods if query.lower() in f['name'].lower()]

        print(f"  ✓ Search for '{query}' returned {len(results)} results")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_search_foods_case_insensitive():
    """Test that search is case insensitive"""
    print("\n🧪 Test: Search is case insensitive")

    try:
        config = load_local_config()
        all_foods = get_all_foods_from_config(config)

        # Search for eggs in different cases
        results_lower = [f for f in all_foods if "egg" in f['name'].lower()]
        results_upper = [f for f in all_foods if "EGG".lower() in f['name'].lower()]
        results_mixed = [f for f in all_foods if "Egg".lower() in f['name'].lower()]

        assert len(results_lower) == len(results_upper) == len(results_mixed), \
            "Case insensitive search should return same results"

        print(f"  ✓ Case insensitive search works")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_config_loads():
    """Test that config loads properly"""
    print("\n🧪 Test: Config loads")

    try:
        config = load_config()
        assert 'pads' in config, "Config should have 'pads'"
        assert len(config['pads']) > 0, "Should have at least one pad"

        print(f"  ✓ Config has {len(config['pads'])} pads")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("  NUTRITION-FOOD CLI TESTS")
    print("="*60)

    tests = [
        test_config_loads,
        test_list_all_foods,
        test_search_foods,
        test_search_foods_case_insensitive,
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
