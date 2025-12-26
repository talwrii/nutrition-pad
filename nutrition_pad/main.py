from flask import Flask, render_template_string, request, redirect, url_for, jsonify
from datetime import datetime, date
import os
import json
import argparse
import toml
import time
import threading

# Import our modules
from .polling import register_polling_routes, get_current_amount, mark_updated, get_polling_javascript
from .amounts import render_amounts_tab, get_amounts_javascript
from .data import (
    ensure_logs_directory, load_config, load_today_log, save_food_entry,
    calculate_daily_total, calculate_daily_item_count, calculate_nutrition_stats,
    validate_food_request, get_food_data, get_all_pads, CONFIG_FILE, LOGS_DIR
)
from .styles import register_styles_routes

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize data directory
ensure_logs_directory()

# --- HTML TEMPLATES ---
HTML_INDEX = """
<!DOCTYPE html>
<html>
<head>
    <title>Food Pads</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="/static/base.css">
    <style>
        /* App-specific styles that may change frequently */
        .settings-cog {
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 1.5em;
            color: rgba(255, 255, 255, 0.7);
            text-decoration: none;
            transition: all 0.3s ease;
            z-index: 10;
            cursor: pointer;
        }

        .settings-cog:hover {
            color: #ffd93d;
            transform: rotate(90deg) scale(1.1);
            text-shadow: 0 0 10px rgba(255, 217, 61, 0.5);
        }
        
        .tab-btn.amounts.active {
            background: linear-gradient(135deg, #ffd93d, #ff6b6b);
            box-shadow: 0 10px 30px rgba(255, 217, 61, 0.3);
        }
        
        .food-btn.amount-food {
            border-color: rgba(255, 217, 61, 0.3);
            background: rgba(255, 217, 61, 0.05);
        }
        
        .food-btn.unit-food {
            border-color: rgba(78, 205, 196, 0.3);
            background: rgba(78, 205, 196, 0.05);
        }
        
        .food-type-indicator.amount {
            background: rgba(255, 217, 61, 0.8);
            color: #1a1a2e;
        }
        
        .food-type-indicator.unit {
            background: rgba(78, 205, 196, 0.8);
            color: #1a1a2e;
        }
        
        /* Amounts-specific styles */
        .amounts-container {
            max-width: 600px;
            margin: 0 auto;
            padding: 30px 20px;
        }
        
        .amount-display {
            text-align: center;
            font-size: 3em;
            font-weight: 700;
            color: #ffd93d;
            margin-bottom: 30px;
            text-shadow: 0 0 20px rgba(255, 217, 61, 0.3);
        }
        
        .slider-container {
            margin: 40px 0;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            backdrop-filter: blur(20px);
        }
        
        .slider {
            width: 100%;
            height: 8px;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.2);
            outline: none;
            -webkit-appearance: none;
            margin: 20px 0;
        }
        
        .slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: linear-gradient(135deg, #ffd93d, #ff6b6b);
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(255, 217, 61, 0.3);
        }
        
        .slider::-moz-range-thumb {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: linear-gradient(135deg, #ffd93d, #ff6b6b);
            cursor: pointer;
            border: none;
            box-shadow: 0 4px 15px rgba(255, 217, 61, 0.3);
        }
        
        .preset-amounts {
            margin: 30px 0;
        }
        
        .preset-amounts h3 {
            font-size: 1.2em;
            margin-bottom: 15px;
            color: rgba(255, 255, 255, 0.7);
            text-align: center;
        }
        
        .preset-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
            gap: 10px;
        }
        
        .preset-btn {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            padding: 15px 10px;
            color: white;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
        }
        
        .preset-btn:hover {
            background: rgba(255, 217, 61, 0.2);
            border-color: #ffd93d;
            transform: translateY(-2px);
        }
        
        @media (max-width: 768px) {
            .settings-cog {
                font-size: 1.3em;
                top: 15px;
                right: 15px;
            }
            
            .amount-display {
                font-size: 2.5em;
            }
        }
    </style>
    
    <script src="/static/polling.js"></script>
    <script>
        // App-specific JavaScript
        setDebugMode({{ 'true' if js_debug else 'false' }});
        
        // Amounts functionality
        {{ amounts_javascript|safe }}
        
        function logFood(padKey, foodKey) {
            var nonce = generateNonce();
            debug('Logging food with nonce: ' + nonce);
            setMyNonce(nonce);
            
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/log', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    debug('Food logged successfully');
                    var itemCountEl = document.querySelector('.item-count');
                    if (itemCountEl) {
                        var currentCount = parseInt(itemCountEl.textContent) || 0;
                        itemCountEl.textContent = (currentCount + 1) + ' items logged today';
                    }
                }
            };
            xhr.send(JSON.stringify({
                pad: padKey,
                food: foodKey,
                nonce: nonce
            }));
        }
        
        function showTodayLog() {
            window.location.href = '/today';
        }
        
        function showNutrition() {
            window.location.href = '/nutrition';
        }
        
        // Initialize when page loads
        window.onload = function() {
            if (typeof initializeAmountsTab === 'function') {
                initializeAmountsTab();
            } else {
                // Fallback to old method
                if (typeof updateAmountDisplay === 'function') {
                    updateAmountDisplay(getCurrentAmount());
                }
                if (typeof createPresetButtons === 'function') {
                    createPresetButtons();
                }
            }
            startLongPolling();
        };
    </script>
</head>
<body>
    <div class="header">
        <h1>Food Pads</h1>
        <a href="/edit-foods" class="settings-cog" title="Edit Foods Configuration">⚙️</a>
        <div class="current-amount">{{ current_amount }}g</div>
        <div class="item-count">{{ item_count }} items logged today</div>
    </div>
    
    <div class="nav-tabs">
        {% for pad_key, pad_data in pads.items() %}
        <a class="tab-btn {% if pad_key == 'amounts' %}amounts{% endif %} {% if pad_key == current_pad %}active{% endif %}" 
           href="/?pad={{ pad_key }}">
            {{ pad_data.name }}
        </a>
        {% endfor %}
    </div>
    
    {% if current_pad == 'amounts' %}
    {{ amounts_content|safe }}
    {% else %}
    <div id="food-grid" class="food-grid">
        {% if current_pad_data and current_pad_data.foods %}
            {% for food_key, food in current_pad_data.foods.items() %}
            <div class="food-btn {% if food.get('type') == 'unit' %}unit-food{% else %}amount-food{% endif %}" 
                 onclick="logFood('{{ current_pad }}', '{{ food_key }}')">
                <div class="food-type-indicator {% if food.get('type') == 'unit' %}unit{% else %}amount{% endif %}">
                    {% if food.get('type') == 'unit' %}UNIT{% else %}{{ current_amount }}g{% endif %}
                </div>
                <div class="food-name">{{ food.name }}</div>
                {% if food.get('type') == 'unit' %}
                    <div class="food-calories">{{ food.get('calories', 0) }}cal • {{ food.get('protein', 0) }}g protein</div>
                {% elif food.get('calories_per_gram') %}
                    <div class="food-calories">{{ "%.2f"|format(food.get('protein_per_gram', 0) / food.calories_per_gram if food.calories_per_gram > 0 else 0) }} p/cal</div>
                {% else %}
                    <div class="food-calories">No nutrition data</div>
                {% endif %}
            </div>
            {% endfor %}
        {% else %}
            <div class="no-foods">No foods in this pad</div>
        {% endif %}
    </div>
    {% endif %}
    
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
    <link rel="stylesheet" href="/static/base.css">
    <style>
        .settings-cog {
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 1.5em;
            color: rgba(255, 255, 255, 0.7);
            text-decoration: none;
            transition: all 0.3s ease;
            z-index: 10;
            cursor: pointer;
        }

        .settings-cog:hover {
            color: #ffd93d;
            transform: rotate(90deg) scale(1.1);
            text-shadow: 0 0 10px rgba(255, 217, 61, 0.5);
        }
        
        @media (max-width: 768px) {
            .settings-cog {
                font-size: 1.3em;
                top: 15px;
                right: 15px;
            }
        }
    </style>
    
    <script src="/static/polling.js"></script>
    <script>
        setDebugMode({{ 'true' if js_debug else 'false' }});
        
        // Simplified polling for today page - just refresh on updates
        function simplePoll() {
            if (isPolling) return;
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
                                lastUpdate = data.timestamp;
                                localStorage.setItem('lastUpdate', lastUpdate.toString());
                                setTimeout(function() {
                                    window.location.reload();
                                }, 1000);
                                return;
                            }
                        } catch (e) {}
                    }
                    setTimeout(simplePoll, 30000);
                }
            };
            xhr.send();
        }
        
        window.onload = function() {
            simplePoll();
        };
    </script>
</head>
<body>
    <div class="header">
        <h1>Today's Log</h1>
        <a href="/edit-foods" class="settings-cog" title="Edit Foods Configuration">⚙️</a>
        <div class="total-protein">{{ total_protein }}g protein</div>
    </div>
    
    <div class="log-container">
        {% if log_entries %}
            {% for entry in log_entries %}
            <div class="log-item">
                <div class="log-item-header">
                    <div class="log-item-name">{{ entry.name }}</div>
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <div class="log-item-amount">{{ entry.amount_display }}</div>
                        <div class="log-item-cal">{{ entry.protein }}g protein</div>
                    </div>
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
</body>
</html>
"""

