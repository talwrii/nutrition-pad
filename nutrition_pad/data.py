"""
Food entry database operations and nutrition calculations.
Handles daily logs, configuration loading, and nutrition statistics.
"""
import json
import os
import toml
from datetime import datetime, date

CONFIG_FILE = 'foods.toml'
LOGS_DIR = 'daily_logs'

# --- DEFAULT CONFIG (unit vs amount foods) ---
DEFAULT_CONFIG = """[pads.proteins]
name = "Proteins"

[pads.proteins.foods.unknown_amount]
name = "Unknown (amount)"
type = "amount"  # needs amount in grams
calories_per_gram = 0.0  # PLACEHOLDER - look up actual values
protein_per_gram = 0.0   # PLACEHOLDER - look up actual values

[pads.proteins.foods.unknown_unit]
name = "Unknown (unit)"
type = "unit"  # fixed serving
calories = 0  # PLACEHOLDER - look up actual values
protein = 0   # PLACEHOLDER - look up actual values

[pads.proteins.foods.chicken_breast]
name = "Chicken Breast"
type = "amount"  # needs amount in grams
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
type = "unit"  # fixed serving
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

[pads.vegetables.foods.carrots]
name = "Carrots"
type = "amount"
calories_per_gram = 0.41
protein_per_gram = 0.01

[pads.carbs]
name = "Carbs"

[pads.carbs.foods.rice]
name = "Rice (cooked)"
type = "amount"
calories_per_gram = 1.30
protein_per_gram = 0.03

[pads.carbs.foods.bread]
name = "Bread (1 slice)"
type = "unit"
calories = 80
protein = 3

[pads.carbs.foods.pasta]
name = "Pasta (cooked)"
type = "amount"
calories_per_gram = 1.31
protein_per_gram = 0.05

[pads.quick]
name = "Quick Add"

[pads.quick.foods.coffee]
name = "Black Coffee"
type = "unit"
calories = 5
protein = 0

[pads.quick.foods.water]
name = "Water"
type = "unit"
calories = 0
protein = 0

[pads.quick.foods.tea]
name = "Tea"
type = "unit"
calories = 2
protein = 0

[pads.amounts]
name = "Set Amount"
"""

def parse_scale(scale_str):
    """Parse scale expressions like '3/4', '2*3', '1/2/3' into float"""
    if not scale_str or scale_str == "1" or scale_str == 1:
        return 1.0
    
    # If it's already a number, convert directly
    if isinstance(scale_str, (int, float)):
        return float(scale_str)
    
    try:
        # Convert to string if needed and strip whitespace
        scale_str = str(scale_str).strip()
        
        # For safety, only allow numbers, operators, parentheses, and decimals
        allowed_chars = set('0123456789./*+-()')
        if not all(c in allowed_chars or c.isspace() for c in scale_str):
            raise ValueError("Invalid characters in scale expression")
        
        # Use eval with restricted globals for safety
        result = eval(scale_str, {"__builtins__": {}}, {})
        
        if not isinstance(result, (int, float)) or result <= 0:
            raise ValueError("Scale must be a positive number")
            
        return float(result)
    except Exception as e:
        print(f"Error parsing scale '{scale_str}': {e}")
        return 1.0  # Default to no scaling on error

def ensure_logs_directory():
    """Create logs directory if it doesn't exist"""
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

def load_config():
    """Load TOML config file, create default if not exists"""
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            f.write(DEFAULT_CONFIG)
    
    with open(CONFIG_FILE, 'r') as f:
        return toml.load(f)

def get_today_log_file():
    """Get path to today's log file"""
    today = date.today().strftime('%Y-%m-%d')
    return os.path.join(LOGS_DIR, f'{today}.json')

def load_today_log():
    """Load today's food log"""
    log_file = get_today_log_file()
    if not os.path.exists(log_file):
        return []
    
    with open(log_file, 'r') as f:
        return json.load(f)

def save_food_entry(pad_key, food_key, food_data, amount=None):
    """Save a food entry to today's log with specified amount or unit, applying scale if present"""
    log_file = get_today_log_file()
    log = load_today_log()
    
    # Parse scale factor from food data
    scale = parse_scale(food_data.get('scale', 1.0))
    
    if food_data.get('type') == 'unit':
        # Unit food - apply scale to fixed calories/protein
        base_calories = food_data['calories']
        base_protein = food_data.get('protein', 0)
        calories = base_calories * scale
        protein = base_protein * scale
        amount = scale  # Store the scale factor as amount for units
        if scale == 1.0:
            amount_display = "1 unit"
        else:
            amount_display = f"{scale} units"
    else:
        # Amount food - apply scale to the amount, then calculate nutrition
        if amount is None:
            amount = 100  # Default fallback
        
        effective_amount = amount * scale
        calories = food_data['calories_per_gram'] * effective_amount
        protein = food_data.get('protein_per_gram', 0) * effective_amount
        amount_display = f"{effective_amount}g"
        amount = effective_amount  # Store the effective amount
    
    entry = {
        'time': datetime.now().strftime('%H:%M'),
        'pad': pad_key,
        'food': food_key,
        'name': food_data['name'],
        'amount': amount,
        'amount_display': amount_display,
        'calories': round(calories, 1),
        'protein': round(protein, 1),
        'scale': scale if scale != 1.0 else None,  # Only store scale if not 1.0
        'timestamp': datetime.now().isoformat()
    }
    
    log.append(entry)
    
    with open(log_file, 'w') as f:
        json.dump(log, f, indent=2)

def calculate_daily_total():
    """Calculate total protein for today"""
    log = load_today_log()
    return round(sum(entry.get('protein', 0) for entry in log), 1)

def calculate_daily_item_count():
    """Calculate total items logged for today"""
    log = load_today_log()
    return len(log)

def calculate_nutrition_stats():
    """Calculate comprehensive nutrition stats for today"""
    log = load_today_log()
    
    if not log:
        return {
            'total_calories': 0,
            'total_protein': 0,
            'avg_ratio': '0.00'
        }
    
    total_calories = sum(entry.get('calories', 0) for entry in log)
    total_protein = sum(entry.get('protein', 0) for entry in log)
    
    avg_ratio = total_protein / total_calories if total_calories > 0 else 0
    
    return {
        'total_calories': round(total_calories),
        'total_protein': round(total_protein, 1),
        'avg_ratio': f"{avg_ratio:.2f}"
    }

def validate_food_request(pad_key, food_key):
    """Validate that a pad and food key exist in the config"""
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
    pads = config.get('pads', {})
    
    # Automatically inject unknown entries into the first available pad
    if pads:
        first_pad_key = list(pads.keys())[0]
        
        # Add unknown entries if they don't already exist
        if 'unknown_amount' not in pads[first_pad_key].get('foods', {}):
            if 'foods' not in pads[first_pad_key]:
                pads[first_pad_key]['foods'] = {}
            
            pads[first_pad_key]['foods']['unknown_amount'] = {
                'name': 'Unknown (amount)',
                'type': 'amount',
                'calories_per_gram': 0.0,  # PLACEHOLDER - look up actual values
                'protein_per_gram': 0.0    # PLACEHOLDER - look up actual values
            }
        
        if 'unknown_unit' not in pads[first_pad_key].get('foods', {}):
            if 'foods' not in pads[first_pad_key]:
                pads[first_pad_key]['foods'] = {}
                
            pads[first_pad_key]['foods']['unknown_unit'] = {
                'name': 'Unknown (unit)',
                'type': 'unit', 
                'calories': 0,    # PLACEHOLDER - look up actual values
                'protein': 0      # PLACEHOLDER - look up actual values
            }
    
    return pads