"""
Calories timeline view - shows when food was eaten with cumulative graphs.
Tracks calories, protein, and fiber with drink markers.
"""

from flask import render_template_string
from datetime import datetime, date

HTML_CALORIES = """
<!DOCTYPE html>
<html>
<head>
    <title>Calories Timeline</title>
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
        
        .timeline-container {
            max-width: 900px;
            margin: 20px auto;
            padding: 0 15px;
        }
        
        /* Graph section */
        .graph-section {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 25px;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .graph-title {
            font-size: 1.1em;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 15px;
            text-align: center;
        }
        
        /* Cumulative graph using SVG */
        .cumulative-graph {
            position: relative;
            height: 180px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            overflow: hidden;
        }
        
        .cumulative-graph svg {
            width: 100%;
            height: 100%;
        }
        
        .graph-line {
            fill: none;
            stroke-width: 2.5;
            stroke-linecap: round;
            stroke-linejoin: round;
        }
        
        .calories-line { stroke: #ff6b6b; }
        .protein-line { stroke: #4ecdc4; }
        .fiber-line { stroke: #ffd93d; }
        
        .graph-area {
            opacity: 0.15;
        }
        .calories-area { fill: #ff6b6b; }
        .protein-area { fill: #4ecdc4; }
        
        /* Graph legend */
        .graph-legend {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.9em;
        }
        
        .legend-color {
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }
        
        .legend-color.calories { background: #ff6b6b; }
        .legend-color.protein { background: #4ecdc4; }
        .legend-color.fiber { background: #ffd93d; }
        
        /* Summary stats */
        .summary-stats {
            display: flex;
            justify-content: space-around;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-size: 1.8em;
            font-weight: 700;
        }
        
        .stat-value.calories { color: #ff6b6b; }
        .stat-value.protein { color: #4ecdc4; }
        .stat-value.fiber { color: #ffd93d; }
        
        .stat-label {
            font-size: 0.8em;
            color: rgba(255, 255, 255, 0.6);
            text-transform: uppercase;
        }
        
        /* Entries list */
        .entries-section {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 100px;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .entries-title {
            font-size: 1.1em;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 15px;
        }
        
        .entry-item {
            display: grid;
            grid-template-columns: 50px 1fr auto auto auto;
            gap: 10px;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .entry-item:last-child {
            border-bottom: none;
        }
        
        .entry-time {
            color: rgba(255, 255, 255, 0.5);
            font-size: 0.9em;
        }
        
        .entry-food {
            font-weight: 500;
        }
        
        .entry-food .amount {
            font-size: 0.85em;
            color: rgba(255, 255, 255, 0.5);
            margin-left: 8px;
        }
        
        .entry-calories {
            color: #ff6b6b;
            font-weight: 600;
            text-align: right;
            min-width: 60px;
        }
        
        .entry-protein {
            color: #4ecdc4;
            font-weight: 600;
            text-align: right;
            min-width: 50px;
        }
        
        .entry-running {
            color: rgba(255, 255, 255, 0.4);
            font-size: 0.85em;
            text-align: right;
            min-width: 60px;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: rgba(255, 255, 255, 0.5);
        }
        
        @media (max-width: 600px) {
            .entry-item {
                grid-template-columns: 45px 1fr auto;
            }
            .entry-protein, .entry-running {
                display: none;
            }
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
        <h1>Calories Timeline</h1>
    </div>
    
    <div class="timeline-container">
        <!-- Summary stats -->
        <div class="summary-stats">
            <div class="stat-item">
                <div class="stat-value calories">{{ total_calories }}</div>
                <div class="stat-label">Calories</div>
            </div>
            <div class="stat-item">
                <div class="stat-value protein">{{ total_protein }}g</div>
                <div class="stat-label">Protein</div>
            </div>
            <div class="stat-item">
                <div class="stat-value fiber">{{ total_fiber }}g</div>
                <div class="stat-label">Fiber</div>
            </div>
        </div>
        
        <!-- Cumulative graph -->
        <div class="graph-section">
            <div class="graph-title">Cumulative Intake</div>
            <div class="cumulative-graph">
                <svg viewBox="0 0 100 100" preserveAspectRatio="none">
                    <!-- Calories area and line -->
                    <path class="graph-area calories-area" d="{{ calories_area_path }}"/>
                    <path class="graph-line calories-line" d="{{ calories_line_path }}"/>
                    
                    <!-- Protein area and line (scaled 10x) -->
                    <path class="graph-area protein-area" d="{{ protein_area_path }}"/>
                    <path class="graph-line protein-line" d="{{ protein_line_path }}"/>
                    
                    <!-- Fiber line (scaled 20x) -->
                    <path class="graph-line fiber-line" d="{{ fiber_line_path }}"/>
                </svg>
            </div>
            <div class="graph-legend">
                <div class="legend-item">
                    <div class="legend-color calories"></div>
                    <span>Calories</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color protein"></div>
                    <span>Protein (×10)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color fiber"></div>
                    <span>Fiber (×20)</span>
                </div>
            </div>
        </div>
        
        <!-- Entries list -->
        <div class="entries-section">
            <div class="entries-title">Today's Entries</div>
            {% if entries %}
                {% set running_cal = namespace(value=0) %}
                {% set running_prot = namespace(value=0) %}
                {% for entry in entries %}
                {% set running_cal.value = running_cal.value + entry.calories %}
                {% set running_prot.value = running_prot.value + entry.protein %}
                <div class="entry-item with-running">
                    <div class="entry-time">{{ entry.time }}</div>
                    <div class="entry-food">
                        {{ entry.name }}
                        <span class="amount">{{ entry.amount_display }}</span>
                    </div>
                    <div class="entry-calories">{{ entry.calories|round|int }} cal</div>
                    <div class="entry-protein">{{ entry.protein|round(1) }}g</div>
                    <div class="entry-running">Σ {{ running_cal.value|round|int }}</div>
                </div>
                {% endfor %}
            {% else %}
                <div class="empty-state">No entries yet today</div>
            {% endif %}
        </div>
    </div>
    
    <div class="bottom-nav">
        <button class="bottom-nav-btn" onclick="window.location.href='/'">
            Back to Food Pads
        </button>
        <button class="bottom-nav-btn" onclick="window.location.href='/nutrition'" style="background: linear-gradient(135deg, #4ecdc4, #00d4ff);">
            Dashboard
        </button>
    </div>
</body>
</html>
"""

