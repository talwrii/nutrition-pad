from flask import Flask, render_template_string, request, redirect, url_for, jsonify
from datetime import datetime, date
import os
import json
import argparse
import toml
import time
import threading

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Long polling update tracking
last_update = time.time()
update_lock = threading.Lock()
update_event = threading.Event()

CONFIG_FILE = 'foods.toml'
LOGS_DIR = 'daily_logs'

# Create logs directory if it doesn't exist
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# --- DEFAULT CONFIG ---
DEFAULT_CONFIG = """[pads.proteins]
name = "Proteins"

[pads.proteins.foods.chicken_breast]
name = "Chicken Breast (4oz)"
calories = 165
protein = 31

[pads.proteins.foods.ground_beef]
name = "Ground Beef (4oz)"
calories = 280
protein = 22

[pads.proteins.foods.salmon]
name = "Salmon (4oz)"
calories = 200
protein = 28

[pads.proteins.foods.eggs]
name = "Eggs (2 large)"
calories = 140
protein = 12

[pads.vegetables]
name = "Vegetables"

[pads.vegetables.foods.broccoli]
name = "Broccoli (1 cup)"
calories = 25
protein = 3

[pads.vegetables.foods.spinach]
name = "Spinach (1 cup)"
calories = 7
protein = 1

[pads.vegetables.foods.carrots]
name = "Carrots (1 cup)"
calories = 50
protein = 1

[pads.carbs]
name = "Carbs"

[pads.carbs.foods.rice]
name = "Rice (1 cup)"
calories = 200
protein = 4

[pads.carbs.foods.bread]
name = "Bread (1 slice)"
calories = 80
protein = 3

[pads.carbs.foods.pasta]
name = "Pasta (1 cup)"
calories = 180
protein = 7

[pads.quick]
name = "Quick Add"

[pads.quick.foods.coffee]
name = "Black Coffee"
calories = 5
protein = 0

[pads.quick.foods.water]
name = "Water"
calories = 0
protein = 0

[pads.quick.foods.tea]
name = "Tea"
calories = 2
protein = 0
"""

