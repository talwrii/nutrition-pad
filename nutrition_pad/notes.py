"""
Notes and unknown food resolution functionality.
- Notes page: Add individual notes with Enter key or Add button
- Resolve unknowns: Shows notes alongside unknown entries for resolution
"""
import os
import json
from datetime import date, datetime
from flask import render_template_string, request, jsonify

NOTES_DIR = 'daily_logs'

# --- HTML Templates ---
HTML_NOTES = """
<!DOCTYPE html>
<html>
<head>
    <title>Food Notes</title>
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
        .amounts-link {
            font-size: 1.5em;
            color: rgba(255, 255, 255, 0.7);
            text-decoration: none;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .amounts-link:hover {
            color: #4ecdc4;
            transform: scale(1.1);
            text-shadow: 0 0 10px rgba(78, 205, 196, 0.5);
        }
        
        .notes-container {
            max-width: 800px;
            margin: 30px auto;
            padding: 0 20px;
        }
        
        .add-note-form {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
        }
        
        .note-input {
            flex: 1;
            padding: 15px 20px;
            background: rgba(0, 0, 0, 0.3);
            border: 2px solid rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            color: white;
            font-size: 1.1em;
            outline: none;
        }
        
        .note-input:focus {
            border-color: #00d4ff;
            box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
        }
        
        .note-input::placeholder {
            color: rgba(255, 255, 255, 0.4);
        }
        
        .add-note-btn {
            padding: 15px 25px;
            background: linear-gradient(135deg, #4ecdc4, #00d4ff);
            border: none;
            border-radius: 15px;
            color: white;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            white-space: nowrap;
        }
        
        .add-note-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(78, 205, 196, 0.4);
        }
        
        .add-note-btn:active {
            transform: translateY(0);
        }
        
        .notes-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .note-item {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 15px 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.2s;
        }
        
        .note-item:hover {
            background: rgba(255, 255, 255, 0.12);
        }
        
        .note-item.done {
            display: none;  /* Hide completed notes */
        }
        
        .note-item.done .note-text {
            text-decoration: line-through;
        }
        
        .note-checkbox {
            width: 24px;
            height: 24px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 6px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            flex-shrink: 0;
        }
        
        .note-checkbox:hover {
            border-color: #4ecdc4;
        }
        
        .note-checkbox.checked {
            background: #4ecdc4;
            border-color: #4ecdc4;
        }
        
        .note-checkbox.checked::after {
            content: '✓';
            color: #1a1a2e;
            font-weight: bold;
        }
        
        .note-text {
            flex: 1;
            font-size: 1.1em;
        }
        
        .note-time {
            font-size: 0.85em;
            color: rgba(255, 255, 255, 0.5);
            flex-shrink: 0;
        }
        
        .note-delete {
            color: rgba(255, 255, 255, 0.3);
            cursor: pointer;
            font-size: 1.2em;
            padding: 5px;
            transition: color 0.2s;
        }
        
        .note-delete:hover {
            color: #ff6b6b;
        }
        
        .empty-state {
            text-align: center;
            color: rgba(255, 255, 255, 0.5);
            padding: 40px;
            font-size: 1.1em;
        }
        
        .notes-header {
            text-align: center;
            margin-bottom: 20px;
        }
        
        .notes-header h2 {
            color: #ffd93d;
            font-size: 1.5em;
            margin-bottom: 10px;
        }
        
        .notes-header p {
            color: rgba(255, 255, 255, 0.7);
        }
        
        @media (max-width: 480px) {
            .add-note-btn {
                padding: 15px 18px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Food Notes</h1>
        <div class="header-icons">
            <a href="/?pad=amounts" class="amounts-link" title="Set Amount"><i class="fas fa-ruler"></i></a>
            <a href="/resolve-unknowns" class="notes-link" title="Resolve Items"><i class="fas fa-search"></i></a>
            <a href="/edit-foods" class="settings-cog" title="Edit Foods Configuration"><i class="fas fa-cog"></i></a>
        </div>
        <div class="item-count">{{ date_display }}</div>
    </div>
    
    <div class="notes-container">
        <div class="notes-header">
            <h2>Quick Notes</h2>
            <p>Add foods to look up later</p>
        </div>
        
        <div class="add-note-form">
            <input type="text" 
                   id="noteInput" 
                   class="note-input" 
                   placeholder="Type a note..."
                   onkeypress="handleKeyPress(event)">
            <button class="add-note-btn" onclick="submitNote()">Add</button>
        </div>
        
        <div id="notesList" class="notes-list">
            {% if notes %}
                {% for note in notes %}
                <div class="note-item {% if note.done %}done{% endif %}" data-id="{{ note.id }}">
                    <div class="note-checkbox {% if note.done %}checked{% endif %}" onclick="toggleNote('{{ note.id }}')"></div>
                    <div class="note-text">{{ note.text }}</div>
                    <div class="note-time">{{ note.time }}</div>
                    <div class="note-delete" onclick="deleteNote('{{ note.id }}')">&times;</div>
                </div>
                {% endfor %}
            {% else %}
                <div class="empty-state">No notes yet. Type above and tap Add.</div>
            {% endif %}
        </div>
    </div>
    
    <div class="bottom-nav">
        <button class="bottom-nav-btn" onclick="window.location.href='/'">
            Back to Food Pads
        </button>
        <button class="bottom-nav-btn" onclick="window.location.href='/resolve-unknowns'" style="background: linear-gradient(135deg, #4ecdc4, #00d4ff);">
            Resolve Items
        </button>
    </div>
    
    <script>
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                submitNote();
            }
        }
        
        function submitNote() {
            var input = document.getElementById('noteInput');
            var text = input.value.trim();
            if (text) {
                addNote(text);
                input.value = '';
            }
        }
        
        function addNote(text) {
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/add-note', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    window.location.reload();
                }
            };
            xhr.send(JSON.stringify({ text: text }));
        }
        
        function toggleNote(id) {
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/toggle-note', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    window.location.reload();
                }
            };
            xhr.send(JSON.stringify({ id: id }));
        }
        
        function deleteNote(id) {
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/delete-note', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    window.location.reload();
                }
            };
            xhr.send(JSON.stringify({ id: id }));
        }
    </script>
</body>
</html>
"""