HTML_NUTRITION = """
<!DOCTYPE html>
<html>
<head>
    <title>Nutrition Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="/static/base.css">
    <style>
        .settings-cog {
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 1.5em;
            color: rgba(255, 255, 255, 0.7);
            text-decoration: none;
            transition: all 0.3s ease;
            z-index: 10;
            cursor: pointer;
        }

        .settings-cog:hover {
            color: #ffd93d;
            transform: rotate(90deg) scale(1.1);
            text-shadow: 0 0 10px rgba(255, 217, 61, 0.5);
        }
        
        @media (max-width: 768px) {
            .settings-cog {
                font-size: 1.3em;
                top: 15px;
                right: 15px;
            }
        }
    </style>
    
    <script src="/static/polling.js"></script>
    <script>
        setDebugMode({{ 'true' if js_debug else 'false' }});
        
        // Simplified polling for nutrition page
        function simplePoll() {
            if (isPolling) return;
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
                                lastUpdate = data.timestamp;
                                localStorage.setItem('lastUpdate', lastUpdate.toString());
                                setTimeout(function() {
                                    window.location.reload();
                                }, 1000);
                                return;
                            }
                        } catch (e) {}
                    }
                    setTimeout(simplePoll, 30000);
                }
            };
            xhr.send();
        }
        
        window.onload = function() {
            simplePoll();
        };
    </script>
</head>
<body>
    <div class="header">
        <h1>Nutrition Dashboard</h1>
        <a href="/edit-foods" class="settings-cog" title="Edit Foods Configuration">⚙️</a>
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
</body>
</html>
"""

