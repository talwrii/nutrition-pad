#!/usr/bin/env python3
"""
Main Flask application for nutrition-pad
"""
import os
import sys
import json
import argparse
from flask import Flask, render_template_string, request, jsonify, send_from_directory

# Import our modules
from .data import (
    load_config, ensure_logs_directory, save_food_entry,
    calculate_nutrition_stats, calculate_time_since_last_ate,
    load_today_log, get_all_pads, validate_food_request,
    LOGS_DIR, backfill_all_logs
)
from .polling import register_polling_routes, get_current_amount, mark_updated
from .calories import register_calories_routes
from .notes import register_notes_routes
from .styles import register_styles_routes
from .amounts import render_amounts_tab, get_amounts_javascript

# Create Flask app
app = Flask(__name__)

# Ensure logs directory exists
ensure_logs_directory()

# Backfill IDs for historic entries on startup
backfill_all_logs()

# Register routes from other modules
register_polling_routes(app)
register_calories_routes(app)
register_notes_routes(app)
register_styles_routes(app)

# Main page template
MAIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{{ pad_name if pad_name else 'Food Pads' }}</title>
    <link rel="stylesheet" href="/static/base.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        /* Food pad grid styles */
        .food-pads {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            padding: 20px;
            padding-bottom: 100px;
        }
        .food-pad {
            aspect-ratio: 1;
            border-radius: 20px;
            border: none;
            color: white;
            font-size: 1.2em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            gap: 5px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            min-width: 44px;
            min-height: 44px;
        }
        .food-pad:active {
            transform: scale(0.95);
        }
        .food-name {
            font-size: 1.2em;
        }
        .food-nutrition {
            font-size: 0.8em;
            opacity: 0.9;
        }
    </style>
    <script>
        {{ amounts_js | safe }}
        {{ polling_js | safe }}
        
        function logFood(padKey, foodKey) {
            var amount = getCurrentAmount();
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/log-food', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    window.location.reload();
                }
            };
            xhr.send(JSON.stringify({pad: padKey, food: foodKey, amount: amount}));
        }
        
        window.onload = function() {
            if (typeof initializeAmountsTab === 'function') {
                initializeAmountsTab();
            }
            setDebugMode(false);
            startLongPolling();
        };
    </script>