HTML_RESOLVE_UNKNOWNS = """
<!DOCTYPE html>
<html>
<head>
    <title>Resolve Items</title>
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
        .amounts-link {
            font-size: 1.5em;
            color: rgba(255, 255, 255, 0.7);
            text-decoration: none;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .amounts-link:hover {
            color: #4ecdc4;
            transform: scale(1.1);
            text-shadow: 0 0 10px rgba(78, 205, 196, 0.5);
        }
        
        .resolve-container {
            max-width: 900px;
            margin: 30px auto;
            padding: 0 20px;
        }
        
        .item-card {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            backdrop-filter: blur(20px);
            border: 2px solid rgba(255, 255, 255, 0.15);
        }
        
        .item-card.note-card {
            border-color: rgba(255, 107, 107, 0.4);
            background: rgba(255, 107, 107, 0.05);
        }
        
        .item-card.unknown-card {
            border-color: rgba(255, 217, 61, 0.4);
            background: rgba(255, 217, 61, 0.05);
        }
        
        .item-card.resolved {
            border-color: rgba(78, 205, 196, 0.5);
            background: rgba(78, 205, 196, 0.1);
            opacity: 0.7;
        }
        
        .item-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .item-info {
            flex: 1;
        }
        
        .item-type {
            font-size: 0.75em;
            padding: 3px 8px;
            border-radius: 5px;
            font-weight: 600;
            margin-bottom: 5px;
            display: inline-block;
        }
        
        .item-type.note {
            background: rgba(255, 107, 107, 0.3);
            color: #ff6b6b;
        }
        
        .item-type.unknown {
            background: rgba(255, 217, 61, 0.3);
            color: #ffd93d;
        }
        
        .item-name {
            font-size: 1.3em;
            font-weight: 600;
            color: white;
        }
        
        .item-details {
            font-size: 0.95em;
            color: rgba(255, 255, 255, 0.7);
            margin-top: 5px;
        }
        
        .item-time {
            font-size: 0.85em;
            color: rgba(255, 255, 255, 0.5);
        }
        
        .search-box {
            width: 100%;
            padding: 12px 15px;
            background: rgba(0, 0, 0, 0.3);
            border: 2px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            color: white;
            font-size: 1em;
            outline: none;
            margin-bottom: 10px;
        }
        
        .search-box:focus {
            border-color: #00d4ff;
        }
        
        .search-box::placeholder {
            color: rgba(255, 255, 255, 0.4);
        }
        
        .search-results {
            max-height: 200px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            display: none;
        }
        
        .search-results.active {
            display: block;
        }
        
        .search-result {
            padding: 12px 15px;
            cursor: pointer;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            transition: background 0.2s;
        }
        
        .search-result:last-child {
            border-bottom: none;
        }
        
        .search-result:hover {
            background: rgba(0, 212, 255, 0.2);
        }
        
        .search-result-name {
            font-weight: 600;
            margin-bottom: 3px;
        }
        
        .search-result-info {
            font-size: 0.85em;
            color: rgba(255, 255, 255, 0.6);
        }
        
        .search-result-pad {
            font-size: 0.8em;
            color: #4ecdc4;
            margin-top: 3px;
        }
        
        .match-char {
            color: #00d4ff;
            font-weight: bold;
        }
        
        .resolved-badge {
            background: rgba(78, 205, 196, 0.3);
            color: #4ecdc4;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.9em;
            font-weight: 600;
        }
        
        .done-btn {
            background: rgba(78, 205, 196, 0.2);
            border: 1px solid rgba(78, 205, 196, 0.4);
            color: #4ecdc4;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.2s;
            margin-bottom: 10px;
        }
        
        .done-btn:hover {
            background: rgba(78, 205, 196, 0.3);
        }
        
        .empty-state {
            text-align: center;
            color: rgba(255, 255, 255, 0.5);
            padding: 60px 20px;
            font-size: 1.2em;
        }
        
        .empty-state-icon {
            font-size: 3em;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Resolve Items</h1>
        <div class="header-icons">
            <a href="/?pad=amounts" class="amounts-link" title="Set Amount"><i class="fas fa-ruler"></i></a>
            <a href="/notes" class="notes-link" title="Food Notes"><i class="fas fa-sticky-note"></i></a>
            <a href="/edit-foods" class="settings-cog" title="Edit Foods Configuration"><i class="fas fa-cog"></i></a>
        </div>
    </div>
    
    <div class="resolve-container">
        {% if items %}
            {% for item in items %}
            <div class="item-card {{ item.card_type }}-card {% if item.resolved or item.done %}resolved{% endif %}">
                <div class="item-header">
                    <div class="item-info">
                        <span class="item-type {{ item.card_type }}">{{ 'NOTE' if item.card_type == 'note' else 'UNKNOWN' }}</span>
                        <div class="item-name">{{ item.name }}</div>
                        {% if item.details %}
                        <div class="item-details">{{ item.details }}</div>
                        {% endif %}
                    </div>
                    <div class="item-time">{{ item.time }}</div>
                </div>
                
                {% if item.resolved %}
                    <span class="resolved-badge">✓ {{ item.resolved_to }}</span>
                {% elif item.done %}
                    <span class="resolved-badge">✓ Done</span>
                {% else %}
                    {% if item.card_type == 'note' %}
                        <button class="done-btn" onclick="markNoteDone('{{ item.id }}', '{{ item.date_str }}')">Mark Done</button>
                    {% endif %}
                    
                    <input type="text" 
                           class="search-box" 
                           placeholder="Search for food..." 
                           oninput="searchFood(this, '{{ item.card_type }}', '{{ item.id }}', '{{ item.date_str }}')"
                           onfocus="showResults('{{ item.card_type }}-{{ item.id }}')"
                           data-type="{{ item.card_type }}"
                           data-id="{{ item.id }}"
                           data-date="{{ item.date_str }}">
                    <div id="results-{{ item.card_type }}-{{ item.id }}" class="search-results"></div>
                {% endif %}
            </div>
            {% endfor %}
        {% else %}
            <div class="empty-state">
                <div class="empty-state-icon">✨</div>
                <div>All done! No items to resolve.</div>
            </div>
        {% endif %}
    </div>
    
    <div class="bottom-nav">
        <button class="bottom-nav-btn" onclick="window.location.href='/notes'">
            <i class="fas fa-sticky-note"></i> Add Notes
        </button>
        <button class="bottom-nav-btn" onclick="window.location.href='/nutrition'" style="background: linear-gradient(135deg, #4ecdc4, #00d4ff);">
            Back to Dashboard
        </button>
    </div>
    
    <script>
        var allFoods = {{ foods_json|safe }};
        
        function fuzzyMatch(str, query) {
            str = str.toLowerCase();
            query = query.toLowerCase();
            
            if (str.indexOf(query) !== -1) {
                return { match: true, score: 100 + query.length };
            }
            
            var queryIdx = 0;
            var score = 0;
            var lastMatchIdx = -1;
            
            for (var i = 0; i < str.length && queryIdx < query.length; i++) {
                if (str[i] === query[queryIdx]) {
                    queryIdx++;
                    if (lastMatchIdx === i - 1) {
                        score += 5;
                    }
                    score += 1;
                    lastMatchIdx = i;
                }
            }
            
            return { match: queryIdx === query.length, score: score };
        }
        
        function highlightMatch(str, query) {
            var result = '';
            var queryLower = query.toLowerCase();
            var strLower = str.toLowerCase();
            
            var subIdx = strLower.indexOf(queryLower);
            if (subIdx !== -1) {
                return str.substring(0, subIdx) + 
                       '<span class="match-char">' + str.substring(subIdx, subIdx + query.length) + '</span>' +
                       str.substring(subIdx + query.length);
            }
            
            var queryIdx = 0;
            for (var i = 0; i < str.length; i++) {
                if (queryIdx < query.length && strLower[i] === queryLower[queryIdx]) {
                    result += '<span class="match-char">' + str[i] + '</span>';
                    queryIdx++;
                } else {
                    result += str[i];
                }
            }
            
            return result;
        }
        
        function searchFood(input, itemType, itemId, dateStr) {
            var query = input.value.trim();
            var resultsEl = document.getElementById('results-' + itemType + '-' + itemId);
            
            if (query.length < 1) {
                resultsEl.classList.remove('active');
                return;
            }
            
            var matches = [];
            
            for (var i = 0; i < allFoods.length; i++) {
                var food = allFoods[i];
                var result = fuzzyMatch(food.name, query);
                if (result.match) {
                    matches.push({
                        food: food,
                        score: result.score
                    });
                }
            }
            
            matches.sort(function(a, b) { return b.score - a.score; });
            matches = matches.slice(0, 10);
            
            if (matches.length === 0) {
                resultsEl.innerHTML = '<div class="search-result"><div class="search-result-name">No matches found</div></div>';
                resultsEl.classList.add('active');
                return;
            }
            
            var html = '';
            for (var i = 0; i < matches.length; i++) {
                var food = matches[i].food;
                var highlighted = highlightMatch(food.name, query);
                var info = food.type === 'unit' 
                    ? food.calories + ' cal • ' + food.protein + 'g protein per unit'
                    : food.calories_per_gram.toFixed(2) + ' cal/g • ' + food.protein_per_gram.toFixed(3) + 'g protein/g';
                
                html += '<div class="search-result" onclick="selectFood(\'' + itemType + '\', \'' + itemId + '\', \'' + food.pad_key + '\', \'' + food.food_key + '\', \'' + dateStr + '\')">';
                html += '<div class="search-result-name">' + highlighted + '</div>';
                html += '<div class="search-result-info">' + info + '</div>';
                html += '<div class="search-result-pad">' + food.pad_name + '</div>';
                html += '</div>';
            }
            
            resultsEl.innerHTML = html;
            resultsEl.classList.add('active');
        }
        
        function showResults(key) {
            var resultsEl = document.getElementById('results-' + key);
            var parts = key.split('-');
            var input = document.querySelector('[data-type="' + parts[0] + '"][data-id="' + parts[1] + '"]');
            if (input && input.value.trim().length > 0) {
                resultsEl.classList.add('active');
            }
        }
        
        function selectFood(itemType, itemId, padKey, foodKey, dateStr) {
            var xhr = new XMLHttpRequest();
            var url = itemType === 'note' ? '/resolve-note' : '/resolve-unknown';
            
            xhr.open('POST', url, true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        window.location.reload();
                    } else {
                        alert('Error resolving item');
                    }
                }
            };
            
            var data = {
                pad_key: padKey,
                food_key: foodKey,
                date_str: dateStr
            };
            
            if (itemType === 'note') {
                data.note_id = itemId;
            } else {
                data.entry_index = parseInt(itemId);
            }
            
            xhr.send(JSON.stringify(data));
        }
        
        function markNoteDone(noteId, dateStr) {
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/toggle-note', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    window.location.reload();
                }
            };
            xhr.send(JSON.stringify({ id: noteId, date_str: dateStr }));
        }
        
        document.addEventListener('click', function(e) {
            if (!e.target.classList.contains('search-box') && !e.target.closest('.search-results')) {
                var allResults = document.querySelectorAll('.search-results');
                for (var i = 0; i < allResults.length; i++) {
                    allResults[i].classList.remove('active');
                }
            }
        });
    </script>
</body>
</html>
"""

