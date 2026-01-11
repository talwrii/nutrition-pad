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
    validate_food_request, get_food_data, get_all_pads, CONFIG_FILE, LOGS_DIR,
    calculate_time_since_last_ate
)
from .styles import register_styles_routes
from .notes import register_notes_routes

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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        /* App-specific styles that may change frequently */
        .header-icons {
            position: absolute;
            top: 20px;
            right: 20px;
            display: flex;
            gap: 15px;
            z-index: 10;
        }
        .settings-cog, .notes-link, .amounts-link {
            font-size: 1.5em;
            color: rgba(255, 255, 255, 0.7);
            text-decoration: none;
            transition: all 0.3s ease;
            cursor: pointer;
            /* Larger touch target for tablets */
            padding: 10px;
            min-width: 44px;
            min-height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .settings-cog:hover {
            color: #ffd93d;
            transform: rotate(90deg) scale(1.1);
            text-shadow: 0 0 10px rgba(255, 217, 61, 0.5);
        }
        .notes-link:hover {
            color: #ff6b6b;
            transform: scale(1.1);
            text-shadow: 0 0 10px rgba(255, 107, 107, 0.5);
        }
        .amounts-link:hover {
            color: #4ecdc4;
            transform: scale(1.1);
            text-shadow: 0 0 10px rgba(78, 205, 196, 0.5);
        }
        
        .food-btn.amount-food {
            border-color: rgba(255, 255, 255, 0.2);
        }
        
        .food-btn.unit-food {
            border-color: rgba(255, 255, 255, 0.3);
        }
        
        /* Square grid layout for food buttons */
        .food-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            padding: 15px;
        }
        
        .food-btn {
            aspect-ratio: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 16px;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
            border: 2px solid rgba(255, 255, 255, 0.2);
            text-align: center;
            overflow: hidden;
            position: relative;
        }
        
        .food-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
        }
        
        .food-btn:active {
            transform: scale(0.95);
        }
        
        .food-btn .food-name {
            font-size: 2em;
            font-weight: 600;
            color: white;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
            line-height: 1.2;
            word-break: break-word;
            max-height: 3.6em;
            overflow: hidden;
        }
        
        .food-btn .food-type-indicator {
            position: absolute;
            top: 8px;
            right: 8px;
            font-size: 1.4em;
            padding: 4px 8px;
            border-radius: 5px;
            background: rgba(0, 0, 0, 0.5);
            color: white;
            line-height: 1;
            max-width: 80px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .food-btn .food-calories {
            display: none;
        }
        
        @media (max-width: 480px) {
            .food-grid {
                grid-template-columns: repeat(3, 1fr);
                gap: 8px;
                padding: 10px;
            }
            .food-btn .food-name {
                font-size: 1.8em;
            }
            .food-btn .food-type-indicator {
                font-size: 1.3em;
            }
        }
        
        @media (max-width: 768px) {
            .header-icons {
                top: 15px;
                right: 15px;
            }
            .settings-cog, .notes-link, .amounts-link {
                font-size: 1.3em;
            }
        }
    </style>
    
    <script src="/static/polling.js"></script>
    <script>
        // Generate consistent color from string
        function hashColor(str) {
            var hash = 5381;
            for (var i = 0; i < str.length; i++) {
                hash = ((hash << 5) + hash) ^ str.charCodeAt(i);
            }
            // Use golden ratio to spread hues more evenly
            var h = Math.abs((hash * 137.508) % 360);
            return 'hsl(' + h + ', 75%, 45%)';
        }
        
        // Apply colors to food buttons on load
        document.addEventListener('DOMContentLoaded', function() {
            var buttons = document.querySelectorAll('.food-btn');
            buttons.forEach(function(btn) {
                var name = btn.querySelector('.food-name');
                if (name) {
                    btn.style.background = hashColor(name.textContent.trim());
                }
            });
        });
        
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
        <div class="header-icons">
            <a href="/?pad=amounts" class="amounts-link" title="Set Amount"><i class="fas fa-ruler"></i></a>
            <a href="/notes" class="notes-link" title="Food Notes"><i class="fas fa-sticky-note"></i></a>
            <a href="/edit-foods" class="settings-cog" title="Edit Foods Configuration"><i class="fas fa-cog"></i></a>
        </div>
        <div class="current-amount">{{ current_amount }}g</div>
        <div class="cal-per-protein">{{ avg_ratio }} cal/g protein</div>
        <div class="item-count">{{ item_count }} items logged today</div>
    </div>
    
    <div class="nav-tabs">
        {% for pad_key, pad_data in pads.items() %}
        {% if pad_key != 'amounts' %}
        <a class="tab-btn {% if pad_key == current_pad %}active{% endif %}" 
           href="/?pad={{ pad_key }}">
            {{ pad_data.name }}
        </a>
        {% endif %}
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
                <div class="food-type-indicator">
                    {% if food.get('type') == 'unit' %}U{% else %}{{ current_amount }}g{% endif %}
                </div>
                <div class="food-name">{{ food.name }}</div>
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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .header-icons {
            position: absolute;
            top: 20px;
            right: 20px;
            display: flex;
            gap: 15px;
            z-index: 10;
        }
        .settings-cog, .notes-link {
            font-size: 1.5em;
            color: rgba(255, 255, 255, 0.7);
            text-decoration: none;
            transition: all 0.3s ease;
            cursor: pointer;
            padding: 10px;
            min-width: 44px;
            min-height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .settings-cog:hover {
            color: #ffd93d;
            transform: rotate(90deg) scale(1.1);
            text-shadow: 0 0 10px rgba(255, 217, 61, 0.5);
        }
        .notes-link:hover {
            color: #ff6b6b;
            transform: scale(1.1);
            text-shadow: 0 0 10px rgba(255, 107, 107, 0.5);
        }
        
        .log-item {
            position: relative;
            padding-right: 50px;
        }
        
        .log-item-delete {
            position: absolute;
            top: 50%;
            right: 15px;
            transform: translateY(-50%);
            color: #ff6b6b;
            cursor: pointer;
            font-size: 1.8em;
            padding: 10px;
            line-height: 1;
            opacity: 0.7;
        }
        
        .log-item-delete:hover {
            opacity: 1;
        }
        
        @media (max-width: 768px) {
            .header-icons {
                top: 15px;
                right: 15px;
            }
            .settings-cog, .notes-link {
                font-size: 1.3em;
            }
        }
    </style>
    
    <script src="/static/polling.js"></script>
    <script>
        setDebugMode({{ 'true' if js_debug else 'false' }});
        
        function deleteEntry(index) {
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/delete-entry', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        window.location.reload();
                    } else {
                        alert('Error deleting entry');
                    }
                }
            };
            xhr.send(JSON.stringify({ index: index }));
        }
        
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
        <div class="header-icons">
            <a href="/notes" class="notes-link" title="Food Notes"><i class="fas fa-sticky-note"></i></a>
            <a href="/edit-foods" class="settings-cog" title="Edit Foods Configuration"><i class="fas fa-cog"></i></a>
        </div>
        <div class="total-protein">{{ total_protein }}g protein</div>
        <div class="cal-per-protein">{{ avg_ratio }} cal/g protein</div>
        <div class="item-count">{{ item_count }} items logged today</div>
    </div>
    
    <div class="log-container">
        {% if log_entries %}
            {% for entry in log_entries %}
            <div class="log-item">
                <span class="log-item-delete" onclick="deleteEntry({{ loop.index0 }})">&times;</span>
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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
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
            padding: 10px;
            min-width: 44px;
            min-height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .settings-cog:hover {
            color: #ffd93d;
            transform: rotate(90deg) scale(1.1);
            text-shadow: 0 0 10px rgba(255, 217, 61, 0.5);
        }
        
        .nav-links {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 20px auto;
            max-width: 600px;
            padding: 0 20px;
        }
        
        .nav-link {
            flex: 1;
            padding: 15px 20px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            color: white;
            text-decoration: none;
            text-align: center;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .nav-link:hover {
            background: rgba(255, 217, 61, 0.2);
            border-color: #ffd93d;
            transform: translateY(-2px);
        }
        
        .nav-link.notes {
            background: rgba(255, 107, 107, 0.1);
            border-color: rgba(255, 107, 107, 0.3);
        }
        
        .nav-link.notes:hover {
            background: rgba(255, 107, 107, 0.2);
            border-color: #ff6b6b;
        }
        
        .nav-link.resolve {
            background: rgba(78, 205, 196, 0.1);
            border-color: rgba(78, 205, 196, 0.3);
        }
        
        .nav-link.resolve:hover {
            background: rgba(78, 205, 196, 0.2);
            border-color: #4ecdc4;
        }
        
        @media (max-width: 768px) {
            .settings-cog {
                font-size: 1.3em;
                top: 15px;
                right: 15px;
            }
            
            .nav-links {
                flex-direction: column;
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
        function updateTimeSinceAte() {
            var timeEl = document.getElementById('time-since-ate');
            if (!timeEl) return;
            var lastMealTimestamp = timeEl.getAttribute('data-last-meal-timestamp');
            if (!lastMealTimestamp) {
                timeEl.textContent = '--';
                return;
            }
            try {
                var lastMealTime = new Date(lastMealTimestamp);
                var now = new Date();
                var diffMs = now - lastMealTime;
                var diffMinutes = Math.floor(diffMs / (1000 * 60));
                if (diffMinutes < 60) {
                    timeEl.textContent = diffMinutes + 'm';
                } else {
                    var hours = Math.floor(diffMinutes / 60);
                    var minutes = diffMinutes % 60;
                    timeEl.textContent = hours + 'h ' + minutes + 'm';
                }
            } catch (e) {
                console.error('Error updating time since ate:', e);
            }
        }
        window.onload = function() {
            simplePoll();
            updateTimeSinceAte();
            // Update time display every 5 minutes (300000 ms)
            setInterval(updateTimeSinceAte, 300000);
        };
    </script>
</head>
<body>
    <div class="header">
        <h1>Nutrition Dashboard</h1>
        <a href="/edit-foods" class="settings-cog" title="Edit Foods Configuration"><i class="fas fa-cog"></i></a>
    </div>
    
    <div class="nav-links">
        <a href="/notes" class="nav-link notes"><i class="fas fa-sticky-note"></i> Food Notes</a>
        <a href="/resolve-unknowns" class="nav-link resolve"><i class="fas fa-search"></i> Resolve Unknowns</a>
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
            <div class="stat-card">
                <div id="time-since-ate" class="stat-value time-since" data-last-meal-timestamp="{{ time_since_last_ate.timestamp if time_since_last_ate else '' }}">
                    {% if time_since_last_ate is not none %}
                        {% if time_since_last_ate.minutes < 60 %}
                            {{ time_since_last_ate.minutes }}m
                        {% else %}
                            {{ (time_since_last_ate.minutes // 60) }}h {{ (time_since_last_ate.minutes % 60) }}m
                        {% endif %}
                    {% else %}
                        --
                    {% endif %}
                </div>
                <div class="stat-label">Since Last Ate</div>
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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
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
            padding: 20px;
            background: rgba(255, 217, 61, 0.1);
            border: 1px solid rgba(255, 217, 61, 0.3);
            border-radius: 10px;
            color: rgba(255, 255, 255, 0.9);
            font-size: 0.95em;
            line-height: 1.6;
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
                <strong>📖 TOML Format Documentation:</strong><br><br>
                
                <strong>Basic Structure:</strong><br>
                <code>[pads.pad_name]</code> - Define a new food pad<br>
                <code>name = "Display Name"</code> - Human-readable pad name<br><br>
                
                <strong>Food Definitions:</strong><br>
                <code>[pads.pad_name.foods.food_key]</code> - Define a food item<br>
                <code>name = "Food Name"</code> - Display name for the food<br>
                <code>type = "amount" | "unit"</code> - Food measurement type<br><br>
                
                <strong>Amount Foods (measured in grams):</strong><br>
                <code>calories_per_gram = 1.46</code> - Calories per gram<br>
                <code>protein_per_gram = 0.27</code> - Protein grams per gram of food<br>
                <code>scale = 1.0</code> - Optional scaling factor<br><br>
                
                <strong>Unit Foods (fixed serving sizes):</strong><br>
                <code>calories = 140</code> - Total calories per serving<br>
                <code>protein = 12</code> - Total protein grams per serving<br>
                <code>scale = 1.0</code> - Optional scaling factor<br><br>
                
                <strong>Example Entry:</strong><br>
                <code>[pads.proteins.foods.chicken_breast]</code><br>
                <code>name = "Chicken Breast"</code><br>
                <code>type = "amount"</code><br>
                <code>calories_per_gram = 1.46</code><br>
                <code>protein_per_gram = 0.27</code><br><br>
                
                <strong>💡 Tips:</strong><br>
                • Use descriptive food keys (no spaces, use underscores)<br>
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
        # Find first non-amounts pad
        for pad_key in pads.keys():
            if pad_key != 'amounts':
                current_pad = pad_key
                break
        # If only amounts exists, use it
        if not current_pad:
            current_pad = 'amounts'
    
    # Get current pad data
    current_pad_data = pads.get(current_pad, {})
    
    daily_total = calculate_daily_total()
    item_count = calculate_daily_item_count()
    stats = calculate_nutrition_stats()
    avg_ratio = stats['avg_ratio']
    current_amount = get_current_amount()
    # Format as int if whole number for cleaner display
    current_amount_display = int(current_amount) if current_amount == int(current_amount) else current_amount
    
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
                                avg_ratio=avg_ratio,
                                current_amount=current_amount_display,
                                amounts_content=amounts_content,
                                amounts_javascript=amounts_javascript,
                                js_debug=app.config.get('JS_DEBUG', False))

@app.route('/today')
def today_log():
    log_entries = load_today_log()
    total_protein = calculate_daily_total()
    stats = calculate_nutrition_stats()
    avg_ratio = stats['avg_ratio']
    item_count = calculate_daily_item_count()
    
    return render_template_string(HTML_TODAY,
                                log_entries=log_entries,
                                total_protein=total_protein,
                                avg_ratio=avg_ratio,
                                item_count=item_count,
                                js_debug=app.config.get('JS_DEBUG', False))

@app.route('/nutrition')
def nutrition_dashboard():
    log_entries = load_today_log()
    stats = calculate_nutrition_stats()
    time_since_last_ate = calculate_time_since_last_ate()
    
    return render_template_string(HTML_NUTRITION,
                                log_entries=log_entries,
                                total_calories=stats['total_calories'],
                                total_protein=stats['total_protein'],
                                avg_ratio=stats['avg_ratio'],
                                time_since_last_ate=time_since_last_ate,
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
    try:
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
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise

@app.route('/delete-entry', methods=['POST'])
def delete_entry():
    """Delete a food entry from today's log by index"""
    try:
        data = request.json
        if not data or 'index' not in data:
            return jsonify({'error': 'No index provided'}), 400
        
        index = data['index']
        log_file = os.path.join(LOGS_DIR, date.today().strftime('%Y-%m-%d') + '.json')
        
        if not os.path.exists(log_file):
            return jsonify({'error': 'No log file for today'}), 400
        
        with open(log_file, 'r') as f:
            log_entries = json.load(f)
        
        if index < 0 or index >= len(log_entries):
            return jsonify({'error': 'Invalid index'}), 400
        
        del log_entries[index]
        
        with open(log_file, 'w') as f:
            json.dump(log_entries, f, indent=2)
        
        mark_updated("delete_entry")
        
        return jsonify({'status': 'success'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise

@app.route('/api/notes')
def api_notes():
    """API endpoint to get notes and unknowns as JSON"""
    from datetime import timedelta
    
    days = int(request.args.get('days', 7))
    
    result = {
        'dates': []
    }
    
    for days_ago in range(days):
        target_date = date.today() - timedelta(days=days_ago)
        date_str = target_date.strftime('%Y-%m-%d')
        
        # Load notes
        notes_file = os.path.join(LOGS_DIR, f'{date_str}_notes.json')
        notes = []
        if os.path.exists(notes_file):
            try:
                with open(notes_file, 'r') as f:
                    notes = json.load(f)
            except:
                pass
        
        # Load unknowns
        log_file = os.path.join(LOGS_DIR, f'{date_str}.json')
        unknowns = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    log_entries = json.load(f)
                
                for i, entry in enumerate(log_entries):
                    if 'unknown' in entry.get('food', '').lower() or 'unknown' in entry.get('name', '').lower():
                        entry['index'] = i
                        unknowns.append(entry)
            except:
                pass
        
        if notes or unknowns:
            result['dates'].append({
                'date': date_str,
                'notes': notes,
                'unknowns': unknowns
            })
    
    return jsonify(result)

@app.route('/api/foods')
def api_foods():
    """API endpoint to get all foods as JSON"""
    pads = get_all_pads()
    
    foods = []
    for pad_key, pad_data in pads.items():
        if pad_key == 'amounts':
            continue
        
        pad_name = pad_data.get('name', pad_key)
        
        for food_key, food in pad_data.get('foods', {}).items():
            food_entry = {
                'pad_key': pad_key,
                'pad_name': pad_name,
                'food_key': food_key,
                'name': food.get('name', food_key),
                'type': food.get('type', 'amount')
            }
            
            if food.get('type') == 'unit':
                food_entry['calories'] = food.get('calories', 0)
                food_entry['protein'] = food.get('protein', 0)
            else:
                food_entry['calories_per_gram'] = food.get('calories_per_gram', 0)
                food_entry['protein_per_gram'] = food.get('protein_per_gram', 0)
            
            if food.get('scale') and food.get('scale') != 1.0:
                food_entry['scale'] = food.get('scale')
            
            foods.append(food_entry)
    
    return jsonify({'foods': foods})

@app.route('/api/foods/search')
def api_foods_search():
    """API endpoint to search foods"""
    query = request.args.get('q', '').lower()
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    pads = get_all_pads()
    
    foods = []
    for pad_key, pad_data in pads.items():
        if pad_key == 'amounts':
            continue
        
        pad_name = pad_data.get('name', pad_key)
        
        for food_key, food in pad_data.get('foods', {}).items():
            # Check if query matches
            if query not in food.get('name', '').lower() and query not in food_key.lower():
                continue
            
            food_entry = {
                'pad_key': pad_key,
                'pad_name': pad_name,
                'food_key': food_key,
                'name': food.get('name', food_key),
                'type': food.get('type', 'amount')
            }
            
            if food.get('type') == 'unit':
                food_entry['calories'] = food.get('calories', 0)
                food_entry['protein'] = food.get('protein', 0)
            else:
                food_entry['calories_per_gram'] = food.get('calories_per_gram', 0)
                food_entry['protein_per_gram'] = food.get('protein_per_gram', 0)
            
            if food.get('scale') and food.get('scale') != 1.0:
                food_entry['scale'] = food.get('scale')
            
            foods.append(food_entry)
    
    return jsonify({'foods': foods, 'query': query})

@app.route('/api/foods/<pad_key>/<food_key>')
def api_foods_get(pad_key, food_key):
    """API endpoint to get specific food"""
    try:
        food_data = get_food_data(pad_key, food_key)
        
        food_entry = {
            'pad_key': pad_key,
            'food_key': food_key,
            'name': food_data.get('name', food_key),
            'type': food_data.get('type', 'amount')
        }
        
        if food_data.get('type') == 'unit':
            food_entry['calories'] = food_data.get('calories', 0)
            food_entry['protein'] = food_data.get('protein', 0)
        else:
            food_entry['calories_per_gram'] = food_data.get('calories_per_gram', 0)
            food_entry['protein_per_gram'] = food_data.get('protein_per_gram', 0)
        
        if food_data.get('scale') and food_data.get('scale') != 1.0:
            food_entry['scale'] = food_data.get('scale')
        
        return jsonify({'food': food_entry})
    except:
        return jsonify({'error': 'Food not found'}), 404

@app.route('/api/foods', methods=['POST'])
def api_foods_add():
    """API endpoint to add a food"""
    data = request.json
    if not data or 'toml_content' not in data:
        return jsonify({'success': False, 'error': 'No TOML content provided'}), 400
    
    toml_content = data['toml_content']
    
    # Parse the TOML fragment
    try:
        parsed = toml.loads(toml_content)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Invalid TOML: {str(e)}'}), 400
    
    # Extract pad and food keys from the TOML structure
    # Expected format: [pads.pad_key.foods.food_key]
    if 'pads' not in parsed:
        return jsonify({'success': False, 'error': 'TOML must contain [pads.pad_key.foods.food_key]'}), 400
    
    # Find the pad and food
    pad_key = None
    food_key = None
    new_food_data = None
    
    for pk, pad_data in parsed['pads'].items():
        if 'foods' in pad_data:
            for fk, food_data in pad_data['foods'].items():
                pad_key = pk
                food_key = fk
                new_food_data = food_data
                break
        if pad_key:
            break
    
    if not pad_key or not food_key or not new_food_data:
        return jsonify({'success': False, 'error': 'Could not find food definition in TOML'}), 400
    
    # Validate food data
    if 'name' not in new_food_data:
        return jsonify({'success': False, 'error': 'Food must have a name'}), 400
    
    if 'type' not in new_food_data:
        return jsonify({'success': False, 'error': 'Food must have a type (amount or unit)'}), 400
    
    food_type = new_food_data['type']
    if food_type not in ['amount', 'unit']:
        return jsonify({'success': False, 'error': 'Type must be "amount" or "unit"'}), 400
    
    if food_type == 'unit':
        if 'calories' not in new_food_data or 'protein' not in new_food_data:
            return jsonify({'success': False, 'error': 'Unit foods must have calories and protein'}), 400
    else:
        if 'calories_per_gram' not in new_food_data or 'protein_per_gram' not in new_food_data:
            return jsonify({'success': False, 'error': 'Amount foods must have calories_per_gram and protein_per_gram'}), 400
    
    # Load existing config
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = toml.load(f)
    except FileNotFoundError:
        return jsonify({'success': False, 'error': 'Config file not found'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error loading config: {str(e)}'}), 500
    
    # Add or update the food
    if 'pads' not in config:
        config['pads'] = {}
    
    if pad_key not in config['pads']:
        config['pads'][pad_key] = {'name': pad_key.capitalize(), 'foods': {}}
    
    if 'foods' not in config['pads'][pad_key]:
        config['pads'][pad_key]['foods'] = {}
    
    config['pads'][pad_key]['foods'][food_key] = new_food_data
    
    # Save config
    try:
        # Create backup first
        backup_file = CONFIG_FILE + '.backup'
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                backup_content = f.read()
            with open(backup_file, 'w') as f:
                f.write(backup_content)
        
        # Save new config
        with open(CONFIG_FILE, 'w') as f:
            toml.dump(config, f)
        
        # Trigger polling update
        mark_updated("food_added")
        
        return jsonify({
            'success': True,
            'message': 'Food added successfully',
            'pad_key': pad_key,
            'food_key': food_key
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error saving config: {str(e)}'}), 500

# Register polling and styles routes
register_polling_routes(app)
register_styles_routes(app)
register_notes_routes(app)

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