HTML_FOOD_EDITOR = """
<!DOCTYPE html>
<html>
<head>
    <title>Edit Foods Configuration</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="/static/base.css">
    <style>
        .editor-container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 30px 20px;
        }
        
        .editor-header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .editor-header h2 {
            color: #ffd93d;
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .editor-header p {
            color: rgba(255, 255, 255, 0.7);
            font-size: 1.1em;
        }
        
        .editor-form {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .editor-textarea {
            width: 100%;
            min-height: 600px;
            background: rgba(0, 0, 0, 0.3);
            border: 2px solid rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            padding: 20px;
            color: white;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 14px;
            line-height: 1.5;
            resize: vertical;
            outline: none;
            tab-size: 2;
        }
        
        .editor-textarea:focus {
            border-color: #00d4ff;
            box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
        }
        
        .editor-buttons {
            display: flex;
            gap: 15px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        
        .editor-btn {
            padding: 15px 30px;
            border: none;
            border-radius: 15px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            flex: 1;
            min-width: 150px;
        }
        
        .save-btn {
            background: linear-gradient(135deg, #4ecdc4, #00d4ff);
            color: white;
        }
        
        .save-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(78, 205, 196, 0.3);
        }
        
        .cancel-btn {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border: 2px solid rgba(255, 255, 255, 0.2);
        }
        
        .cancel-btn:hover {
            background: rgba(255, 107, 107, 0.2);
            border-color: #ff6b6b;
        }
        
        .status-message {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            font-weight: 600;
            display: none;
        }
        
        .status-success {
            background: rgba(78, 205, 196, 0.2);
            border: 2px solid rgba(78, 205, 196, 0.5);
            color: #4ecdc4;
        }
        
        .status-error {
            background: rgba(255, 107, 107, 0.2);
            border: 2px solid rgba(255, 107, 107, 0.5);
            color: #ff6b6b;
        }
        
        .help-text {
            margin-bottom: 20px;
            padding: 15px;
            background: rgba(255, 217, 61, 0.1);
            border: 1px solid rgba(255, 217, 61, 0.3);
            border-radius: 10px;
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.95em;
            line-height: 1.4;
        }
        
        @media (max-width: 768px) {
            .editor-container {
                padding: 20px 15px;
            }
            
            .editor-form {
                padding: 20px;
            }
            
            .editor-textarea {
                min-height: 400px;
                font-size: 12px;
            }
            
            .editor-buttons {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Food Configuration Editor</h1>
    </div>
    
    <div class="editor-container">
        <div class="editor-header">
            <h2>Edit foods.toml</h2>
            <p>Modify your food database configuration</p>
        </div>
        
        <div class="editor-form">
            <div class="help-text">
                <strong>💡 Tips:</strong><br>
                • Use <code>type = "amount"</code> for foods measured in grams<br>
                • Use <code>type = "unit"</code> for fixed serving sizes<br>
                • Make sure to save your changes before leaving this page<br>
                • Invalid TOML format will prevent saving
            </div>
            
            <form id="foodsForm" onsubmit="saveFoods(event)">
                <textarea id="foodsContent" class="editor-textarea" placeholder="Loading food configuration...">{{ foods_content }}</textarea>
                
                <div class="editor-buttons">
                    <button type="submit" class="editor-btn save-btn">💾 Save Changes</button>
                    <button type="button" class="editor-btn cancel-btn" onclick="window.location.href='/nutrition'">❌ Cancel</button>
                </div>
                
                <div id="statusMessage" class="status-message"></div>
            </form>
        </div>
    </div>
    
    <script>
        function saveFoods(event) {
            event.preventDefault();
            
            var content = document.getElementById('foodsContent').value;
            var statusEl = document.getElementById('statusMessage');
            var saveBtn = event.target.querySelector('.save-btn');
            
            // Disable save button
            saveBtn.disabled = true;
            saveBtn.textContent = '💾 Saving...';
            
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/edit-foods', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    saveBtn.disabled = false;
                    saveBtn.textContent = '💾 Save Changes';
                    
                    if (xhr.status === 200) {
                        try {
                            var response = JSON.parse(xhr.responseText);
                            if (response.success) {
                                showStatus('✅ Configuration saved! All devices will refresh automatically.', 'success');
                                setTimeout(function() {
                                    window.location.href = '/nutrition';
                                }, 2000);
                            } else {
                                showStatus('❌ Error: ' + (response.error || 'Failed to save'), 'error');
                            }
                        } catch (e) {
                            showStatus('❌ Error parsing response', 'error');
                        }
                    } else {
                        try {
                            var response = JSON.parse(xhr.responseText);
                            showStatus('❌ Error: ' + (response.error || 'Failed to save'), 'error');
                        } catch (e) {
                            showStatus('❌ Server error: ' + xhr.status, 'error');
                        }
                    }
                }
            };
            xhr.send(JSON.stringify({ content: content }));
        }
        
        function showStatus(message, type) {
            var statusEl = document.getElementById('statusMessage');
            statusEl.textContent = message;
            statusEl.className = 'status-message status-' + type;
            statusEl.style.display = 'block';
            
            if (type === 'success') {
                setTimeout(function() {
                    statusEl.style.display = 'none';
                }, 3000);
            }
        }
    </script>
</body>
</html>
"""