</head>
<body>
    <div class="header">
        <div class="header-icons">
            <a href="/" class="food-link" title="Food Pads">🍎</a>
            <a href="/?pad=amounts" class="amounts-link" title="Set Amount">📏</a>
            <a href="/notes" class="notes-link" title="Food Notes">📝</a>
            <a href="/edit-foods" class="settings-cog" title="Edit Foods Configuration">⚙️</a>
        </div>
        <h1>{{ pad_name if pad_name else 'Food Pads' }}</h1>
        <div class="current-amount">{{ current_amount }}g</div>
        <div class="item-count">{{ item_count }} items logged today</div>
    </div>
    
    {% if show_amounts %}
        {{ amounts_content | safe }}
    {% else %}
        <div class="food-pads">
            {% for food_key, food in foods.items() %}
            <button class="food-pad" 
                    style="background: {{ food.color if food.color else '#667eea' }};"
                    onclick="logFood('{{ pad_key }}', '{{ food_key }}')">
                <div class="food-name">{{ food.name }}</div>
                <div class="food-nutrition">{{ food.protein_per_gram * 100 if food.type != 'unit' else food.protein }}g protein</div>
            </button>
            {% endfor %}
        </div>
    {% endif %}
    
    <div class="bottom-nav">
        <button class="bottom-nav-btn" onclick="window.location.href='/nutrition'">
            Dashboard
        </button>
        <button class="bottom-nav-btn" onclick="window.location.href='/calories'" style="background: linear-gradient(135deg, #4ecdc4, #00d4ff);">
            Timeline
        </button>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page - show food pads or amounts tab"""
    config = load_config()
    pad_param = request.args.get('pad', '')
    
    # Show amounts tab
    if pad_param == 'amounts':
        current_amount = get_current_amount()
        amounts_content = render_amounts_tab(current_amount)
        amounts_js = get_amounts_javascript(current_amount)
        
        from .polling import get_polling_javascript
        polling_js = get_polling_javascript()
        
        from .data import calculate_daily_item_count
        item_count = calculate_daily_item_count()
        
        return render_template_string(
            MAIN_HTML,
            show_amounts=True,
            amounts_content=amounts_content,
            amounts_js=amounts_js,
            polling_js=polling_js,
            current_amount=current_amount,
            item_count=item_count,
            pad_name="Set Amount"
        )
    
    # Show food pad
    pads = config.get('pads', {})
    
    # If no pad specified or invalid, show first non-amounts pad
    if not pad_param or pad_param not in pads:
        for key in pads.keys():
            if key != 'amounts':
                pad_param = key
                break
    
    if pad_param not in pads:
        return "No food pads configured", 404
    
    pad = pads[pad_param]
    foods = pad.get('foods', {})
    
    current_amount = get_current_amount()
    amounts_js = get_amounts_javascript(current_amount)
    
    from .polling import get_polling_javascript
    polling_js = get_polling_javascript()
    
    from .data import calculate_daily_item_count
    item_count = calculate_daily_item_count()
    
    return render_template_string(
        MAIN_HTML,
        show_amounts=False,
        foods=foods,
        pad_key=pad_param,
        pad_name=pad.get('name', pad_param),
        amounts_js=amounts_js,
        polling_js=polling_js,
        current_amount=current_amount,
        item_count=item_count
    )

@app.route('/log-food', methods=['POST'])
def log_food():
    """Log a food entry"""
    data = request.json
    pad_key = data.get('pad')
    food_key = data.get('food')
    amount = data.get('amount', 100)
    
    valid, food_data_or_error = validate_food_request(pad_key, food_key)
    if not valid:
        return jsonify({'error': food_data_or_error}), 400
    
    food_data = food_data_or_error
    entry = save_food_entry(pad_key, food_key, food_data, amount)
    
    mark_updated()
    
    return jsonify({'success': True, 'entry': entry})

@app.route('/nutrition')
def nutrition_dashboard():
    """Nutrition statistics dashboard"""
    stats = calculate_nutrition_stats()
    time_since = calculate_time_since_last_ate()
    
    # Format time since last ate
    if time_since:
        minutes = time_since['minutes']
        hours = minutes // 60
        mins = minutes % 60
        time_display = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
    else:
        time_display = "--"
    
    HTML = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Nutrition Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="/static/base.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    </head>
    <body>
        <div class="header">
            <div class="header-icons">
                <a href="/" class="food-link">🍎</a>
                <a href="/notes" class="notes-link">📝</a>
                <a href="/edit-foods" class="settings-cog">⚙️</a>
            </div>
            <h1>Nutrition Dashboard</h1>
        </div>
        
        <div class="nutrition-stats">
            <div class="stat-cards">
                <div class="stat-card">
                    <div class="stat-value calories">{{ stats.total_calories }}</div>
                    <div class="stat-label">Calories</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value protein">{{ stats.total_protein }}g</div>
                    <div class="stat-label">Protein</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value fiber">{{ stats.total_fiber }}g</div>
                    <div class="stat-label">Fiber</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value ratio">{{ stats.avg_ratio }}</div>
                    <div class="stat-label">kcal/g protein</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value time-since">{{ time_display }}</div>
                    <div class="stat-label">Since Last Ate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value cal-hour">{{ stats.cal_per_hour }}</div>
                    <div class="stat-label">cal/hour</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value prot-hour">{{ stats.protein_per_hour }}</div>
                    <div class="stat-label">protein/hour</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value fiber-ratio">{{ stats.kcal_per_fiber }}</div>
                    <div class="stat-label">kcal/g fiber</div>
                </div>
            </div>
        </div>
        
        <div class="bottom-nav">
            <button class="bottom-nav-btn" onclick="window.location.href='/'">
                Back to Food Pads
            </button>
            <button class="bottom-nav-btn" onclick="window.location.href='/calories'" style="background: linear-gradient(135deg, #4ecdc4, #00d4ff);">
                Timeline
            </button>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(HTML, stats=stats, time_display=time_display)

@app.route('/edit-foods')
def edit_foods():
    """Food configuration editor"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Edit Foods</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="/static/base.css">
    </head>
    <body>
        <div class="header">
            <h1>Food Editor</h1>
        </div>
        <div style="padding: 20px; text-align: center;">
            <p>Edit foods.toml file directly on the server</p>
            <p>Path: foods.toml</p>
        </div>
        <div class="bottom-nav">
            <button class="bottom-nav-btn" onclick="window.location.href='/'">
                Back to Food Pads
            </button>
        </div>
    </body>
    </html>
    """

@app.route('/api/resolve-unknown', methods=['POST'])
def api_resolve_unknown():
    """API endpoint to resolve unknown food entries"""
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    entry_ids = data.get('entry_ids', [])
    food_key = data.get('food_key')
    
    if not entry_ids or not food_key:
        return jsonify({'success': False, 'error': 'Missing entry_ids or food_key'}), 400
    
    # Find the food in the config
    pad_key = None
    food_data = None
    
    pads = get_all_pads()
    for pk, pad_data in pads.items():
        if pk == 'amounts':
            continue
        foods = pad_data.get('foods', {})
        if food_key in foods:
            pad_key = pk
            food_data = foods[food_key]
            break
    
    if not food_data:
        return jsonify({'success': False, 'error': f'Food "{food_key}" not found'}), 404
    
    # Find and update entries in log files
    updated_count = 0
    updated_entries = []
    
    for filename in sorted(os.listdir(LOGS_DIR), reverse=True):
        if not filename.endswith('.json') or filename.endswith('_notes.json'):
            continue
        
        filepath = os.path.join(LOGS_DIR, filename)
        
        try:
            with open(filepath, 'r') as f:
                entries = json.load(f)
        except:
            continue
        
        modified = False
        for entry in entries:
            if entry.get('id') in entry_ids:
                # Resolve the entry
                amount = entry.get('amount', 100)
                
                if food_data.get('type') == 'unit':
                    calories = food_data.get('calories', 0)
                    protein = food_data.get('protein', 0)
                    fiber = food_data.get('fiber', 0)
                    amount_display = "1 unit"
                else:
                    calories = food_data.get('calories_per_gram', 0) * amount
                    protein = food_data.get('protein_per_gram', 0) * amount
                    fiber = food_data.get('fiber_per_gram', 0) * amount
                    amount_display = f"{amount}g"
                
                entry['pad'] = pad_key
                entry['food'] = food_key
                entry['name'] = food_data.get('name', food_key)
                entry['calories'] = round(calories, 1)
                entry['protein'] = round(protein, 1)
                entry['fiber'] = round(fiber, 1)
                entry['amount_display'] = amount_display
                
                modified = True
                updated_count += 1
                updated_entries.append({
                    'id': entry['id'],
                    'date': filename.replace('.json', ''),
                    'calories': entry['calories'],
                    'protein': entry['protein']
                })
        
        if modified:
            with open(filepath, 'w') as f:
                json.dump(entries, f, indent=2)
            
            # Trigger update notification
            mark_updated("resolve_unknown")
    
    return jsonify({
        'success': True,
        'updated_count': updated_count,
        'total_requested': len(entry_ids),
        'updated_entries': updated_entries,
        'food_name': food_data.get('name', food_key)
    })

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Nutrition Pad Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()