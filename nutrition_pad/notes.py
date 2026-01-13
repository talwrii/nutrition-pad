"""
Food notes functionality.
"""

from flask import render_template_string

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
        .settings-cog, .food-link, .notes-link {
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
        .food-link:hover {
            transform: scale(1.2);
            filter: drop-shadow(0 0 8px rgba(255, 100, 100, 0.6));
        }
        .notes-link:hover {
            color: #ff6b6b;
            transform: scale(1.1);
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-icons">
            <a href="/" class="food-link" title="Food Pads">🍎</a>
            <a href="/notes" class="notes-link" title="Food Notes"><i class="fas fa-sticky-note"></i></a>
            <a href="/edit-foods" class="settings-cog" title="Edit Foods Configuration"><i class="fas fa-cog"></i></a>
        </div>
        <h1>Food Notes</h1>
    </div>
    <div style="max-width: 600px; margin: 20px auto; padding: 20px; text-align: center; color: rgba(255,255,255,0.5);">
        No notes yet
    </div>
    <div class="bottom-nav">
        <button class="bottom-nav-btn" onclick="window.location.href='/'">Back to Food Pads</button>
    </div>
</body>
</html>
"""

HTML_RESOLVE = """
<!DOCTYPE html>
<html>
<head>
    <title>Resolve Unknowns</title>
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
        .settings-cog, .food-link, .notes-link {
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
        .food-link:hover {
            transform: scale(1.2);
            filter: drop-shadow(0 0 8px rgba(255, 100, 100, 0.6));
        }
        .notes-link:hover {
            color: #ff6b6b;
            transform: scale(1.1);
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-icons">
            <a href="/" class="food-link" title="Food Pads">🍎</a>
            <a href="/notes" class="notes-link" title="Food Notes"><i class="fas fa-sticky-note"></i></a>
            <a href="/edit-foods" class="settings-cog" title="Edit Foods Configuration"><i class="fas fa-cog"></i></a>
        </div>
        <h1>Resolve Unknowns</h1>
    </div>
    <div style="max-width: 600px; margin: 20px auto; padding: 20px; text-align: center; color: rgba(255,255,255,0.5);">
        No unknown entries to resolve
    </div>
    <div class="bottom-nav">
        <button class="bottom-nav-btn" onclick="window.location.href='/'">Back to Food Pads</button>
    </div>
</body>
</html>
"""

def register_notes_routes(app):
    @app.route('/notes')
    def notes_page():
        return render_template_string(HTML_NOTES)
    
    @app.route('/resolve-unknowns')
    def resolve_unknowns():
        return render_template_string(HTML_RESOLVE)