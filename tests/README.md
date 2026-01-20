# Nutrition-Pad Tests

Tests to prevent regressions in critical functionality.

## Running Tests

### Quick test (food CLI only, no Flask required):
```bash
python3 tests/test_nutrition_food_cli.py
```

### All tests (requires Flask):
```bash
# Install dependencies first
pip install flask toml

# Run all tests
./tests/run_all_tests.sh
```

Or run individually:
```bash
python3 tests/test_nutrition_food_cli.py
python3 tests/test_nutrition_unknown_cli.py
python3 tests/test_api_routes.py
```

## What Gets Tested

### test_nutrition_food_cli.py
- Config loading
- Listing all foods
- Searching foods
- Case-insensitive search

### test_nutrition_unknown_cli.py (requires Flask)
- `/api/resolve-unknown` endpoint exists
- Parameter validation
- Invalid food rejection
- Successfully resolving unknown entries

### test_api_routes.py (requires Flask)
- All critical routes exist and don't crash:
  - `/` - Main page
  - `/today` - Today's log
  - `/nutrition` - Nutrition dashboard
  - `/edit-foods` - Edit foods page
  - `/log` - Log food entry (POST)
  - `/delete-entry` - Delete entry (POST)
  - `/api/foods` - List foods API
  - `/api/foods/search` - Search foods API
  - `/api/resolve-unknown` - Resolve unknown API (POST)
- CSS compatibility for Nexus 10:
  - Uses float-based layout (not `aspect-ratio`)
  - Has `food-btn` or `food-grid` classes

## Why These Tests?

These tests prevent regressions like:
1. Routes accidentally deleted during refactoring
2. CSS changes breaking old Android browsers (Nexus 10)
3. CLI tools breaking due to function renames
4. API endpoints changing behavior unexpectedly
