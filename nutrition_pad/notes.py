"""
Notes and unknown food resolution functionality.
"""
import os
import json
from datetime import date, datetime
from flask import render_template_string, request, jsonify

NOTES_DIR = 'daily_logs'

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
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 10px;
        }
        .settings-cog, .notes-link, .amounts-link, .food-link {
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
        }
        .notes-link:hover {
            color: #ff6b6b;
            transform: scale(1.1);
        }
        .amounts-link:hover {
            color: #4ecdc4;
            transform: scale(1.1);
        }
        .food-link:hover {
            transform: scale(1.2);
        }
        .title-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }
        .title-row h2 {
            color: #ffd93d;
            font-size: 1.5em;
            margin: 0;
        }
        .title-amounts-link {
            font-size: 1.3em;
            color: #4ecdc4;
            text-decoration: none;
            padding: 8px 12px;
            background: rgba(78, 205, 196, 0.15);
            border: 2px solid rgba(78, 205, 196, 0.3);
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        .title-amounts-link:hover {
            background: rgba(78, 205, 196, 0.25);
            border-color: #4ecdc4;
            transform: scale(1.05);
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
            min-width: 80px;
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
            opacity: 0.5;
            background: rgba(78, 205, 196, 0.1);
            border-color: rgba(78, 205, 196, 0.3);
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
    </style>
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
        <h1>Food Notes</h1>
        <div class="item-count">{{ date_display }}</div>
    </div>
    <div class="notes-container">
        <div class="notes-header">
            <a href="/?pad=amounts" class="title-amounts-link" title="Set Amount">📏 Amounts</a>
        </div>
        <div class="add-note-form">
            <input type="text"
                   id="noteInput"
                   class="note-input"
                   placeholder="Type a note and press Enter..."
                   onkeypress="handleKeyPress(event)"
                   autofocus>
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
                <div class="empty-state">No notes yet. Type above and press Enter.</div>
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

def get_notes_file():
    today = date.today().strftime('%Y-%m-%d')
    return os.path.join(NOTES_DIR, f'{today}_notes.json')

def load_notes():
    notes_file = get_notes_file()
    if not os.path.exists(notes_file):
        return []
    try:
        with open(notes_file, 'r') as f:
            return json.load(f)
    except:
        return []

def save_notes(notes):
    notes_file = get_notes_file()
    os.makedirs(os.path.dirname(notes_file), exist_ok=True)
    with open(notes_file, 'w') as f:
        json.dump(notes, f, indent=2)

def register_notes_routes(app):
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
        return render_template_string("<html><body><h1>Resolve Unknowns</h1></body></html>")