def get_notes_file():
    """Get path to today's notes file (JSON format)"""
    today = date.today().strftime('%Y-%m-%d')
    return os.path.join(NOTES_DIR, f'{today}_notes.json')

def load_notes():
    """Load today's notes as list of dicts"""
    notes_file = get_notes_file()
    if not os.path.exists(notes_file):
        return []
    
    try:
        with open(notes_file, 'r') as f:
            return json.load(f)
    except:
        return []

def save_notes(notes):
    """Save notes list to file"""
    notes_file = get_notes_file()
    os.makedirs(os.path.dirname(notes_file), exist_ok=True)
    
    with open(notes_file, 'w') as f:
        json.dump(notes, f, indent=2)

def get_all_foods_flat(pads):
    """Get all foods as a flat list for fuzzy search"""
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
            
            foods.append(food_entry)
    
    return foods

def get_unknown_entries(log_entries):
    """Get unknown entries from today's log with their indices"""
    unknowns = []
    for i, entry in enumerate(log_entries):
        if 'unknown' in entry.get('food', '').lower() or 'unknown' in entry.get('name', '').lower():
            entry_copy = dict(entry)
            entry_copy['index'] = i
            entry_copy['resolved'] = bool(entry.get('resolved_to'))
            unknowns.append(entry_copy)
    return unknowns