# --- HTML TEMPLATES ---
HTML_INDEX = """
<!DOCTYPE html>
<html>
<head>
    <title>Food Pads</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: #fff; 
            font-family: 'SF Pro Display', -webkit-system-font, 'Segoe UI', Roboto, sans-serif;
            min-height: 100vh;
            overflow-x: hidden;
            padding-bottom: 120px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header h1 {
            font-size: 2.5em;
            font-weight: 700;
            text-align: center;
            background: linear-gradient(45deg, #00d4ff, #ff6b6b, #4ecdc4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -1px;
        }
        
        .item-count {
            text-align: center;
            margin-top: 15px;
            font-size: 1.4em;
            font-weight: 600;
            color: #4ecdc4;
            text-shadow: 0 0 20px rgba(78, 205, 196, 0.3);
        }
        
        .nav-tabs {
            display: flex;
            justify-content: center;
            margin: 30px 20px 0;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            padding: 8px;
            backdrop-filter: blur(20px);
        }
        
        .tab-btn {
            flex: 1;
            padding: 15px 20px;
            background: none;
            border: none;
            color: rgba(255, 255, 255, 0.6);
            font-size: 1.1em;
            font-weight: 600;
            border-radius: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            text-decoration: none;
            display: block;
            text-align: center;
        }
        
        .tab-btn.active {
            background: linear-gradient(135deg, #00d4ff, #4ecdc4);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0, 212, 255, 0.3);
        }
        
        .tab-btn:hover:not(.active) {
            color: white;
            background: rgba(255, 255, 255, 0.1);
        }
        
        .food-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            padding: 30px 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .food-btn {
            background: rgba(255, 255, 255, 0.08);
            border: 2px solid rgba(255, 255, 255, 0.15);
            border-radius: 20px;
            padding: 25px;
            color: white;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            backdrop-filter: blur(20px);
            position: relative;
            overflow: hidden;
            text-align: center;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        .food-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            transition: left 0.5s;
        }
        
        .food-btn:hover::before {
            left: 100%;
        }
        
        .food-btn:hover {
            transform: translateY(-8px) scale(1.02);
            border-color: #00d4ff;
            box-shadow: 0 20px 40px rgba(0, 212, 255, 0.2);
            background: rgba(0, 212, 255, 0.1);
        }
        
        .food-btn:active {
            transform: translateY(-4px) scale(0.98);
        }
        
        .food-name {
            font-size: 1.4em;
            font-weight: 700;
            margin-bottom: 8px;
            line-height: 1.2;
        }
        
        .food-calories {
            font-size: 1.1em;
            color: #00d4ff;
            font-weight: 600;
        }
        
        .no-foods {
            text-align: center;
            color: rgba(255, 255, 255, 0.5);
            font-size: 1.2em;
            margin: 50px 0;
            grid-column: 1 / -1;
        }
        
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(0, 0, 0, 0.9);
            backdrop-filter: blur(20px);
            padding: 15px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .bottom-nav-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #ff6b6b, #ffd93d);
            border: none;
            border-radius: 15px;
            color: white;
            font-size: 1.2em;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 10px;
        }
        
        .bottom-nav-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(255, 107, 107, 0.3);
        }
        
        /* Mobile optimizations */
        @media (max-width: 768px) {
            .food-grid {
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                padding: 20px 15px;
            }
            
            .food-btn {
                padding: 20px 15px;
                min-height: 100px;
            }
            
            .food-name {
                font-size: 1.1em;
            }
            
            .food-calories {
                font-size: 1em;
            }
            
            .header h1 {
                font-size: 2em;
            }
        }
    </style>
    <script>
        var lastUpdate = parseFloat(localStorage.getItem('lastUpdate') || '0');
        var isPolling = false;
        
        function logFood(padKey, foodKey) {
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/log', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.send(JSON.stringify({
                pad: padKey,
                food: foodKey
            }));
        }
        
        function poll() {
            if (isPolling) return; // Prevent multiple polls
            isPolling = true;
            
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/poll-updates?since=' + lastUpdate, true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    isPolling = false;
                    if (xhr.status === 200) {
                        try {
                            var data = JSON.parse(xhr.responseText);
                            if (data.updated && data.timestamp > lastUpdate) {
                                // Actually changed - update and reload
                                lastUpdate = data.timestamp;
                                localStorage.setItem('lastUpdate', lastUpdate.toString());
                                
                                // Update item count immediately
                                var itemCountEl = document.querySelector('.item-count');
                                if (itemCountEl) {
                                    itemCountEl.textContent = data.item_count + ' items logged today';
                                }
                                
                                // Reload to show new food entries
                                setTimeout(function() {
                                    window.location.reload();
                                }, 1000);
                                return; // Don't schedule next poll - page will reload
                            }
                        } catch (e) {}
                    }
                    // Only schedule next poll if we're not reloading
                    setTimeout(poll, 30000);
                }
            };
            xhr.send();
        }
        
        function startLongPolling() {
            poll();
        }
        
        function showTodayLog() {
            window.location.href = '/today';
        }
        
        function showNutrition() {
            window.location.href = '/nutrition';
        }
        
        // Start long polling when page loads
        if (window.addEventListener) {
            window.addEventListener('load', startLongPolling, false);
        } else if (window.attachEvent) {
            window.attachEvent('onload', startLongPolling);
        } else {
            window.onload = startLongPolling;
        }
    </script>
</head>
<body>
    <div class="header">
        <h1>Food Pads</h1>
        <div class="item-count">{{ item_count }} items logged today</div>
    </div>
    
    <div class="nav-tabs">
        {% for pad_key, pad_data in pads.items() %}
        <a class="tab-btn {% if pad_key == current_pad %}active{% endif %}" 
           href="/?pad={{ pad_key }}">
            {{ pad_data.name }}
        </a>
        {% endfor %}
    </div>
    
    <div id="food-grid" class="food-grid">
        {% if current_pad_data and current_pad_data.foods %}
            {% for food_key, food in current_pad_data.foods.items() %}
            <div class="food-btn" 
                 onclick="logFood('{{ current_pad }}', '{{ food_key }}')">
                <div class="food-name">{{ food.name }}</div>
                <div class="food-calories">{% if food.calories > 0 %}{{ "%.2f"|format(food.protein / food.calories) }}{% else %}0.00{% endif %} p/cal</div>
            </div>
            {% endfor %}
        {% else %}
            <div class="no-foods">No foods in this pad</div>
        {% endif %}
    </div>
    
    <div class="bottom-nav">
        <button class="bottom-nav-btn" onclick="showTodayLog()">
            View Today's Log
        </button>
        <button class="bottom-nav-btn" onclick="showNutrition()" style="background: linear-gradient(135deg, #4ecdc4, #00d4ff);">
            Nutrition Dashboard
        </button>
    </div>
</body>
</html>
"""

