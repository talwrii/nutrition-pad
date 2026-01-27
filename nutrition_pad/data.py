"""
Data module for nutrition pad application.
Handles daily logs, configuration loading, and nutrition statistics.
"""

import json
import os
import toml
import random
import string
from datetime import datetime, date, timedelta

CONFIG_FILE = 'foods.toml'
LOGS_DIR = 'daily_logs'

# Hardcoded unknown food definitions
UNKNOWN_FOODS = {
    'amount': {
        'name': 'Unknown (amount)',
        'type': 'amount',
        'calories_per_gram': 0.0,
        'protein_per_gram': 0.0,
        'fiber_per_gram': 0.0
    },
    'unit': {
        'name': 'Unknown (unit)',
        'type': 'unit',
        'calories': 0,
        'protein': 0,
        'fiber': 0
    }
}

# --- DEFAULT CONFIG (unit vs amount foods) ---
DEFAULT_CONFIG = """[pads.proteins]
name = "Proteins"

[pads.proteins.foods.unknown_amount]
name = "Unknown (amount)"
type = "amount"
calories_per_gram = 0.0
protein_per_gram = 0.0

[pads.proteins.foods.unknown_unit]
name = "Unknown (unit)"
type = "unit"
calories = 0
protein = 0

[pads.proteins.foods.chicken_breast]
name = "Chicken Breast"
type = "amount"
calories_per_gram = 1.46
protein_per_gram = 0.27

[pads.proteins.foods.ground_beef]
name = "Ground Beef"
type = "amount"
calories_per_gram = 2.50
protein_per_gram = 0.20

[pads.proteins.foods.salmon]
name = "Salmon"
type = "amount"
calories_per_gram = 1.77
protein_per_gram = 0.25

[pads.proteins.foods.eggs]
name = "Eggs (2 large)"
type = "unit"
calories = 140
protein = 12

[pads.vegetables]
name = "Vegetables"

[pads.vegetables.foods.broccoli]
name = "Broccoli"
type = "amount"
calories_per_gram = 0.34
protein_per_gram = 0.03

[pads.vegetables.foods.spinach]
name = "Spinach"
type = "amount"
calories_per_gram = 0.23
protein_per_gram = 0.03

[pads.carbs]
name = "Carbs"

[pads.carbs.foods.rice]
name = "Rice (cooked)"
type = "amount"
calories_per_gram = 1.30
protein_per_gram = 0.027

[pads.carbs.foods.oatmeal]
name = "Oatmeal (cooked)"
type = "amount"
calories_per_gram = 0.625
protein_per_gram = 0.021
"""

def generate_entry_id():
    """Generate a unique ID for a food entry"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{timestamp}{suffix}"

def ensure_logs_directory():
    """Create logs directory if it doesn't exist"""
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

def validate_config(config):
    """Validate that all foods have required fields"""
    errors = []
    
    pads = config.get('pads', {})
    for pad_key, pad_data in pads.items():
        if pad_key == 'amounts':
            continue
        
        foods = pad_data.get('foods', {})
        for food_key, food_data in foods.items():
            # Check type is specified
            if 'type' not in food_data:
                errors.append(f"[{pad_key}/{food_key}] Missing 'type' field (must be 'unit' or 'amount')")
                continue
            
            food_type = food_data.get('type')
            if food_type not in ('unit', 'amount'):
                errors.append(f"[{pad_key}/{food_key}] Invalid type '{food_type}' (must be 'unit' or 'amount')")
                continue
            
            # Check required fields for each type
            if food_type == 'unit':
                if 'calories' not in food_data:
                    errors.append(f"[{pad_key}/{food_key}] Unit food missing 'calories'")
                if 'protein' not in food_data:
                    errors.append(f"[{pad_key}/{food_key}] Unit food missing 'protein'")
            else:  # amount
                if 'calories_per_gram' not in food_data:
                    errors.append(f"[{pad_key}/{food_key}] Amount food missing 'calories_per_gram'")
                if 'protein_per_gram' not in food_data:
                    errors.append(f"[{pad_key}/{food_key}] Amount food missing 'protein_per_gram'")
    
    if errors:
        error_msg = "Invalid foods.toml configuration:\n  " + "\n  ".join(errors)
        raise ValueError(error_msg)


def load_config():
    """Load TOML config file, create default if not exists"""
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            f.write(DEFAULT_CONFIG)
    
    with open(CONFIG_FILE, 'r') as f:
        config = toml.load(f)
    
    validate_config(config)
    return config

def get_today_log_file():
    """Get path to today's log file"""
    today = date.today().strftime('%Y-%m-%d')
    return os.path.join(LOGS_DIR, f'{today}.json')

