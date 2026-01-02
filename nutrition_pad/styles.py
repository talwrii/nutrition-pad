"""
General-purpose CSS styles for the nutrition pad application.
Contains stable, foundational styles that rarely change.
"""

from flask import Response

# Base CSS styles - foundational styles that rarely change
BASE_CSS = """
/* Reset and base styles */
* { 
    margin: 0; 
    padding: 0; 
    box-sizing: border-box; 
}

body { 
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: #fff; 
    font-family: 'SF Pro Display', -webkit-system-font, 'Segoe UI', Roboto, sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
    padding-bottom: 120px;
}

/* Header styles */
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

/* Navigation tabs */
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

.tab-btn:hover:not(.active) {
    color: white;
    background: rgba(255, 255, 255, 0.1);
}

/* Grid layouts */
.food-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(280px, 1fr));
    gap: 20px;
    padding: 30px 20px;
    max-width: 1200px;
    margin: 0 auto;
}

/* General button styles */
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

/* Typography */
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

/* Status displays */
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

.no-foods {
    text-align: center;
    color: rgba(255, 255, 255, 0.5);
    font-size: 1.2em;
    margin: 50px 0;
    grid-column: 1 / -1;
}

/* Bottom navigation */
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

/* Log page styles */
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

/* Nutrition dashboard styles */
.nutrition-stats {
    max-width: 800px;
    margin: 30px auto;
    padding: 0 20px;
}

.stat-cards {
    display: grid;
    grid-template-columns: repeat(3, minmax(200px, 1fr));
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

/* Mobile responsive breakpoints */
@media (max-width: 768px) {
    .food-grid {
        grid-template-columns: repeat(3, minmax(150px, 1fr));
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
    
    .nav-tabs {
        margin: 20px 10px 0;
    }
    
    .tab-btn {
        padding: 12px 15px;
        font-size: 1em;
    }
    
    .log-item-header {
        flex-direction: column;
        align-items: stretch;
    }
    
    .log-item-amount {
        margin-right: 0;
        margin-bottom: 5px;
    }
}
"""


def get_base_css():
    """Get the base CSS styles"""
    return BASE_CSS


def register_styles_routes(app):
    """Register CSS serving routes with the Flask app"""
    
    @app.route('/static/base.css')
    def base_css():
        return Response(BASE_CSS, mimetype='text/css')