def time_to_x(time_str):
    """Convert time string (HH:MM) to x position (0-100) on graph"""
    try:
        parts = time_str.split(':')
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
    except (ValueError, IndexError):
        return 50  # default to middle
    
    # Minutes since 6am (6am = 360 minutes from midnight)
    total_minutes = hour * 60 + minute
    minutes_since_6am = total_minutes - 360
    
    # Wrap around if before 6am (treat as next day)
    if minutes_since_6am < 0:
        minutes_since_6am += 1440
    
    # Scale to 0-100 (18 hours = 1080 minutes from 6am to midnight)
    x = (minutes_since_6am / 1080) * 100
    return max(0, min(100, x))


def build_cumulative_path(entries, value_key, max_value, scale_factor=1):
    """Build SVG path for cumulative line graph"""
    if not entries:
        return "M 0 100 L 100 100", "M 0 100 L 100 100 L 0 100 Z"
    
    points = []
    running_total = 0
    
    # Start at 0
    points.append((0, 100))
    
    for entry in entries:
        x = time_to_x(entry.get('time', '12:00'))
        running_total += entry.get(value_key, 0) * scale_factor
        y = 100 - (running_total / max_value * 100) if max_value > 0 else 100
        y = max(0, min(100, y))
        points.append((x, y))
    
    # Extend to end of day at final value
    if points:
        points.append((100, points[-1][1]))
    
    # Build line path
    line_path = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in points)
    
    # Build area path (closed shape)
    area_path = line_path + f" L 100 100 L 0 100 Z"
    
    return line_path, area_path


def register_calories_routes(app):
    """Register calories timeline routes with the Flask app"""
    
    from .data import load_today_log, LOGS_DIR
    
    @app.route('/calories')
    def calories_timeline():
        entries = load_today_log()
        
        # Ensure fiber field exists for all entries
        for entry in entries:
            if 'fiber' not in entry:
                entry['fiber'] = 0
        
        # Calculate totals
        total_calories = sum(entry.get('calories', 0) for entry in entries)
        total_protein = sum(entry.get('protein', 0) for entry in entries)
        total_fiber = sum(entry.get('fiber', 0) for entry in entries)
        
        # Determine max values for scaling
        max_calories = max(total_calories, 2000)  # At least 2000 cal scale
        
        # Build cumulative graph paths
        # Protein scaled by 10x, fiber by 20x to show on same graph as calories
        calories_line, calories_area = build_cumulative_path(entries, 'calories', max_calories)
        protein_line, protein_area = build_cumulative_path(entries, 'protein', max_calories, scale_factor=10)
        fiber_line, _ = build_cumulative_path(entries, 'fiber', max_calories, scale_factor=20)
        
        return render_template_string(HTML_CALORIES,
                                    entries=entries,
                                    total_calories=round(total_calories),
                                    total_protein=round(total_protein, 1),
                                    total_fiber=round(total_fiber, 1),
                                    calories_line_path=calories_line,
                                    calories_area_path=calories_area,
                                    protein_line_path=protein_line,
                                    protein_area_path=protein_area,
                                    fiber_line_path=fiber_line)