def load_today_log():
    """Load today's food log"""
    log_file = get_today_log_file()
    
    if not os.path.exists(log_file):
        return []
    
    try:
        with open(log_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def backfill_entry_ids(entries):
    """Add IDs to entries that don't have them. Returns True if any were added."""
    modified = False
    for entry in entries:
        if 'id' not in entry or not entry['id']:
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
    return modified

def backfill_all_logs():
    """Backfill IDs for all historic log files. Returns count of files modified."""
    if not os.path.exists(LOGS_DIR):
        return 0
    
    files_modified = 0
    
    for filename in os.listdir(LOGS_DIR):
        if filename.endswith('.json') and not filename.endswith('_notes.json'):
            filepath = os.path.join(LOGS_DIR, filename)
            try:
                with open(filepath, 'r') as f:
                    entries = json.load(f)
                
                if backfill_entry_ids(entries):
                    with open(filepath, 'w') as f:
                        json.dump(entries, f, indent=2)
                    files_modified += 1
                    
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not process {filename}: {e}")
                continue
    
    return files_modified

def save_food_entry(pad_key, food_key, food_data, amount=None):
    """Save a food entry to today's log with specified amount or unit"""
    log_file = get_today_log_file()
    
    entries = load_today_log()
    backfill_entry_ids(entries)
    
    now = datetime.now()
    timestamp = now.isoformat()
    time_str = now.strftime('%H:%M')
    
    entry_id = generate_entry_id()
    
    scale = food_data.get('scale', 1.0)
    
    if food_data.get('type') == 'unit':
        calories = food_data.get('calories', 0) * scale
        protein = food_data.get('protein', 0) * scale
        fiber = food_data.get('fiber', 0) * scale
        amount_display = "1 unit"
        entry_amount = 1
    else:
        if amount is None:
            amount = 100
        calories = food_data.get('calories_per_gram', 0) * amount * scale
        protein = food_data.get('protein_per_gram', 0) * amount * scale
        fiber = food_data.get('fiber_per_gram', 0) * amount * scale
        amount_display = f"{amount}g"
        entry_amount = amount
    
    entry = {
        'id': entry_id,
        'time': time_str,
        'pad': pad_key,
        'food': food_key,
        'name': food_data.get('name', food_key),
        'amount': entry_amount,
        'amount_display': amount_display,
        'calories': round(calories, 1),
        'protein': round(protein, 1),
        'fiber': round(fiber, 1),
        'timestamp': timestamp
    }
    
    entries.append(entry)
    
    with open(log_file, 'w') as f:
        json.dump(entries, f, indent=2)
    
    return entry

def calculate_daily_total():
    """Calculate total protein for today"""
    entries = load_today_log()
    return sum(entry.get('protein', 0) for entry in entries)

def calculate_daily_item_count():
    """Calculate total items logged for today"""
    return len(load_today_log())

def calculate_nutrition_stats():
    """Calculate comprehensive nutrition stats for today"""
    log = load_today_log()
    
    if not log:
        return {
            'total_calories': 0,
            'total_protein': 0,
            'total_fiber': 0,
            'avg_ratio': '--',
            'cal_per_hour': '--',
            'protein_per_hour': '--',
            'kcal_per_fiber': '--'
        }
    
    total_calories = sum(entry.get('calories', 0) for entry in log)
    total_protein = sum(entry.get('protein', 0) for entry in log)
    total_fiber = sum(entry.get('fiber', 0) for entry in log)
    
    avg_ratio = total_calories / total_protein if total_protein > 0 else 0
    kcal_per_fiber = total_calories / total_fiber if total_fiber > 0 else 0
    
    now = datetime.now()
    five_am = now.replace(hour=5, minute=0, second=0, microsecond=0)
    if now < five_am:
        five_am = five_am.replace(day=five_am.day - 1)
    
    hours_since_5am = (now - five_am).total_seconds() / 3600
    hours_since_5am = max(hours_since_5am, 0.1)
    
    cal_per_hour = total_calories / hours_since_5am
    protein_per_hour = total_protein / hours_since_5am
    
    return {
        'total_calories': round(total_calories),
        'total_protein': round(total_protein, 1),
        'total_fiber': round(total_fiber, 1),
        'avg_ratio': f"{avg_ratio:.1f}",
        'cal_per_hour': f"{cal_per_hour:.0f}",
        'protein_per_hour': f"{protein_per_hour:.1f}",
        'kcal_per_fiber': f"{kcal_per_fiber:.0f}" if total_fiber > 0 else '--'
    }

def calculate_time_since_last_ate():
    """Calculate time since last food entry (excludes drinks/items under 20 kcal)"""
    entries = load_today_log()
    food_entries = [e for e in entries if e.get('calories', 0) >= 20]

    # If no food today, check previous days
    if not food_entries:
        today = date.today()
        for days_ago in range(1, 8):  # Check up to a week back
            check_date = today - timedelta(days=days_ago)
            log_file = os.path.join(LOGS_DIR, f'{check_date.strftime("%Y-%m-%d")}.json')
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        old_entries = json.load(f)
                    food_entries = [e for e in old_entries if e.get('calories', 0) >= 20]
                    if food_entries:
                        break
                except (json.JSONDecodeError, IOError):
                    continue

    if not food_entries:
        return None

    last_entry = food_entries[-1]
    timestamp_str = last_entry.get('timestamp')
    if not timestamp_str:
        return None

    try:
        last_time = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        delta = now - last_time
        total_minutes = int(delta.total_seconds() / 60)
        return {
            'minutes': total_minutes,
            'timestamp': timestamp_str
        }
    except (ValueError, TypeError):
        return None

def validate_food_request(pad_key, food_key):
    """Validate that a pad and food key exist in the config"""
    if pad_key == '_unknown' and food_key in UNKNOWN_FOODS:
        return True, UNKNOWN_FOODS[food_key]
    
    config = load_config()
    
    if pad_key not in config.get('pads', {}):
        return False, 'Invalid pad'
        
    if food_key not in config['pads'][pad_key].get('foods', {}):
        return False, 'Invalid food'
    
    return True, config['pads'][pad_key]['foods'][food_key]

def get_food_data(pad_key, food_key):
    """Get food data for a specific pad and food key"""
    config = load_config()
    return config['pads'][pad_key]['foods'][food_key]

def get_all_pads():
    """Get all pads from the configuration"""
    config = load_config()
    return config.get('pads', {})
