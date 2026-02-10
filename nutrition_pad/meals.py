"""
Meals feature: define reusable meals (collections of foods) and log them in one click.
"""
import os
import json
import random
import string
from datetime import datetime, date
from flask import render_template_string, request, jsonify

from .data import MEALS_FILE, load_today_log, get_today_log_file, generate_entry_id, backfill_entry_ids
from .polling import get_current_amount, mark_updated


def load_meals():
    """Load all meal definitions from meals.json"""
    if not os.path.exists(MEALS_FILE):
        return []
    try:
        with open(MEALS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_meals(meals):
    """Save all meal definitions to meals.json"""
    with open(MEALS_FILE, 'w') as f:
        json.dump(meals, f, indent=2)


def generate_meal_id():
    """Generate a unique meal definition ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"meal_{timestamp}{suffix}"


def generate_meal_log_uid():
    """Generate a unique meal logging event UID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"meallog_{timestamp}{suffix}"


def calculate_meal_totals(meal):
    """Calculate total calories and protein for a meal definition"""
    total_cal = 0
    total_protein = 0
    for item in meal.get('items', []):
        if item.get('type') == 'unit':
            total_cal += item.get('calories', 0)
            total_protein += item.get('protein', 0)
        else:
            amount = item.get('amount', 100)
            total_cal += item.get('calories_per_gram', 0) * amount
            total_protein += item.get('protein_per_gram', 0) * amount
    return round(total_cal), round(total_protein, 1)


HTML_MEALS_BUILD = """
<!DOCTYPE html>
<html>
<head>
    <title>Building Meal</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="/static/base.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {
            background: linear-gradient(135deg, #1a2a2e 0%, #163e3e 50%, #0f4660 100%);
            min-height: 100vh;
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        .header-icons {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 10px;
        }
        .header-icons a {
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
        .meal-name-input {
            width: 90%;
            max-width: 500px;
            margin: 15px auto;
            display: block;
            padding: 12px 16px;
            font-size: 1.3em;
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid rgba(78, 205, 196, 0.4);
            border-radius: 12px;
            color: white;
            text-align: center;
            outline: none;
            -webkit-box-sizing: border-box;
            box-sizing: border-box;
        }
        .meal-name-input:focus { border-color: #4ecdc4; }
        .meal-name-input::placeholder { color: rgba(255, 255, 255, 0.4); }
        .meal-items {
            max-width: 600px;
            margin: 0 auto;
            padding: 0 15px;
        }
        .meal-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 12px;
            margin: 4px 0;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            color: white;
        }
        .meal-item .item-detail {
            color: rgba(255, 255, 255, 0.5);
            font-size: 0.85em;
        }
        .meal-item-remove {
            color: #ff6b6b;
            cursor: pointer;
            font-size: 1.4em;
            padding: 0 0 0 10px;
            opacity: 0.6;
        }
        .meal-item-remove:hover { opacity: 1; }
        .meal-totals {
            text-align: center;
            padding: 10px;
            color: rgba(255, 255, 255, 0.6);
            font-size: 0.95em;
            margin-top: 8px;
        }
        .meal-empty {
            text-align: center;
            color: rgba(255, 255, 255, 0.4);
            padding: 30px 15px;
            font-size: 1.1em;
        }
        .meal-empty a {
            color: #4ecdc4;
            text-decoration: none;
            font-weight: 600;
        }
    </style>
    <script>
        function itemCal(item) {
            if (item.type === 'unit') return item.calories || 0;
            return (item.calories_per_gram || 0) * (item.amount || 100);
        }
        function itemProt(item) {
            if (item.type === 'unit') return item.protein || 0;
            return (item.protein_per_gram || 0) * (item.amount || 100);
        }

        var cachedItems = [];

        function loadItemsFromServer(callback) {
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/get-meal-items', true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    var data = JSON.parse(xhr.responseText);
                    cachedItems = data.meal_items || [];
                    if (callback) callback(cachedItems);
                }
            };
            xhr.send();
        }

        function removeItem(index) {
            // For now, just don't support removal (would need server endpoint)
            alert('Item removal not yet supported in server-sync mode');
        }

        function renderItems() {
            loadItemsFromServer(function(items) {
                var container = document.getElementById('meal-items');
                var totalsEl = document.getElementById('meal-totals');
                var doneBtn = document.getElementById('done-btn');

                if (items.length === 0) {
                    container.innerHTML = '<div class="meal-empty">No items yet.<br><a href="/">Go to Food Pads</a> and click foods to add them.</div>';
                    if (totalsEl) totalsEl.innerHTML = '';
                    if (doneBtn) doneBtn.disabled = true;
                    return;
                }

                var html = '';
                var totalCal = 0;
                var totalProt = 0;
                for (var i = 0; i < items.length; i++) {
                    var item = items[i];
                    var cal = Math.round(itemCal(item));
                    var prot = Math.round(itemProt(item) * 10) / 10;
                    totalCal += cal;
                    totalProt += prot;
                    var detail = item.type === 'unit' ? '1 unit' : (item.amount || 100) + 'g';
                    html += '<div class="meal-item">';
                    html += '<span>' + item.name + ' <span class="item-detail">' + detail + '</span></span>';
                    html += '<span>' + cal + ' kcal</span>';
                    html += '</div>';
                }
                container.innerHTML = html;
                if (totalsEl) totalsEl.innerHTML = items.length + ' items &middot; ' + totalCal + ' kcal &middot; ' + totalProt + 'g protein';
                updateDoneBtn();
            });
        }

        function updateDoneBtn() {
            var doneBtn = document.getElementById('done-btn');
            var nameInput = document.getElementById('meal-name');
            if (doneBtn && nameInput) {
                doneBtn.disabled = !(cachedItems.length > 0 && nameInput.value.trim().length > 0);
            }
        }

        function doneMeal() {
            var nameInput = document.getElementById('meal-name');
            var name = nameInput ? nameInput.value.trim() : '';
            if (!name || cachedItems.length === 0) return;

            var doneBtn = document.getElementById('done-btn');
            if (doneBtn) { doneBtn.disabled = true; doneBtn.textContent = 'Saving...'; }

            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/meals/create', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        sessionStorage.removeItem('mealMode');
                        sessionStorage.removeItem('mealName');
                        setServerMealMode(false);
                        window.location.href = '/?pad=meals';
                    } else {
                        alert('Error saving meal');
                        if (doneBtn) { doneBtn.disabled = false; doneBtn.textContent = 'Done'; }
                    }
                }
            };
            xhr.send(JSON.stringify({ name: name, items: cachedItems }));
        }

        function cancelMeal() {
            sessionStorage.removeItem('mealMode');
            sessionStorage.removeItem('mealName');
            setServerMealMode(false);
            window.location.href = '/today';
        }

        function setServerMealMode(active) {
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/set-meal-mode', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.send(JSON.stringify({ active: active }));
        }

        window.onload = function() {
            // Activate meal mode (local + server)
            sessionStorage.setItem('mealMode', '1');
            setServerMealMode(true);
            // Restore name
            var nameInput = document.getElementById('meal-name');
            if (nameInput) {
                nameInput.value = sessionStorage.getItem('mealName') || '';
            }
            renderItems();
            // Poll for changes (items added from food pads)
            setInterval(renderItems, 2000);
        };
    </script>
</head>
<body>
    <div class="header">
        <div class="header-icons">
            <a href="/" class="food-link" title="Food Pads">🍎</a>
            <a href="/?pad=amounts" class="amounts-link" title="Set Amount"><i class="fas fa-ruler"></i></a>
            <a href="/meals/build" class="meal-link" title="Build Meal"><i class="fas fa-utensils"></i></a>
            <a href="/notes" class="notes-link" title="Food Notes"><i class="fas fa-sticky-note"></i></a>
            <a href="/edit-foods" class="settings-cog" title="Edit Foods Configuration"><i class="fas fa-cog"></i></a>
        </div>
        <h1 style="color: #4ecdc4;">Building Meal</h1>
    </div>

    <input type="text" id="meal-name" class="meal-name-input" placeholder="Meal name..."
           oninput="updateDoneBtn(); sessionStorage.setItem('mealName', this.value);">

    <div id="meal-items" class="meal-items"></div>
    <div id="meal-totals" class="meal-totals"></div>

    <div class="bottom-nav" style="display: flex; gap: 10px; padding: 15px;">
        <button id="done-btn" class="bottom-nav-btn" onclick="doneMeal()" disabled
                style="background: linear-gradient(135deg, #4ecdc4, #00d4ff); flex: 1;">
            Done
        </button>
        <button class="bottom-nav-btn" onclick="cancelMeal()"
                style="background: linear-gradient(135deg, #ff6b6b, #ee5a24); flex: 0 0 auto; padding: 15px 25px;">
            Cancel
        </button>
    </div>
</body>
</html>
"""


def register_meals_routes(app):
    """Register meal-related routes with the Flask app"""
    from .data import get_all_pads, validate_food_request

    @app.route('/meals/build')
    def meals_build_page():
        return render_template_string(HTML_MEALS_BUILD)

    @app.route('/meals/create', methods=['POST'])
    def meals_create_save():
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        name = (data.get('name') or '').strip()
        items = data.get('items', [])

        if not name:
            return jsonify({'success': False, 'error': 'Meal name is required'}), 400
        if not items:
            return jsonify({'success': False, 'error': 'At least one item is required'}), 400

        meal = {
            'id': generate_meal_id(),
            'name': name,
            'created': datetime.now().isoformat(),
            'items': items
        }

        meals = load_meals()
        meals.append(meal)
        save_meals(meals)

        return jsonify({'success': True, 'meal_id': meal['id'], 'name': name})

    @app.route('/api/meals')
    def api_meals_list():
        meals = load_meals()
        result = []
        for meal in meals:
            total_cal, total_protein = calculate_meal_totals(meal)
            result.append({
                'id': meal['id'],
                'name': meal['name'],
                'item_count': len(meal.get('items', [])),
                'total_calories': total_cal,
                'total_protein': total_protein,
                'created': meal.get('created')
            })
        return jsonify({'meals': result})

    @app.route('/log-meal', methods=['POST'])
    def log_meal():
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        meal_id = data.get('meal_id')
        nonce = data.get('nonce')

        if not meal_id:
            return jsonify({'error': 'No meal_id provided'}), 400

        # Find the meal
        meals = load_meals()
        meal = None
        for m in meals:
            if m['id'] == meal_id:
                meal = m
                break

        if not meal:
            return jsonify({'error': 'Meal not found'}), 404

        meal_uid = generate_meal_log_uid()
        now = datetime.now()
        time_str = now.strftime('%H:%M')

        log_file = get_today_log_file()
        entries = load_today_log()
        backfill_entry_ids(entries)

        # Create meal header entry (zero-calorie marker)
        header_entry = {
            'id': generate_entry_id(),
            'time': time_str,
            'pad': '_meal',
            'food': meal_id,
            'name': meal['name'],
            'amount': 0,
            'amount_display': 'meal',
            'calories': 0,
            'protein': 0,
            'fiber': 0,
            'timestamp': now.isoformat(),
            'meal_uid': meal_uid,
            'is_meal_header': True
        }
        entries.append(header_entry)

        # Create one entry per meal item
        for item in meal.get('items', []):
            if item.get('type') == 'unit':
                cal = item.get('calories', 0)
                prot = item.get('protein', 0)
                fib = item.get('fiber', 0)
                amount = 1
                amount_display = '1 unit'
            else:
                amt = item.get('amount', 100)
                cal = item.get('calories_per_gram', 0) * amt
                prot = item.get('protein_per_gram', 0) * amt
                fib = item.get('fiber_per_gram', 0) * amt
                amount = amt
                amount_display = f"{amt}g"

            food_entry = {
                'id': generate_entry_id(),
                'time': time_str,
                'pad': item.get('pad', '_meal'),
                'food': item.get('food', 'unknown'),
                'name': item.get('name', 'Unknown'),
                'amount': amount,
                'amount_display': amount_display,
                'calories': round(cal, 1),
                'protein': round(prot, 1),
                'fiber': round(fib, 1),
                'timestamp': now.isoformat(),
                'meal_uid': meal_uid
            }
            entries.append(food_entry)

        with open(log_file, 'w') as f:
            json.dump(entries, f, indent=2)

        mark_updated(nonce)

        total_cal, total_protein = calculate_meal_totals(meal)
        return jsonify({
            'status': 'success',
            'meal_name': meal['name'],
            'items_logged': len(meal.get('items', [])),
            'total_calories': total_cal
        })