HTML_TODAY = """
<!DOCTYPE html>
<html>
<head>
    <title>Today's Log</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: #fff; 
            font-family: 'SF Pro Display', -webkit-system-font, 'Segoe UI', Roboto, sans-serif;
            min-height: 100vh;
            padding-bottom: 80px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            font-weight: 700;
            background: linear-gradient(45deg, #00d4ff, #ff6b6b, #4ecdc4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -1px;
        }
        
        .total-protein {
            font-size: 2em;
            margin-top: 15px;
            color: #00d4ff;
            font-weight: 700;
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        }
        
        .log-container {
            max-width: 800px;
            margin: 30px auto;
            padding: 0 20px;
        }
        
        .log-item {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 15px;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }
        
        .log-item:hover {
            background: rgba(255, 255, 255, 0.12);
            transform: translateY(-2px);
        }
        
        .log-item-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }
        
        .log-item-name {
            font-size: 1.3em;
            font-weight: 600;
        }
        
        .log-item-cal {
            font-size: 1.2em;
            color: #4ecdc4;
            font-weight: 700;
        }
        
        .log-item-time {
            font-size: 0.9em;
            color: rgba(255, 255, 255, 0.6);
        }
        
        .no-entries {
            text-align: center;
            color: rgba(255, 255, 255, 0.5);
            font-size: 1.2em;
            margin: 50px 0;
        }
        
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(0, 0, 0, 0.9);
            backdrop-filter: blur(20px);
            padding: 15px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .bottom-nav-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #4ecdc4, #00d4ff);
            border: none;
            border-radius: 15px;
            color: white;
            font-size: 1.2em;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .bottom-nav-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(0, 212, 255, 0.3);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Today's Log</h1>
        <div class="total-protein">{{ total_protein }}g protein</div>
    </div>
    
    <div class="log-container">
        {% if log_entries %}
            {% for entry in log_entries %}
            <div class="log-item">
                <div class="log-item-header">
                    <div class="log-item-name">{{ entry.name }}</div>
                    <div class="log-item-cal">{{ entry.protein }}g ({{ "%.2f"|format(entry.protein / entry.calories if entry.calories > 0 else 0) }} p/cal)</div>
                </div>
                <div class="log-item-time">{{ entry.time }}</div>
            </div>
            {% endfor %}
        {% else %}
            <div class="no-entries">No foods logged today</div>
        {% endif %}
    </div>
    
    <div class="bottom-nav">
        <button class="bottom-nav-btn" onclick="window.location.href='/'">
            Back to Food Pads
        </button>
    </div>
    
    <script>
        var lastUpdate = 0;
        
        function poll() {
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/poll-updates?since=' + lastUpdate, true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        try {
                            var data = JSON.parse(xhr.responseText);
                            if (data.updated) {
                                var proteinEl = document.querySelector('.total-protein');
                                if (proteinEl) {
                                    proteinEl.textContent = data.total_protein + 'g protein';
                                }
                                lastUpdate = data.timestamp;
                                
                                setTimeout(function() {
                                    window.location.reload();
                                }, 1000);
                            }
                            // Always wait 30 seconds before next poll
                            setTimeout(poll, 30000);
                        } catch (e) {
                            setTimeout(poll, 30000);
                        }
                    } else {
                        setTimeout(poll, 30000);
                    }
                }
            };
            xhr.send();
        }
        
        function startLongPolling() {
            poll();
        }
        
        // Start long polling when page loads  
        if (window.addEventListener) {
            window.addEventListener('load', startLongPolling, false);
        } else if (window.attachEvent) {
            window.attachEvent('onload', startLongPolling);
        } else {
            window.onload = startLongPolling;
        }
    </script>
</body>
</html>
"""

