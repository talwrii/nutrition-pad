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
            height: 220px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            overflow: visible;
            margin-top: 30px;
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

        .entry-dot {
            fill: #ff6b6b;
            cursor: pointer;
        }
        .entry-dot:hover {
            fill: #fff;
            r: 2.5;
        }
        .graph-tooltip {
            position: absolute;
            top: 8px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            padding: 6px 12px;
            font-size: 0.8em;
            color: #fff;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.15s;
            z-index: 10;
        }
        .graph-tooltip.visible { opacity: 1; }
        .graph-tooltip .tt-name { font-weight: 600; }
        .graph-tooltip .tt-detail { color: rgba(255,255,255,0.6); margin-left: 8px; }

        .hour-labels {
            display: flex;
            justify-content: space-between;
            padding: 4px 0 0 0;
        }
        .hour-label {
            font-size: 0.7em;
            color: rgba(255, 255, 255, 0.4);
            width: 0;
            text-align: center;
        }
        .hour-label:first-child { text-align: left; width: auto; }
        .hour-label:last-child { text-align: right; width: auto; }
        
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
        .stat-delta {
            font-size: 0.85em;
            font-weight: 600;
            margin-top: 2px;
        }
        
        /* Window bars */
        .window-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
        }
        .window-label {
            width: 45px;
            font-size: 0.8em;
            color: rgba(255, 255, 255, 0.6);
            text-align: right;
            flex-shrink: 0;
        }
        .window-bar-bg {
            flex: 1;
            height: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
            overflow: hidden;
        }
        .window-bar {
            height: 100%;
            background: linear-gradient(90deg, #ff6b6b, #ff8e8e);
            border-radius: 4px;
            min-width: 2px;
        }
        .window-cal {
            width: 110px;
            font-size: 0.8em;
            color: rgba(255, 255, 255, 0.6);
            flex-shrink: 0;
        }
        .window-row { cursor: pointer; }
        .window-foods {
            display: none;
            margin: 0 0 8px 53px;
            padding: 6px 10px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 6px;
            font-size: 0.8em;
        }
        .window-foods.open { display: block; }
        .window-food-item {
            display: flex;
            justify-content: space-between;
            padding: 2px 0;
            color: rgba(255, 255, 255, 0.6);
        }
        .window-food-item .wf-cal { color: #ff6b6b; }

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
            grid-template-columns: 40px 1fr auto auto auto auto;
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
            <a href="/nutrition" class="notes-link" title="Dashboard"><i class="fas fa-chart-pie"></i></a>
            <a href="/notes" class="notes-link" title="Food Notes"><i class="fas fa-sticky-note"></i></a>
            <a href="/edit-foods" class="settings-cog" title="Edit Foods Configuration"><i class="fas fa-cog"></i></a>
        </div>
        <div style="display: flex; align-items: center; justify-content: center; gap: 20px;">
            <a href="/calories?date={{ prev_date }}" style="color: rgba(255,255,255,0.7); text-decoration: none; font-size: 1.5em; padding: 10px;">&larr;</a>
            <h1 style="margin: 0;">{{ title }}</h1>
            {% if not is_today %}
            <a href="/calories?date={{ next_date }}" style="color: rgba(255,255,255,0.7); text-decoration: none; font-size: 1.5em; padding: 10px;">&rarr;</a>
            {% else %}
            <span style="width: 44px;"></span>
            {% endif %}
        </div>
    </div>
    
    <div class="timeline-container">
        <!-- Summary stats -->
        <div class="summary-stats">
            <div class="stat-item">
                <div class="stat-value calories">{{ total_calories }}</div>
                <div class="stat-label">Calories</div>
                {% if cal_delta != 0 %}
                <div class="stat-delta" style="color: {{ '#4ecdc4' if cal_delta < 0 else '#ff6b6b' }};">
                    {{ '%+d'|format(cal_delta) }}
                </div>
                {% endif %}
            </div>
            <div class="stat-item">
                <div class="stat-value protein">{{ cal_per_protein }}</div>
                <div class="stat-label">kcal/g protein</div>
                {% if cpp_delta is not none %}
                <div class="stat-delta" style="color: {{ '#4ecdc4' if cpp_delta < 0 else '#ff6b6b' }};">
                    {{ '%+.1f'|format(cpp_delta) }}
                </div>
                {% endif %}
            </div>
            <div class="stat-item">
                <div class="stat-value fiber">{{ cal_per_fiber }}</div>
                <div class="stat-label">kcal/g fiber</div>
                {% if cpf_delta is not none %}
                <div class="stat-delta" style="color: {{ '#4ecdc4' if cpf_delta < 0 else '#ff6b6b' }};">
                    {{ '%+.1f'|format(cpf_delta) }}
                </div>
                {% endif %}
            </div>
        </div>
        
        <!-- Cumulative graph -->
        <div class="graph-section">
            <div class="graph-title">Cumulative Intake</div>
            <div class="cumulative-graph">
                <svg viewBox="0 0 100 100" preserveAspectRatio="none">
                    <!-- Hour grid lines -->
                    {% for h in range(0, 25, 6) %}
                    <line x1="{{ h / 24 * 100 }}" y1="0" x2="{{ h / 24 * 100 }}" y2="100"
                          stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/>
                    {% endfor %}

                    <!-- Calories area and line -->
                    <path class="graph-area calories-area" d="{{ calories_area_path }}"/>
                    <path class="graph-line calories-line" d="{{ calories_line_path }}"/>

                    <!-- kcal/g protein ratio line -->
                    <path class="graph-line protein-line" d="{{ protein_line_path }}"/>

                    <!-- kcal/g fiber ratio line -->
                    <path class="graph-line fiber-line" d="{{ fiber_line_path }}"/>

                    <!-- Entry dots on calorie line -->
                    {% for dot in entry_dots %}
                    <circle class="entry-dot" cx="{{ dot.x }}" cy="{{ dot.y }}" r="1.5"
                            data-name="{{ dot.name }}" data-time="{{ dot.time }}"
                            data-cal="{{ dot.calories }}" data-protein="{{ dot.protein }}"
                            data-fiber="{{ dot.fiber }}" data-amount="{{ dot.amount }}"
                            data-ccal="{{ dot.cum_cal }}" data-cprot="{{ dot.cum_protein }}"
                            data-cfib="{{ dot.cum_fiber }}" data-pct="{{ dot.pct }}"/>
                    {% endfor %}
                </svg>
                <div class="graph-tooltip" id="graphTooltip"></div>
            </div>
            <script>
            (function() {
                var tip = document.getElementById('graphTooltip');
                document.querySelectorAll('.entry-dot').forEach(function(dot) {
                    dot.addEventListener('mouseenter', function() {
                        var n = dot.getAttribute('data-name');
                        var t = dot.getAttribute('data-time');
                        var c = dot.getAttribute('data-cal');
                        var p = dot.getAttribute('data-protein');
                        var f = dot.getAttribute('data-fiber');
                        var a = dot.getAttribute('data-amount');
                        var cc = dot.getAttribute('data-ccal');
                        var cp = dot.getAttribute('data-cprot');
                        var cf = dot.getAttribute('data-cfib');
                        var pct = dot.getAttribute('data-pct');
                        tip.innerHTML =
                            '<div style="font-weight:600;margin-bottom:3px;">' + n + ' <span style="color:rgba(255,255,255,0.5)">' + a + ' @ ' + t + '</span></div>' +
                            '<div><span style="color:#ff6b6b">' + c + ' cal</span> · <span style="color:#4ecdc4">' + p + 'g prot</span> · <span style="color:#ffd93d">' + f + 'g fiber</span></div>' +
                            '<div style="margin-top:3px;color:rgba(255,255,255,0.5);">\u03A3 <span style="color:#ff6b6b">' + cc + ' cal</span> · <span style="color:#4ecdc4">' + cp + 'g prot</span> · <span style="color:#ffd93d">' + cf + 'g fiber</span> · <span style="color:#fff">' + pct + '%</span> of day</div>';
                        tip.classList.add('visible');
                    });
                    dot.addEventListener('mouseleave', function() {
                        tip.classList.remove('visible');
                    });
                });
            })();
            </script>
            <div class="hour-labels">
                {% for h in range(0, 25, 3) %}
                <span class="hour-label">{{ '%02d'|format(h % 24) }}</span>
                {% endfor %}
            </div>
            <div class="graph-legend">
                <div class="legend-item">
                    <div class="legend-color calories"></div>
                    <span>Calories</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color protein"></div>
                    <span>kcal/g protein</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color fiber"></div>
                    <span>kcal/g fiber</span>
                </div>
            </div>
        </div>
        
        <!-- 2-hour window breakdown -->
        {% if windows_sorted %}
        <div class="graph-section" style="margin-bottom: 25px;">
            <div class="graph-title">Calories by 2-Hour Window</div>
            {% set wcum = namespace(value=0) %}
            {% for wdata in windows_sorted %}
            {% set wcum.value = wcum.value + wdata.cal %}
            <div class="window-row" onclick="this.nextElementSibling.classList.toggle('open')">
                <div class="window-label">{{ wdata.label }}</div>
                <div class="window-bar-bg">
                    <div class="window-bar" style="width: {{ (wdata.cal / max_window_cal * 100)|round }}%;"></div>
                </div>
                <div class="window-cal">{{ wdata.cal|round|int }} cal <span style="color:rgba(255,255,255,0.4);">{{ (wdata.cal / total_calories * 100)|round|int }}%</span> <span style="color:rgba(255,255,255,0.3);">{{ (wcum.value / total_calories * 100)|round|int }}%</span></div>
            </div>
            <div class="window-foods">
                {% set fcum = namespace(value=0) %}
                {% for food in wdata.foods %}
                {% set fcum.value = fcum.value + food.calories %}
                <div class="window-food-item">
                    <span>{{ food.name }} <span style="color:rgba(255,255,255,0.3)">{{ food.amount_display }}</span></span>
                    <span><span class="wf-cal">{{ food.calories|round|int }}</span> <span style="color:rgba(255,255,255,0.5);">{{ (fcum.value / wdata.cal * 100)|round|int }}%</span> <span style="color:rgba(255,255,255,0.35);">({{ (food.calories / wdata.cal * 100)|round|int }}%)</span> · <span style="color:#4ecdc4">{{ food.protein|round(1) }}g p</span> · <span style="color:#ffd93d">{{ food.fiber|round(1) }}g f</span></span>
                </div>
                {% endfor %}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- Fasting gaps -->
        {% if top_fasts %}
        <div class="graph-section" style="margin-bottom: 25px;">
            <div class="graph-title">Longest Fasting Gaps</div>
            {% for gap in top_fasts %}
            <div class="window-row" style="cursor: default;">
                <div class="window-label">{{ gap.start }}</div>
                <div class="window-bar-bg">
                    <div class="window-bar" style="width: {{ (gap.minutes / top_fasts[0].minutes * 100)|round }}%; background: linear-gradient(90deg, #4ecdc4, #2ab7ad);"></div>
                </div>
                <div class="window-cal" style="color:#4ecdc4;">{{ gap.duration }} <span style="color:rgba(255,255,255,0.4);">{{ gap.before_count }} ate → {{ gap.end }} ({{ gap.after_count }})</span></div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- Entries list -->
        <div class="entries-section">
            <div class="entries-title">By Calories</div>
            {% if entries %}
                {% set running_cal = namespace(value=0) %}
                {% for entry in entries %}
                {% set running_cal.value = running_cal.value + entry.calories %}
                <div class="entry-item">
                    <div class="entry-time">{{ entry.time }}</div>
                    <div class="entry-food">
                        {% if entry.count > 1 %}{{ entry.count }}x {% endif %}{{ entry.name }}
                        <span class="amount">{{ entry.amount_display }}</span>
                    </div>
                    <div class="entry-calories">{{ entry.calories|round|int }} cal <span style="color:rgba(255,255,255,0.4);">({{ (entry.calories / total_calories * 100)|round|int }}%)</span></div>
                    <div class="entry-protein">{{ entry.protein|round(1) }}g p</div>
                    <div class="entry-fiber" style="color:#ffd93d;">{{ entry.fiber|round(1) }}g f</div>
                    <div class="entry-running">{{ (running_cal.value / total_calories * 100)|round|int }}%</div>
                </div>
                {% endfor %}
            {% else %}
                <div class="empty-state">No entries yet today</div>
            {% endif %}
        </div>
    </div>
    
    <div class="bottom-nav">
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

    total_minutes = hour * 60 + minute
    # Scale to 0-100 over 24 hours (0=midnight, 100=midnight)
    x = (total_minutes / 1440) * 100
    return max(0, min(100, x))


def build_cumulative_path(entries, value_key, max_value, scale_factor=1):
    """Build SVG path for cumulative step graph"""
    if not entries:
        return "M 0 100 L 100 100", "M 0 100 L 100 100 L 0 100 Z"

    parts = ["M 0 100"]
    running_total = 0
    prev_y = 100

    for entry in entries:
        x = time_to_x(entry.get('time', '12:00'))
        # Horizontal line to this time at previous level
        parts.append(f"L {x:.1f} {prev_y:.1f}")
        running_total += entry.get(value_key, 0) * scale_factor
        y = 100 - (running_total / max_value * 100) if max_value > 0 else 100
        y = max(0, min(100, y))
        # Vertical jump to new level
        parts.append(f"L {x:.1f} {y:.1f}")
        prev_y = y

    # Extend to end of day at final value
    parts.append(f"L 100 {prev_y:.1f}")

    line_path = " ".join(parts)
    area_path = line_path + " L 100 100 L 0 100 Z"

    return line_path, area_path


def build_ratio_path(entries, nutrient_key, max_ratio):
    """Build SVG path for cumulative kcal/g ratio step graph"""
    if not entries:
        return "M 0 100 L 100 100"

    parts = []
    running_cal = 0
    running_nutrient = 0
    prev_y = None

    for entry in entries:
        x = time_to_x(entry.get('time', '12:00'))
        running_cal += entry.get('calories', 0)
        running_nutrient += entry.get(nutrient_key, 0)
        if running_nutrient > 0:
            ratio = running_cal / running_nutrient
            y = 100 - (ratio / max_ratio * 100)
            y = max(0, min(100, y))
            if prev_y is not None:
                parts.append(f"L {x:.1f} {prev_y:.1f}")
            else:
                parts.append(f"M {x:.1f} {y:.1f}")
            parts.append(f"L {x:.1f} {y:.1f}")
            prev_y = y

    if not parts:
        return "M 0 100 L 100 100"

    parts.append(f"L 100 {prev_y:.1f}")
    return " ".join(parts)


def build_entry_dots(entries, max_calories):
    """Build list of dot info for each entry on the cumulative calorie line"""
    total_cal = sum(e.get('calories', 0) for e in entries)
    dots = []
    running_cal = 0
    running_protein = 0
    running_fiber = 0
    for entry in entries:
        x = time_to_x(entry.get('time', '12:00'))
        cal = entry.get('calories', 0)
        prot = entry.get('protein', 0)
        fib = entry.get('fiber', 0)
        running_cal += cal
        running_protein += prot
        running_fiber += fib
        y = 100 - (running_cal / max_calories * 100) if max_calories > 0 else 100
        y = max(0, min(100, y))
        name = entry.get('name', entry.get('food', '?'))
        amount = entry.get('amount_display', '')
        time = entry.get('time', '')
        pct = round(running_cal / total_cal * 100) if total_cal > 0 else 0
        dots.append({
            'x': x, 'y': y, 'name': name, 'time': time,
            'calories': round(cal), 'protein': round(prot, 1),
            'fiber': round(fib, 1), 'amount': amount,
            'cum_cal': round(running_cal),
            'cum_protein': round(running_protein, 1),
            'cum_fiber': round(running_fiber, 1),
            'pct': pct,
        })
    return dots


def register_calories_routes(app):
    """Register calories timeline routes with the Flask app"""
    
    from .data import load_today_log, load_log_for_date, LOGS_DIR
    from datetime import timedelta
    from flask import request

    @app.route('/calories')
    def calories_timeline():
        date_str = request.args.get('date')
        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                target_date = date.today()
        else:
            target_date = date.today()

        entries = load_log_for_date(target_date)
        is_today = (target_date == date.today())
        prev_date = (target_date - timedelta(days=1)).isoformat()
        next_date = (target_date + timedelta(days=1)).isoformat()

        if target_date == date.today():
            title = "Today"
        elif target_date == date.today() - timedelta(days=1):
            title = "Yesterday"
        else:
            title = target_date.strftime('%a %d %b')
        
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
        calories_line, calories_area = build_cumulative_path(entries, 'calories', max_calories)
        # Ratio lines: kcal/g protein (scale 0-30), kcal/g fiber (scale 0-200)
        protein_ratio_line = build_ratio_path(entries, 'protein', 30)
        fiber_ratio_line = build_ratio_path(entries, 'fiber', 200)

        # Build entry dots for the calorie line
        entry_dots = build_entry_dots(entries, max_calories)

        # Group consecutive entries with the same food key
        grouped = []
        for entry in entries:
            if grouped and grouped[-1].get('food') == entry.get('food'):
                g = grouped[-1]
                g['calories'] = round(g['calories'] + entry.get('calories', 0), 1)
                g['protein'] = round(g['protein'] + entry.get('protein', 0), 1)
                g['fiber'] = round(g['fiber'] + entry.get('fiber', 0), 1)
                g['count'] = g.get('count', 1) + 1
                if entry.get('type') == 'amount' or 'g' in str(entry.get('amount_display', '')):
                    old_amt = g.get('amount', 0)
                    new_amt = old_amt + entry.get('amount', 0)
                    g['amount'] = new_amt
                    g['amount_display'] = f"{new_amt}g"
                else:
                    g['amount_display'] = f"{g['count']} units"
            else:
                g = dict(entry)
                g['count'] = 1
                grouped.append(g)

        # Entries sorted by calories descending
        entries_by_cal = sorted(grouped, key=lambda e: e.get('calories', 0), reverse=True)

        # Group entries into eating sessions (within 15 min of each other)
        # then compute fasting gaps between sessions
        fasting_gaps = []
        if entries:
            sorted_by_time = sorted(entries, key=lambda e: e.get('time', '00:00'))

            def time_to_mins(t):
                parts = t.split(':')
                return int(parts[0]) * 60 + int(parts[1])

            # Build sessions: groups of entries where consecutive entries are <= 15 min apart
            sessions = []
            current_session = [sorted_by_time[0]]
            for i in range(1, len(sorted_by_time)):
                t_prev = time_to_mins(sorted_by_time[i - 1].get('time', '00:00'))
                t_curr = time_to_mins(sorted_by_time[i].get('time', '00:00'))
                if t_curr - t_prev <= 15:
                    current_session.append(sorted_by_time[i])
                else:
                    sessions.append(current_session)
                    current_session = [sorted_by_time[i]]
            sessions.append(current_session)

            # Gaps between sessions
            for i in range(len(sessions) - 1):
                last_entry = sessions[i][-1]
                first_entry = sessions[i + 1][0]
                t1 = last_entry.get('time', '00:00')
                t2 = first_entry.get('time', '00:00')
                try:
                    mins = time_to_mins(t2) - time_to_mins(t1)
                    if mins > 0:
                        hours = mins // 60
                        remaining = mins % 60
                        dur = f"{hours}h {remaining:02d}m" if hours > 0 else f"{remaining}m"
                        fasting_gaps.append({
                            'start': t1, 'end': t2,
                            'minutes': mins, 'duration': dur,
                            'before_count': len(sessions[i]),
                            'after_count': len(sessions[i + 1]),
                        })
                except (ValueError, IndexError):
                    pass
        fasting_gaps.sort(key=lambda g: g['minutes'], reverse=True)
        top_fasts = fasting_gaps[:5]

        # 2-hour window calorie breakdown with food lists
        windows = {}
        for entry in entries:
            try:
                hour = int(entry.get('time', '12:00').split(':')[0])
            except (ValueError, IndexError):
                hour = 12
            bucket = (hour // 2) * 2
            label = f"{bucket:02d}-{bucket+2:02d}"
            if label not in windows:
                windows[label] = {'cal': 0, 'foods': []}
            windows[label]['cal'] += entry.get('calories', 0)
            windows[label]['foods'].append(entry)
        # Sort foods within each window by calories desc
        for w in windows.values():
            w['foods'].sort(key=lambda e: e.get('calories', 0), reverse=True)
        windows_sorted = [{'label': k, 'cal': v['cal'], 'foods': v['foods']}
                          for k, v in sorted(windows.items(), key=lambda x: x[1]['cal'], reverse=True)]
        max_window_cal = windows_sorted[0]['cal'] if windows_sorted else 1

        cal_per_protein = f"{total_calories / total_protein:.1f}" if total_protein > 0 else '--'
        cal_per_fiber = f"{total_calories / total_fiber:.1f}" if total_fiber > 0 else '--'

        # Compare to previous day at the same time
        prev_day = target_date - timedelta(days=1)
        prev_entries = load_log_for_date(prev_day)
        for e in prev_entries:
            if 'fiber' not in e:
                e['fiber'] = 0

        if is_today:
            # Filter previous day entries to only those up to current time
            now_time = datetime.now().strftime('%H:%M')
            prev_entries = [e for e in prev_entries if e.get('time', '00:00') <= now_time]

        prev_cal = sum(e.get('calories', 0) for e in prev_entries)
        prev_prot = sum(e.get('protein', 0) for e in prev_entries)
        prev_fib = sum(e.get('fiber', 0) for e in prev_entries)

        # Deltas
        cal_delta = round(total_calories - prev_cal)
        prev_cpp = prev_cal / prev_prot if prev_prot > 0 else 0
        prev_cpf = prev_cal / prev_fib if prev_fib > 0 else 0
        curr_cpp = total_calories / total_protein if total_protein > 0 else 0
        curr_cpf = total_calories / total_fiber if total_fiber > 0 else 0
        # For ratios, lower is better so delta sign is inverted for display
        cpp_delta = round(curr_cpp - prev_cpp, 1) if prev_prot > 0 and total_protein > 0 else None
        cpf_delta = round(curr_cpf - prev_cpf, 1) if prev_fib > 0 and total_fiber > 0 else None

        return render_template_string(HTML_CALORIES,
                                    entries=entries_by_cal,
                                    windows_sorted=windows_sorted,
                                    max_window_cal=max_window_cal,
                                    top_fasts=top_fasts,
                                    total_calories=round(total_calories),
                                    cal_per_protein=cal_per_protein,
                                    cal_per_fiber=cal_per_fiber,
                                    cal_delta=cal_delta,
                                    cpp_delta=cpp_delta,
                                    cpf_delta=cpf_delta,
                                    calories_line_path=calories_line,
                                    calories_area_path=calories_area,
                                    protein_line_path=protein_ratio_line,
                                    fiber_line_path=fiber_ratio_line,
                                    entry_dots=entry_dots,
                                    title=title,
                                    prev_date=prev_date,
                                    next_date=next_date,
                                    is_today=is_today)