#!/bin/bash
# Run all tests for nutrition-pad

set -e

echo "Running all nutrition-pad tests..."
echo ""

python3 tests/test_nutrition_food_cli.py
python3 tests/test_nutrition_unknown_cli.py
python3 tests/test_api_routes.py
python3 tests/test_entries_api.py
python3 tests/test_meals.py

echo ""
echo "✅ All tests completed!"