HTML_NUTRITION = """
<!DOCTYPE html>
<html>
<head>
    <title>Nutrition Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: #fff; 
            font-family: 'SF Pro Display', -webkit-system-font, 'Segoe UI', Roboto, sans-serif;
            min-height: 100vh;
            padding-bottom: 80px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            font-weight: 700;
            background: linear-gradient(45deg, #00d4ff, #ff6b6b, #4ecdc4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -1px;
        }
        
        .nutrition-stats {
            max-width: 800px;
            margin: 30px auto;
            padding: 0 20px;
        }
        
        .stat-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .stat-value {
            font-size: 2.2em;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .stat-value.calories { color: #ff6b6b; }
        .stat-value.protein { color: #4ecdc4; }
        .stat-value.ratio { color: #00d4ff; }
        
        .stat-label {
            font-size: 1em;
            color: rgba(255, 255, 255, 0.7);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(0, 0, 0, 0.9);
            backdrop-filter: blur(20px);
            padding: 15px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .bottom-nav-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #4ecdc4, #00d4ff);
            border: none;
            border-radius: 15px;
            color: white;
            font-size: 1.2em;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .bottom-nav-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(0, 212, 255, 0.3);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Nutrition Dashboard</h1>
    </div>
    
    <div class="nutrition-stats">
        <div class="stat-cards">
            <div class="stat-card">
                <div class="stat-value calories">{{ total_calories }}</div>
                <div class="stat-label">Calories</div>
            </div>
            <div class="stat-card">
                <div class="stat-value protein">{{ total_protein }}g</div>
                <div class="stat-label">Protein</div>
            </div>
            <div class="stat-card">
                <div class="stat-value ratio">{{ avg_ratio }}</div>
                <div class="stat-label">Avg P/Cal</div>
            </div>
        </div>
    </div>
    
    <div class="bottom-nav">
        <button class="bottom-nav-btn" onclick="window.location.href='/'">
            Back to Food Pads
        </button>
    </div>
    
    <script>
        var lastUpdate = 0;
        
        function poll() {
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/poll-updates?since=' + lastUpdate, true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        try {
                            var data = JSON.parse(xhr.responseText);
                            if (data.updated) {
                                lastUpdate = data.timestamp;
                                // Reload to update nutrition stats
                                setTimeout(function() {
                                    window.location.reload();
                                }, 1000);
                            }
                            // Always wait 30 seconds before next poll
                            setTimeout(poll, 30000);
                        } catch (e) {
                            setTimeout(poll, 30000);
                        }
                    } else {
                        setTimeout(poll, 30000);
                    }
                }
            };
            xhr.send();
        }
        
        function startLongPolling() {
            poll();
        }
        
        // Start long polling when page loads
        if (window.addEventListener) {
            window.addEventListener('load', startLongPolling, false);
        } else if (window.attachEvent) {
            window.attachEvent('onload', startLongPolling);
        } else {
            window.onload = startLongPolling;
        }
    </script>
</body>
</html>
"""

# --- HELPER FUNCTIONS ---
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

def save_food_entry(pad_key, food_key, food_data):
    """Save a food entry to today's log"""
    log_file = get_today_log_file()
    log = load_today_log()
    
    entry = {
        'time': datetime.now().strftime('%H:%M'),
        'pad': pad_key,
        'food': food_key,
        'name': food_data['name'],
        'calories': food_data['calories'],
        'protein': food_data.get('protein', 0),
        'timestamp': datetime.now().isoformat()
    }
    
    log.append(entry)
    
    with open(log_file, 'w') as f:
        json.dump(log, f, indent=2)

