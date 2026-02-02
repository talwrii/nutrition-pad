"""
CSS styles for the nutrition pad application.
"""

from flask import Response

BASE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    min-height: 100vh;
    color: white;
}

.header {
    text-align: center;
    padding: 30px 20px 20px;
    position: relative;
}

.header h1 {
    font-size: 2em;
    margin-bottom: 10px;
    background: linear-gradient(135deg, #ffd93d, #ff6b6b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.current-amount, .total-protein, .item-count, .cal-per-protein {
    font-size: 1.1em;
    color: rgba(255, 255, 255, 0.7);
    margin: 5px 0;
}

.current-amount { color: #4ecdc4; font-weight: 600; }

.nav-tabs {
    display: flex;
    justify-content: center;
    gap: 10px;
    padding: 15px;
    flex-wrap: wrap;
}

.tab-btn {
    padding: 12px 20px;
    background: rgba(255, 255, 255, 0.1);
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-radius: 25px;
    color: white;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.3s ease;
}

.tab-btn:hover, .tab-btn.active {
    background: rgba(255, 217, 61, 0.2);
    border-color: #ffd93d;
    transform: translateY(-2px);
}

.bottom-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 15px;
    background: rgba(26, 26, 46, 0.95);
    backdrop-filter: blur(20px);
    display: flex;
    gap: 10px;
}

.bottom-nav-btn {
    flex: 1;
    padding: 15px;
    background: linear-gradient(135deg, #ff6b6b, #ffd93d);
    border: none;
    border-radius: 15px;
    color: white;
    font-size: 1.1em;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
}

.bottom-nav-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(255, 107, 107, 0.3);
}

/* Nutrition stats */
.nutrition-stats {
    max-width: 600px;
    margin: 20px auto;
    padding: 0 20px;
}

.stat-cards {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
}

.stat-card {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 25px 15px;
    text-align: center;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.stat-value {
    font-size: 2.5em;
    font-weight: 700;
    margin-bottom: 8px;
}

.stat-value.calories { color: #ff6b6b; }
.stat-value.protein { color: #4ecdc4; }
.stat-value.ratio { color: #00d4ff; }
.stat-value.time-since { color: #ffd93d; }
.stat-value.cal-hour { color: #ff8c42; }
.stat-value.prot-hour { color: #98d8c8; }
.stat-value.fiber-ratio { color: #c9b1ff; }
.stat-value.fiber { color: #f7dc6f; }

.stat-label {
    font-size: 0.9em;
    color: rgba(255, 255, 255, 0.6);
    text-transform: uppercase;
    letter-spacing: 1px;
}

.stat-sub {
    font-size: 1.3em;
    color: rgba(255, 255, 255, 0.5);
    margin-top: -5px;
    margin-bottom: 5px;
}

.stat-rate {
    font-size: 0.55em;
    color: rgba(255, 255, 255, 0.45);
}

/* Log container */
.log-container {
    max-width: 600px;
    margin: 20px auto;
    padding: 0 20px 100px;
}

.log-item {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 15px;
    padding: 15px;
    margin-bottom: 10px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.log-item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.log-item-name {
    font-weight: 600;
    font-size: 1.1em;
}

.log-item-amount, .log-item-cal {
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.9em;
}

.log-item-time {
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.85em;
    margin-top: 5px;
}

.no-entries, .no-foods {
    text-align: center;
    padding: 40px 20px;
    color: rgba(255, 255, 255, 0.5);
}

@media (max-width: 480px) {
    .stat-cards { grid-template-columns: repeat(2, 1fr); }
    .stat-value { font-size: 2em; }
}
"""

def register_styles_routes(app):
    @app.route('/static/base.css')
    def base_css():
        return Response(BASE_CSS, mimetype='text/css')