# --- ROUTES ---
@app.route('/')
def index():
    pads = get_all_pads()
    
    # Always ensure amounts tab is available
    if 'amounts' not in pads:
        pads['amounts'] = {'name': 'Set Amount'}
    
    # Get current pad from URL parameter  
    current_pad = request.args.get('pad', None)
    
    # If no pad specified or invalid pad, default to first available pad or amounts
    if not current_pad or current_pad not in pads:
        if 'amounts' in pads:
            current_pad = 'amounts'
        elif pads:
            current_pad = list(pads.keys())[0]
        else:
            # Fallback - should never happen now
            current_pad = 'amounts'
    
    # Get current pad data
    current_pad_data = pads.get(current_pad, {})
    
    daily_total = calculate_daily_total()
    item_count = calculate_daily_item_count()
    current_amount = get_current_amount()
    
    # Handle amounts tab content
    amounts_content = ""
    amounts_javascript = ""
    if current_pad == 'amounts':
        amounts_content = render_amounts_tab(current_amount)
        amounts_javascript = get_amounts_javascript()
    
    return render_template_string(HTML_INDEX,
                                pads=pads,
                                current_pad=current_pad,
                                current_pad_data=current_pad_data,
                                daily_total=daily_total,
                                item_count=item_count,
                                current_amount=current_amount,
                                amounts_content=amounts_content,
                                amounts_javascript=amounts_javascript,
                                js_debug=app.config.get('JS_DEBUG', False))