def calculate_daily_total():
    """Calculate total protein for today"""
    log = load_today_log()
    return sum(entry.get('protein', 0) for entry in log)

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
        'total_calories': total_calories,
        'total_protein': total_protein,
        'avg_ratio': f"{avg_ratio:.2f}"
    }

def mark_updated():
    """Mark that data has been updated for long polling"""
    global last_update
    with update_lock:
        last_update = time.time()
    # Wake up all waiting threads immediately
    update_event.set()
    # Clear the event after a brief moment so it's ready for next update
    threading.Timer(0.1, update_event.clear).start()

# --- ROUTES ---
@app.route('/poll-updates')
def poll_updates():
    """Long polling endpoint using threading events"""
    since = float(request.args.get('since', 0))
    timeout = 30  # 30 second timeout
    
    # Check if already updated before waiting
    with update_lock:
        if last_update > since:
            return jsonify({
                'updated': True,
                'timestamp': last_update,
                'item_count': calculate_daily_item_count(),
                'total_protein': calculate_daily_total()
            })
    
    # Wait for update event or timeout
    event_occurred = update_event.wait(timeout)
    
    if event_occurred:
        with update_lock:
            if last_update > since:
                return jsonify({
                    'updated': True,
                    'timestamp': last_update,
                    'item_count': calculate_daily_item_count(),
                    'total_protein': calculate_daily_total()
                })
    
    return jsonify({'updated': False})
@app.route('/')
def index():
    config = load_config()
    pads = config.get('pads', {})
    
    # Get current pad from URL parameter
    current_pad = request.args.get('pad', list(pads.keys())[0] if pads else None)
    
    # If invalid pad, redirect to first pad
    if current_pad not in pads and pads:
        return redirect(url_for('index', pad=list(pads.keys())[0]))
    
    # Get current pad data
    current_pad_data = pads.get(current_pad, {})
    
    daily_total = calculate_daily_total()
    item_count = calculate_daily_item_count()
    
    return render_template_string(HTML_INDEX,
                                pads=pads,
                                current_pad=current_pad,
                                current_pad_data=current_pad_data,
                                daily_total=daily_total,
                                item_count=item_count)

@app.route('/today')
def today_log():
    log_entries = load_today_log()
    total_protein = calculate_daily_total()
    
    return render_template_string(HTML_TODAY,
                                log_entries=log_entries,
                                total_protein=total_protein)

@app.route('/nutrition')
def nutrition_dashboard():
    log_entries = load_today_log()
    stats = calculate_nutrition_stats()
    
    return render_template_string(HTML_NUTRITION,
                                log_entries=log_entries,
                                total_calories=stats['total_calories'],
                                total_protein=stats['total_protein'],
                                avg_ratio=stats['avg_ratio'])

@app.route('/log', methods=['POST'])
def log_food():
    data = request.json
    if not data:
        return jsonify({'error': 'No data'}), 400
    
    pad_key = data.get('pad')
    food_key = data.get('food')
    
    if not pad_key or not food_key:
        return jsonify({'error': 'Missing pad or food key'}), 400
    
    config = load_config()
    
    if pad_key not in config.get('pads', {}):
        return jsonify({'error': 'Invalid pad'}), 400
        
    if food_key not in config['pads'][pad_key].get('foods', {}):
        return jsonify({'error': 'Invalid food'}), 400
    
    food_data = config['pads'][pad_key]['foods'][food_key]
    save_food_entry(pad_key, food_key, food_data)
    
    # Mark that data has been updated for long polling
    mark_updated()
    
    return jsonify({'status': 'success'})

# --- MAIN ---
def main():
    parser = argparse.ArgumentParser(description="Nutrition Pad")
    parser.add_argument('--host', default='localhost', help='Host IP')
    parser.add_argument('--port', type=int, default=5001, help='Port')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    args = parser.parse_args()
    
    print("Starting Nutrition Pad on http://{}:{}".format(args.host, args.port))
    print("Config file: {}".format(CONFIG_FILE))
    print("Logs directory: {}".format(LOGS_DIR))
    
    app.run(debug=args.debug, host=args.host, port=args.port, threaded=True)

if __name__ == '__main__':
    main()