def register_notes_routes(app):
    """Register notes routes with the Flask app"""
    
    from .data import load_today_log, get_all_pads, get_food_data, LOGS_DIR
    from .polling import mark_updated
    import json as json_module
    
    @app.route('/notes')
    def notes_page():
        notes = load_notes()
        date_display = date.today().strftime('%A, %B %d, %Y')
        
        return render_template_string(HTML_NOTES,
                                    notes=notes,
                                    date_display=date_display)
    
    @app.route('/add-note', methods=['POST'])
    def add_note():
        data = request.json
        if not data or 'text' not in data:
            return jsonify({'error': 'No text'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'error': 'Empty text'}), 400
        
        notes = load_notes()
        
        new_note = {
            'id': datetime.now().strftime('%Y%m%d%H%M%S%f'),
            'text': text,
            'time': datetime.now().strftime('%H:%M'),
            'timestamp': datetime.now().isoformat(),
            'done': False
        }
        
        notes.insert(0, new_note)
        save_notes(notes)
        
        return jsonify({'status': 'success', 'note': new_note})
    
    @app.route('/toggle-note', methods=['POST'])
    def toggle_note():
        data = request.json
        if not data or 'id' not in data:
            return jsonify({'error': 'No id'}), 400
        
        note_id = data['id']
        date_str = data.get('date_str', date.today().strftime('%Y-%m-%d'))
        
        # Load notes for the specified date
        notes_file = os.path.join(NOTES_DIR, f'{date_str}_notes.json')
        if not os.path.exists(notes_file):
            return jsonify({'error': 'Notes file not found'}), 400
        
        try:
            with open(notes_file, 'r') as f:
                notes = json.load(f)
        except:
            return jsonify({'error': 'Could not load notes'}), 400
        
        for note in notes:
            if note['id'] == note_id:
                note['done'] = not note.get('done', False)
                break
        
        with open(notes_file, 'w') as f:
            json.dump(notes, f, indent=2)
        
        return jsonify({'status': 'success'})
    
    @app.route('/delete-note', methods=['POST'])
    def delete_note():
        data = request.json
        if not data or 'id' not in data:
            return jsonify({'error': 'No id'}), 400
        
        note_id = data['id']
        notes = load_notes()
        notes = [n for n in notes if n['id'] != note_id]
        save_notes(notes)
        
        return jsonify({'status': 'success'})
    
    @app.route('/resolve-unknowns')
    def resolve_unknowns_page():
        from datetime import timedelta
        
        pads = get_all_pads()
        all_foods = get_all_foods_flat(pads)
        
        items = []
        
        # Load from today and yesterday
        for days_ago in [0, 1]:
            target_date = date.today() - timedelta(days=days_ago)
            date_str = target_date.strftime('%Y-%m-%d')
            date_label = 'Today' if days_ago == 0 else 'Yesterday'
            
            # Load notes for this day
            notes_file = os.path.join(NOTES_DIR, f'{date_str}_notes.json')
            if os.path.exists(notes_file):
                try:
                    with open(notes_file, 'r') as f:
                        day_notes = json.load(f)
                    for note in day_notes:
                        items.append({
                            'card_type': 'note',
                            'id': note['id'],
                            'name': note['text'],
                            'details': date_label,
                            'time': note.get('time', ''),
                            'timestamp': note.get('timestamp', ''),
                            'done': note.get('done', False),
                            'resolved': note.get('resolved', False),
                            'resolved_to': note.get('resolved_to', ''),
                            'date_str': date_str
                        })
                except:
                    pass
            
            # Load unknown entries for this day
            log_file = os.path.join(LOGS_DIR, f'{date_str}.json')
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        log_entries = json.load(f)
                    for i, entry in enumerate(log_entries):
                        if 'unknown' in entry.get('food', '').lower() or 'unknown' in entry.get('name', '').lower():
                            items.append({
                                'card_type': 'unknown',
                                'id': str(i),
                                'name': entry.get('name', 'Unknown'),
                                'details': f"{entry.get('amount_display', '')} • {date_label}",
                                'time': entry.get('time', ''),
                                'timestamp': entry.get('timestamp', ''),
                                'done': False,
                                'resolved': bool(entry.get('resolved_to')),
                                'resolved_to': entry.get('resolved_to', ''),
                                'date_str': date_str
                            })
                except:
                    pass
        
        # Sort: unresolved first, then by time
        unresolved = [i for i in items if not i.get('done') and not i.get('resolved')]
        resolved = [i for i in items if i.get('done') or i.get('resolved')]
        items = unresolved + resolved
        
        return render_template_string(HTML_RESOLVE_UNKNOWNS,
                                    items=items,
                                    foods_json=json_module.dumps(all_foods))
    
    @app.route('/resolve-unknown', methods=['POST'])
    def resolve_unknown():
        data = request.json
        if not data:
            return jsonify({'error': 'No data'}), 400
        
        entry_index = data.get('entry_index')
        pad_key = data.get('pad_key')
        food_key = data.get('food_key')
        date_str = data.get('date_str', date.today().strftime('%Y-%m-%d'))
        
        if entry_index is None or not pad_key or not food_key:
            return jsonify({'error': 'Missing data'}), 400
        
        # Load log for the specified date
        log_file = os.path.join(LOGS_DIR, f'{date_str}.json')
        if not os.path.exists(log_file):
            return jsonify({'error': 'Log file not found'}), 400
        
        try:
            with open(log_file, 'r') as f:
                log_entries = json.load(f)
        except:
            return jsonify({'error': 'Could not load log'}), 400
        
        if entry_index < 0 or entry_index >= len(log_entries):
            return jsonify({'error': 'Invalid entry index'}), 400
        
        entry = log_entries[entry_index]
        
        try:
            food_data = get_food_data(pad_key, food_key)
        except:
            return jsonify({'error': 'Food not found'}), 400
        
        amount = entry.get('amount', 100)
        
        if food_data.get('type') == 'unit':
            calories = food_data.get('calories', 0) * amount
            protein = food_data.get('protein', 0) * amount
        else:
            calories = food_data.get('calories_per_gram', 0) * amount
            protein = food_data.get('protein_per_gram', 0) * amount
        
        entry['resolved_to'] = food_data.get('name', food_key)
        entry['resolved_pad'] = pad_key
        entry['resolved_food'] = food_key
        entry['calories'] = round(calories, 1)
        entry['protein'] = round(protein, 1)
        
        with open(log_file, 'w') as f:
            json_module.dump(log_entries, f, indent=2)
        
        mark_updated("resolve_unknown")
        
        return jsonify({'status': 'success', 'calories': entry['calories'], 'protein': entry['protein']})
    
    @app.route('/resolve-note', methods=['POST'])
    def resolve_note():
        """Resolve a note by attaching a food to it"""
        data = request.json
        if not data:
            return jsonify({'error': 'No data'}), 400
        
        note_id = data.get('note_id')
        pad_key = data.get('pad_key')
        food_key = data.get('food_key')
        date_str = data.get('date_str', date.today().strftime('%Y-%m-%d'))
        
        if not note_id or not pad_key or not food_key:
            return jsonify({'error': 'Missing data'}), 400
        
        try:
            food_data = get_food_data(pad_key, food_key)
        except:
            return jsonify({'error': 'Food not found'}), 400
        
        # Load notes for the specified date
        notes_file = os.path.join(NOTES_DIR, f'{date_str}_notes.json')
        if not os.path.exists(notes_file):
            return jsonify({'error': 'Notes file not found'}), 400
        
        try:
            with open(notes_file, 'r') as f:
                notes = json.load(f)
        except:
            return jsonify({'error': 'Could not load notes'}), 400
        
        for note in notes:
            if note['id'] == note_id:
                note['done'] = True
                note['resolved'] = True
                note['resolved_to'] = food_data.get('name', food_key)
                note['resolved_pad'] = pad_key
                note['resolved_food'] = food_key
                break
        
        with open(notes_file, 'w') as f:
            json.dump(notes, f, indent=2)
        
        return jsonify({'status': 'success'})