@app.route('/today')
def today_log():
    log_entries = load_today_log()
    total_protein = calculate_daily_total()
    
    return render_template_string(HTML_TODAY,
                                log_entries=log_entries,
                                total_protein=total_protein,
                                js_debug=app.config.get('JS_DEBUG', False))

@app.route('/nutrition')
def nutrition_dashboard():
    log_entries = load_today_log()
    stats = calculate_nutrition_stats()
    
    return render_template_string(HTML_NUTRITION,
                                log_entries=log_entries,
                                total_calories=stats['total_calories'],
                                total_protein=stats['total_protein'],
                                avg_ratio=stats['avg_ratio'],
                                js_debug=app.config.get('JS_DEBUG', False))

@app.route('/edit-foods', methods=['GET', 'POST'])
def edit_foods():
    """Food configuration editor route"""
    if request.method == 'GET':
        # Load current food configuration
        try:
            with open(CONFIG_FILE, 'r') as f:
                foods_content = f.read()
        except FileNotFoundError:
            foods_content = "# Food configuration file not found"
        except Exception as e:
            foods_content = f"# Error loading configuration: {str(e)}"
        
        return render_template_string(HTML_FOOD_EDITOR, 
                                    foods_content=foods_content,
                                    js_debug=app.config.get('JS_DEBUG', False))
    
    elif request.method == 'POST':
        # Save food configuration
        data = request.json
        if not data or 'content' not in data:
            return jsonify({'success': False, 'error': 'No content provided'}), 400
        
        content = data['content']
        
        # Validate TOML format
        try:
            toml.loads(content)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Invalid TOML format: {str(e)}'}), 400
        
        # Save the file
        try:
            # Create backup first
            backup_file = CONFIG_FILE + '.backup'
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    backup_content = f.read()
                with open(backup_file, 'w') as f:
                    f.write(backup_content)
            
            # Save new content
            with open(CONFIG_FILE, 'w') as f:
                f.write(content)
            
            # Trigger polling update to refresh all devices
            mark_updated("config_updated")
                
            return jsonify({'success': True, 'message': 'Configuration saved successfully'})
        except Exception as e:
            return jsonify({'success': False, 'error': f'Failed to save file: {str(e)}'}), 500

@app.route('/log', methods=['POST'])
def log_food():
    data = request.json
    if not data:
        return jsonify({'error': 'No data'}), 400
    
    pad_key = data.get('pad')
    food_key = data.get('food')
    nonce = data.get('nonce')
    
    if not pad_key or not food_key:
        return jsonify({'error': 'Missing pad or food key'}), 400
    
    # Validate request using data module
    valid, result = validate_food_request(pad_key, food_key)
    if not valid:
        return jsonify({'error': result}), 400
    
    food_data = result
    
    # Pass amount for amount-based foods, None for unit foods
    if food_data.get('type') == 'unit':
        save_food_entry(pad_key, food_key, food_data, None)
    else:
        current_amount = get_current_amount()
        save_food_entry(pad_key, food_key, food_data, current_amount)
    
    mark_updated(nonce)
    
    return jsonify({'status': 'success'})

# Register polling and styles routes
register_polling_routes(app)
register_styles_routes(app)

# --- MAIN ---
def main():
    parser = argparse.ArgumentParser(description="Nutrition Pad")
    parser.add_argument('--host', default='localhost', help='Host IP')
    parser.add_argument('--port', type=int, default=5001, help='Port')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    parser.add_argument('--js-debug', action='store_true', help='Enable JavaScript debugging')
    args = parser.parse_args()
    
    print("Starting Nutrition Pad on http://{}:{}".format(args.host, args.port))
    print("Config file: {}".format(CONFIG_FILE))
    print("Logs directory: {}".format(LOGS_DIR))
    if args.js_debug:
        print("JavaScript debugging enabled")
    
    app.config['JS_DEBUG'] = args.js_debug
    
    app.run(debug=args.debug, host=args.host, port=args.port, threaded=True)

if __name__ == '__main__':
    main()