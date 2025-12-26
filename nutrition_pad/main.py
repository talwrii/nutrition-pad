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
current_nonce = None  # Store the nonce from the last update
current_amount = 100  # Server-side amount state
amount_update = time.time()  # Track when amount was last updated

CONFIG_FILE = 'foods.toml'
LOGS_DIR = 'daily_logs'

# Create logs directory if it doesn't exist
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# --- DEFAULT CONFIG (unit vs amount foods) ---
DEFAULT_CONFIG = """[pads.proteins]
name = "Proteins"

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
        
        .current-amount {
            text-align: center;
            margin-top: 15px;
            font-size: 1.8em;
            font-weight: 700;
            color: #ffd93d;
            text-shadow: 0 0 20px rgba(255, 217, 61, 0.3);
        }
        
        .item-count {
            text-align: center;
            margin-top: 10px;
            font-size: 1.2em;
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
            flex-wrap: wrap;
        }
        
        .tab-btn {
            flex: 1;
            min-width: 100px;
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
            margin: 2px;
        }
        
        .tab-btn.active {
            background: linear-gradient(135deg, #00d4ff, #4ecdc4);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0, 212, 255, 0.3);
        }
        
        .tab-btn.amounts.active {
            background: linear-gradient(135deg, #ffd93d, #ff6b6b);
            box-shadow: 0 10px 30px rgba(255, 217, 61, 0.3);
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
        
        .food-btn.amount-food {
            border-color: rgba(255, 217, 61, 0.3);
            background: rgba(255, 217, 61, 0.05);
        }
        
        .food-btn.unit-food {
            border-color: rgba(78, 205, 196, 0.3);
            background: rgba(78, 205, 196, 0.05);
        }
        
        .food-type-indicator {
            position: absolute;
            top: 8px;
            right: 8px;
            background: rgba(0, 0, 0, 0.6);
            color: white;
            font-size: 0.75em;
            padding: 4px 8px;
            border-radius: 8px;
            font-weight: 600;
        }
        
        .food-type-indicator.amount {
            background: rgba(255, 217, 61, 0.8);
            color: #1a1a2e;
        }
        
        .food-type-indicator.unit {
            background: rgba(78, 205, 196, 0.8);
            color: #1a1a2e;
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
            
            .amount-display {
                font-size: 2.5em;
            }
            
            .nav-tabs {
                margin: 20px 10px 0;
            }
            
            .tab-btn {
                padding: 12px 15px;
                font-size: 1em;
            }
        }
    </style>
    <script>
        var lastUpdate = parseFloat(localStorage.getItem('lastUpdate') || '0');
        var lastAmountUpdate = parseFloat(localStorage.getItem('lastAmountUpdate') || '0');
        var isPolling = false;
        var myNonce = null;
        var debugMode = {{ 'true' if js_debug else 'false' }};
        
        function debug(msg) {
            if (debugMode) {
                console.log('[DEBUG] ' + msg);
                var debugEl = document.getElementById('debug') || document.createElement('div');
                if (!debugEl.id) {
                    debugEl.id = 'debug';
                    debugEl.style.cssText = 'position:fixed;top:0;right:0;background:red;color:white;padding:5px;font-size:12px;z-index:9999;max-width:200px;';
                    document.body.appendChild(debugEl);
                }
                debugEl.innerHTML = new Date().toTimeString().substr(0,8) + ': ' + msg;
            }
        }
        
        function generateNonce() {
            return Date.now().toString() + Math.random().toString(36).substr(2);
        }
        
        function getCurrentAmount() {
            // Amount is now synced with server, get from page data initially
            var displayEl = document.querySelector('.current-amount, .amount-display');
            if (displayEl) {
                var match = displayEl.textContent.match(/(\d+)g/);
                if (match) return parseFloat(match[1]);
            }
            return 100;
        }
        
        function setCurrentAmount(amount) {
            // Send amount to server
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/set-amount', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    debug('Amount set successfully to: ' + amount);
                    updateAmountDisplay(amount);
                    // Update our local timestamp so we don't get our own update back
                    lastAmountUpdate = new Date().getTime() / 1000;
                    localStorage.setItem('lastAmountUpdate', lastAmountUpdate.toString());
                } else if (xhr.readyState === 4) {
                    debug('Error setting amount: ' + xhr.status);
                }
            };
            xhr.send(JSON.stringify({amount: amount}));
        }
        
        function updateAmountDisplay(amount) {
            var amountEls = document.querySelectorAll('.current-amount, .amount-display');
            amountEls.forEach(function(el) {
                el.textContent = amount + 'g';
            });
            
            // Update amount indicators on food buttons
            var amountIndicators = document.querySelectorAll('.food-type-indicator.amount');
            amountIndicators.forEach(function(el) {
                el.textContent = amount + 'g';
            });
            
            var sliderEl = document.getElementById('amountSlider');
            if (sliderEl) {
                sliderEl.value = amount;
            }
        }
        
        function createPresetButtons() {
            var presetGrid = document.querySelector('.preset-grid');
            if (!presetGrid) return;
            
            var presets = [25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 300, 400, 500];
            presetGrid.innerHTML = '';
            
            presets.forEach(function(amount) {
                var btn = document.createElement('button');
                btn.className = 'preset-btn';
                btn.textContent = amount + 'g';
                btn.onclick = function() { setCurrentAmount(amount); };
                presetGrid.appendChild(btn);
            });
        }
        
        function onAmountSliderChange(value) {
            setCurrentAmount(parseFloat(value));
        }
        
        function logFood(padKey, foodKey) {
            myNonce = generateNonce();
            debug('Logging food with nonce: ' + myNonce);
            
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
                nonce: myNonce
            }));
        }
        
        function poll() {
            if (isPolling) {
                debug('Poll already running, skipping');
                return;
            }
            
            isPolling = true;
            debug('Starting poll, lastUpdate: ' + lastUpdate + ', lastAmountUpdate: ' + lastAmountUpdate);
            
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/poll-updates?since=' + lastUpdate + '&amount_since=' + lastAmountUpdate, true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    isPolling = false;
                    
                    if (xhr.status === 200) {
                        try {
                            var data = JSON.parse(xhr.responseText);
                            debug('Poll response: updated=' + data.updated + ', amount_changed=' + data.amount_changed + ', current_amount=' + data.current_amount);
                            
                            if (data.updated && data.timestamp > lastUpdate) {
                                lastUpdate = data.timestamp;
                                localStorage.setItem('lastUpdate', lastUpdate.toString());
                                
                                if (data.nonce && myNonce && data.nonce === myNonce) {
                                    debug('Skipping refresh - this was my update');
                                    myNonce = null;
                                } else {
                                    debug('Refreshing - update from other device');
                                    var itemCountEl = document.querySelector('.item-count');
                                    if (itemCountEl) {
                                        itemCountEl.textContent = data.item_count + ' items logged today';
                                    }
                                    
                                    setTimeout(function() {
                                        window.location.reload();
                                    }, 1000);
                                    return;
                                }
                            }
                            
                            // Check for amount changes separately
                            if (data.amount_changed) {
                                debug('Amount changed from server: ' + data.current_amount);
                                lastAmountUpdate = new Date().getTime() / 1000;
                                localStorage.setItem('lastAmountUpdate', lastAmountUpdate.toString());
                                updateAmountDisplay(data.current_amount);
                                
                                // Force update of amount indicators specifically
                                var amountIndicators = document.querySelectorAll('.food-type-indicator.amount');
                                debug('Found ' + amountIndicators.length + ' amount indicators to update');
                                amountIndicators.forEach(function(el) {
                                    el.textContent = data.current_amount + 'g';
                                    debug('Updated indicator to: ' + data.current_amount + 'g');
                                });
                            }
                            
                            if (!data.updated && !data.amount_changed) {
                                debug('No updates');
                            }
                        } catch (e) {
                            debug('JSON parse error: ' + e.message);
                        }
                    } else {
                        debug('HTTP error: ' + xhr.status);
                    }
                    
                    setTimeout(poll, 2000); // Poll every 2 seconds for immediate syncing
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
        
        // Initialize when page loads
        window.onload = function() {
            updateAmountDisplay(getCurrentAmount());
            createPresetButtons();
            startLongPolling();
        };
    </script>
</head>
<body>
    <div class="header">
        <h1>Food Pads</h1>
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
    <div class="amounts-container">
        <div class="amount-display">{{ current_amount }}g</div>
        
        <div class="slider-container">
            <input type="range" min="0" max="500" value="{{ current_amount }}" 
                   class="slider" id="amountSlider" 
                   onchange="setCurrentAmount(this.value)">
            <div style="display: flex; justify-content: space-between; color: rgba(255,255,255,0.5); font-size: 0.9em; margin-top: 10px;">
                <span>0g</span>
                <span>250g</span>
                <span>500g</span>
            </div>
        </div>
        
        <div class="preset-amounts">
            <h3>Quick Amounts</h3>
            <div class="preset-grid"></div>
        </div>
    </div>
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
            align-items: flex-start;
            margin-bottom: 8px;
            flex-wrap: wrap;
        }
        
        .log-item-name {
            font-size: 1.3em;
            font-weight: 600;
            flex: 1;
            min-width: 200px;
        }
        
        .log-item-amount {
            font-size: 1.1em;
            color: #ffd93d;
            font-weight: 600;
            margin-right: 15px;
        }
        
        .log-item-cal {
            font-size: 1.2em;
            color: #4ecdc4;
            font-weight: 700;
        }
        
        .log-item-time {
            font-size: 0.9em;
            color: rgba(255, 255, 255, 0.6);
            margin-top: 5px;
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
        
        @media (max-width: 768px) {
            .log-item-header {
                flex-direction: column;
                align-items: stretch;
            }
            
            .log-item-amount {
                margin-right: 0;
                margin-bottom: 5px;
            }
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
    
    <script>
        var lastUpdate = parseFloat(localStorage.getItem('lastUpdate') || '0');
        var isPolling = false;
        var debugMode = {{ 'true' if js_debug else 'false' }};
        
        function debug(msg) {
            if (debugMode) {
                console.log('[DEBUG TODAY] ' + msg);
                var debugEl = document.getElementById('debug') || document.createElement('div');
                if (!debugEl.id) {
                    debugEl.id = 'debug';
                    debugEl.style.cssText = 'position:fixed;top:0;right:0;background:blue;color:white;padding:5px;font-size:12px;z-index:9999;max-width:200px;';
                    document.body.appendChild(debugEl);
                }
                debugEl.innerHTML = new Date().toTimeString().substr(0,8) + ': ' + msg;
            }
        }
        
        function poll() {
            if (isPolling) {
                debug('Poll already running, skipping');
                return;
            }
            
            isPolling = true;
            debug('Starting poll, lastUpdate: ' + lastUpdate);
            
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/poll-updates?since=' + lastUpdate, true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    isPolling = false;
                    
                    if (xhr.status === 200) {
                        try {
                            var data = JSON.parse(xhr.responseText);
                            debug('Poll response: updated=' + data.updated);
                            
                            if (data.updated && data.timestamp > lastUpdate) {
                                lastUpdate = data.timestamp;
                                localStorage.setItem('lastUpdate', lastUpdate.toString());
                                
                                debug('Refreshing - showing new logged items');
                                setTimeout(function() {
                                    window.location.reload();
                                }, 1000);
                                return;
                            }
                        } catch (e) {
                            debug('JSON parse error: ' + e.message);
                        }
                    }
                    
                    setTimeout(poll, 30000);
                }
            };
            xhr.send();
        }
        
        window.onload = function() {
            poll();
        };
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
        var lastUpdate = parseFloat(localStorage.getItem('lastUpdate') || '0');
        var isPolling = false;
        var debugMode = {{ 'true' if js_debug else 'false' }};
        
        function poll() {
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
                    setTimeout(poll, 30000);
                }
            };
            xhr.send();
        }
        
        window.onload = function() {
            poll();
        };
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

def save_food_entry(pad_key, food_key, food_data, amount=None):
    """Save a food entry to today's log with specified amount or unit"""
    log_file = get_today_log_file()
    log = load_today_log()
    
    if food_data.get('type') == 'unit':
        # Unit food - use fixed calories/protein
        calories = food_data['calories']
        protein = food_data.get('protein', 0)
        amount = 1  # Store as 1 unit
        amount_display = "1 unit"
    else:
        # Amount food - calculate based on grams
        if amount is None:
            amount = 100  # Default fallback
        calories = food_data['calories_per_gram'] * amount
        protein = food_data.get('protein_per_gram', 0) * amount
        amount_display = f"{amount}g"
    
    entry = {
        'time': datetime.now().strftime('%H:%M'),
        'pad': pad_key,
        'food': food_key,
        'name': food_data['name'],
        'amount': amount,
        'amount_display': amount_display,
        'calories': round(calories, 1),
        'protein': round(protein, 1),
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

def mark_updated(nonce=None):
    """Mark that data has been updated for long polling"""
    global last_update, current_nonce
    with update_lock:
        last_update = time.time()
        current_nonce = nonce
    update_event.set()
    threading.Timer(0.1, update_event.clear).start()

def mark_amount_updated():
    """Mark that amount has been updated"""
    global amount_update
    with update_lock:
        amount_update = time.time()
    # Use the same event mechanism to wake up long polling requests
    update_event.set()
    threading.Timer(0.1, update_event.clear).start()

# --- ROUTES ---
@app.route('/poll-updates')
def poll_updates():
    """Long polling endpoint using threading events"""
    since = float(request.args.get('since', 0))
    amount_since = float(request.args.get('amount_since', 0))
    timeout = 30
    
    print(f"[DEBUG] Poll request: since={since}, amount_since={amount_since}, current_amount={current_amount}, amount_update={amount_update}")
    
    with update_lock:
        if last_update > since or amount_update > amount_since:
            response = {
                'updated': last_update > since,
                'timestamp': last_update,
                'item_count': calculate_daily_item_count(),
                'total_protein': calculate_daily_total(),
                'nonce': current_nonce,
                'amount_changed': amount_update > amount_since,
                'current_amount': current_amount
            }
            print(f"[DEBUG] Immediate response: {response}")
            return jsonify(response)
    
    event_occurred = update_event.wait(timeout)
    
    if event_occurred:
        with update_lock:
            if last_update > since or amount_update > amount_since:
                response = {
                    'updated': last_update > since,
                    'timestamp': last_update,
                    'item_count': calculate_daily_item_count(),
                    'total_protein': calculate_daily_total(),
                    'nonce': current_nonce,
                    'amount_changed': amount_update > amount_since,
                    'current_amount': current_amount
                }
                print(f"[DEBUG] Event response: {response}")
                return jsonify(response)
    
    return jsonify({
        'updated': False,
        'amount_changed': False,
        'current_amount': current_amount
    })

@app.route('/set-amount', methods=['POST'])
def set_amount():
    """Set the current amount"""
    global current_amount
    
    data = request.json
    if not data or 'amount' not in data:
        return jsonify({'error': 'No amount provided'}), 400
    
    try:
        new_amount = float(data['amount'])
        if new_amount < 0 or new_amount > 500:
            return jsonify({'error': 'Amount must be between 0 and 500'}), 400
        
        old_amount = current_amount
        with update_lock:
            current_amount = new_amount
        
        print(f"[DEBUG] Amount changed from {old_amount} to {current_amount}")
        mark_amount_updated()
        print(f"[DEBUG] Amount update marked, new timestamp: {amount_update}")
        
        return jsonify({'status': 'success', 'amount': current_amount})
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid amount'}), 400

@app.route('/')
def index():
    global current_amount
    
    config = load_config()
    pads = config.get('pads', {})
    
    # Get current pad from URL parameter  
    current_pad = request.args.get('pad', None)
    
    # If no pad specified or invalid pad, default to first available pad or amounts
    if not current_pad or current_pad not in pads:
        if 'amounts' in pads:
            current_pad = 'amounts'
        elif pads:
            current_pad = list(pads.keys())[0]
        else:
            # No pads configured at all - this shouldn't happen with default config
            current_pad = 'amounts'
    
    # Get current pad data
    current_pad_data = pads.get(current_pad, {})
    
    daily_total = calculate_daily_total()
    item_count = calculate_daily_item_count()
    
    return render_template_string(HTML_INDEX,
                                pads=pads,
                                current_pad=current_pad,
                                current_pad_data=current_pad_data,
                                daily_total=daily_total,
                                item_count=item_count,
                                current_amount=current_amount,
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

@app.route('/log', methods=['POST'])
def log_food():
    global current_amount
    
    data = request.json
    if not data:
        return jsonify({'error': 'No data'}), 400
    
    pad_key = data.get('pad')
    food_key = data.get('food')
    nonce = data.get('nonce')
    
    if not pad_key or not food_key:
        return jsonify({'error': 'Missing pad or food key'}), 400
    
    config = load_config()
    
    if pad_key not in config.get('pads', {}):
        return jsonify({'error': 'Invalid pad'}), 400
        
    if food_key not in config['pads'][pad_key].get('foods', {}):
        return jsonify({'error': 'Invalid food'}), 400
    
    food_data = config['pads'][pad_key]['foods'][food_key]
    
    # Pass amount for amount-based foods, None for unit foods
    if food_data.get('type') == 'unit':
        save_food_entry(pad_key, food_key, food_data, None)
    else:
        save_food_entry(pad_key, food_key, food_data, current_amount)
    
    mark_updated(nonce)
    
    return jsonify({'status': 'success'})

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