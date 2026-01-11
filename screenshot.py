#!/usr/bin/env python3
"""
Nutrition-Pad Screenshot Automation - All-in-One Version
Creates a temporary Flask app and takes screenshots
"""

import os
import sys
import time
import subprocess
import tempfile
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

# Configuration
FLASK_PORT = 5000
FLASK_URL = f"http://127.0.0.1:{FLASK_PORT}"
SCREENSHOT_DIR = Path("/mnt/user-data/outputs/nutrition_pad_screenshots")
MAX_START_ATTEMPTS = 30

# Pages to screenshot
PAGES = [
    {"name": "home", "url": "/", "description": "Home page"},
    {"name": "amounts", "url": "/?pad=amounts", "description": "Amounts tab"},
    {"name": "notes", "url": "/notes", "description": "Notes page"},
    {"name": "editor", "url": "/edit-foods", "description": "Food editor"},
]

# Embedded Flask app code
FLASK_APP_CODE = '''
import os
from flask import Flask, render_template_string, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

# Sample food data
FOODS = {
    "chicken": {"protein": 31, "calories": 165, "color": "#ff6b6b"},
    "rice": {"protein": 2.7, "calories": 130, "color": "#ffd93d"},
    "broccoli": {"protein": 2.8, "calories": 34, "color": "#6bcf7f"},
    "salmon": {"protein": 25, "calories": 208, "color": "#ff8b94"},
    "eggs": {"protein": 13, "calories": 155, "color": "#ffbe5c"},
    "oats": {"protein": 13.2, "calories": 389, "color": "#c5a880"},
    "tofu": {"protein": 8, "calories": 76, "color": "#f0e5d8"},
    "almonds": {"protein": 21, "calories": 579, "color": "#d4a574"}
}

CURRENT_AMOUNT = 100

# Amounts tab HTML
AMOUNTS_TAB_HTML = """
<style>
.custom-slider {
    padding: 30px 15px;
}
.slider-track {
    position: relative;
    width: 100%;
    height: 12px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 6px;
    cursor: pointer;
    margin: 20px 0;
}
.slider-fill {
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    background: linear-gradient(90deg, #ffd93d, #ff6b6b);
    border-radius: 6px;
    width: 20%;
    pointer-events: none;
    transition: width 0.1s ease;
}
.slider-thumb {
    position: absolute;
    top: 50%;
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, #ffd93d, #ff6b6b);
    border: 3px solid white;
    border-radius: 50%;
    cursor: pointer;
    left: 20%;
    margin-top: -16px;
    margin-left: -16px;
    box-shadow: 0 4px 15px rgba(255, 217, 61, 0.3);
    transition: transform 0.1s ease;
    z-index: 10;
}
.slider-labels {
    display: flex;
    justify-content: space-between;
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.9em;
    margin-top: 15px;
}
.amount-controls {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin: 20px 0;
    flex-wrap: wrap;
}
.amount-btn {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 10px;
    padding: 12px 16px;
    color: white;
    font-size: 1em;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    min-width: 60px;
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
</style>
<div class="amounts-container">
    <div class="amount-display">{{ current_amount }}g</div>
    
    <div class="slider-container">
        <div class="custom-slider">
            <div class="slider-track" id="sliderTrack">
                <div class="slider-fill" id="sliderFill"></div>
                <div class="slider-thumb" id="sliderThumb"></div>
            </div>
            <div class="slider-labels">
                <span>0g</span>
                <span>125g</span>
                <span>250g</span>
                <span>375g</span>
                <span>500g</span>
            </div>
        </div>
    </div>
    
    <div class="amount-controls">
        <button class="amount-btn" onclick="adjustAmount(-25)">-25g</button>
        <button class="amount-btn" onclick="adjustAmount(-5)">-5g</button>
        <button class="amount-btn" onclick="adjustAmount(5)">+5g</button>
        <button class="amount-btn" onclick="adjustAmount(25)">+25g</button>
    </div>
    
    <div class="preset-amounts">
        <h3>Quick Amounts</h3>
        <div class="preset-grid"></div>
    </div>
</div>
"""

# Amounts JavaScript
AMOUNTS_JS = """
var currentAmountValue = 100;

function getCurrentAmount() {
    return currentAmountValue;
}

function setCurrentAmount(amount) {
    amount = parseFloat(amount);
    if (isNaN(amount)) amount = 100;
    if (amount < 0) amount = 0;
    if (amount > 500) amount = 500;
    
    currentAmountValue = amount;
    updateAmountDisplay(amount);
}

function adjustAmount(delta) {
    var newAmount = Math.max(0, Math.min(500, currentAmountValue + delta));
    setCurrentAmount(newAmount);
}

function updateAmountDisplay(amount) {
    currentAmountValue = amount;
    
    var amountEls = document.querySelectorAll('.current-amount, .amount-display');
    for (var i = 0; i < amountEls.length; i++) {
        amountEls[i].textContent = amount + 'g';
    }
    
    updateSliderPosition(amount);
}

function updateSliderPosition(amount) {
    var sliderThumb = document.getElementById('sliderThumb');
    var sliderFill = document.getElementById('sliderFill');
    if (!sliderThumb || !sliderFill) return;
    
    var percentage = Math.max(0, Math.min(100, (amount / 500) * 100));
    sliderThumb.style.left = percentage + '%';
    sliderFill.style.width = percentage + '%';
}

function createPresetButtons() {
    var presetGrid = document.querySelector('.preset-grid');
    if (!presetGrid) return;
    
    var presets = [25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 300, 400, 500];
    presetGrid.innerHTML = '';
    
    for (var i = 0; i < presets.length; i++) {
        var amount = presets[i];
        var btn = document.createElement('button');
        btn.className = 'preset-btn';
        btn.textContent = amount + 'g';
        
        (function(amt) {
            btn.onclick = function() {
                setCurrentAmount(amt);
            };
        })(amount);
        
        presetGrid.appendChild(btn);
    }
}

function initializeAmountsTab() {
    var currentAmount = getCurrentAmount();
    updateAmountDisplay(currentAmount);
    
    setTimeout(function() {
        createPresetButtons();
    }, 100);
}
"""

# Main page template
MAIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Food Pads</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding-bottom: 80px;
        }
        .header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 20px;
            text-align: center;
            color: white;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .header h1 { font-size: 2em; margin-bottom: 10px; }
        .header-icons {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 10px 0;
        }
        .header-icons a {
            font-size: 1.5em;
            text-decoration: none;
            padding: 8px;
            min-width: 44px;
            min-height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .current-amount {
            font-size: 1.5em;
            font-weight: bold;
            margin: 10px 0;
        }
        .item-count {
            font-size: 1em;
            opacity: 0.9;
        }
        .nav-tabs {
            display: flex;
            overflow-x: auto;
            gap: 10px;
            padding: 15px;
            background: rgba(0, 0, 0, 0.1);
        }
        .tab {
            padding: 12px 24px;
            background: rgba(255, 255, 255, 0.1);
            border: none;
            border-radius: 20px;
            color: white;
            font-size: 1em;
            white-space: nowrap;
            cursor: pointer;
            transition: all 0.3s ease;
            min-width: 44px;
            min-height: 44px;
        }
        .tab.active {
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.05);
        }
        .tab-content {
            padding: 20px;
        }
        .amounts-container {
            max-width: 600px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px 20px;
        }
        .amount-display {
            font-size: 3em;
            font-weight: bold;
            text-align: center;
            color: white;
            margin-bottom: 20px;
        }
        .food-pads {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
            padding: 20px;
        }
        .food-pad {
            aspect-ratio: 1;
            border-radius: 20px;
            border: none;
            color: white;
            font-size: 1.2em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            gap: 5px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        .food-pad:active {
            transform: scale(0.95);
        }
        .food-name {
            font-size: 1.2em;
            text-transform: capitalize;
        }
        .food-nutrition {
            font-size: 0.8em;
            opacity: 0.9;
        }
    </style>
    <script>
        """ + AMOUNTS_JS + """
        
        function startLongPolling() { }
        
        window.onload = function() {
            if (typeof initializeAmountsTab === 'function') {
                initializeAmountsTab();
            } else {
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
            <a href="/?pad=amounts" class="amounts-link" title="Set Amount">📏</a>
            <a href="/notes" class="notes-link" title="Food Notes">📝</a>
            <a href="/edit-foods" class="settings-cog" title="Edit Foods Configuration">⚙️</a>
        </div>
        <div class="current-amount">{{ current_amount }}g</div>
        <div class="item-count">0 items logged today</div>
    </div>
    
    {% if show_amounts %}
        {{ amounts_content | safe }}
    {% else %}
        <div class="food-pads">
            {% for food_name, food_data in foods.items() %}
            <button class="food-pad" style="background: {{ food_data.color }};">
                <div class="food-name">{{ food_name }}</div>
                <div class="food-nutrition">{{ food_data.protein }}g protein</div>
            </button>
            {% endfor %}
        </div>
    {% endif %}
</body>
</html>
"""

# Notes template
NOTES_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Food Notes</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 20px;
            text-align: center;
        }
        .header h1 { font-size: 2em; }
        .notes-container {
            max-width: 800px;
            margin: 20px auto;
            padding: 20px;
        }
        .note-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Food Notes</h1>
    </div>
    <div class="notes-container">
        <div class="note-card">
            <p>No notes yet. Click on food pads to add notes!</p>
        </div>
    </div>
</body>
</html>
"""

# Editor template
EDITOR_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Food Editor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 20px;
            text-align: center;
        }
        .header h1 { font-size: 2em; }
        .editor-container {
            max-width: 800px;
            margin: 20px auto;
            padding: 20px;
        }
        .food-item {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 15px;
        }
        .food-item h3 {
            font-size: 1.5em;
            margin-bottom: 10px;
            text-transform: capitalize;
        }
        .food-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }
        .stat {
            background: rgba(0, 0, 0, 0.2);
            padding: 10px;
            border-radius: 8px;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        .stat-value {
            font-size: 1.2em;
            font-weight: bold;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Food Configuration Editor</h1>
    </div>
    <div class="editor-container">
        {% for food_name, food_data in foods.items() %}
        <div class="food-item" style="border-left: 4px solid {{ food_data.color }};">
            <h3>{{ food_name }}</h3>
            <div class="food-stats">
                <div class="stat">
                    <div class="stat-label">Protein</div>
                    <div class="stat-value">{{ food_data.protein }}g</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Calories</div>
                    <div class="stat-value">{{ food_data.calories }}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Color</div>
                    <div class="stat-value">{{ food_data.color }}</div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    show_amounts = request.args.get('pad') == 'amounts'
    amounts_content = render_template_string(AMOUNTS_TAB_HTML, current_amount=CURRENT_AMOUNT) if show_amounts else ""
    return render_template_string(MAIN_TEMPLATE, 
                                 foods=FOODS, 
                                 current_amount=CURRENT_AMOUNT,
                                 show_amounts=show_amounts,
                                 amounts_content=amounts_content)

@app.route('/notes')
def notes():
    return render_template_string(NOTES_TEMPLATE)

@app.route('/edit-foods')
def edit_foods():
    return render_template_string(EDITOR_TEMPLATE, foods=FOODS)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
'''


class ScreenshotHarness:
    def __init__(self):
        self.temp_dir = None
        self.flask_process = None
        self.screenshot_dir = SCREENSHOT_DIR
        
    def setup(self):
        """Create temporary directory and Flask app"""
        print("=" * 60)
        print("   NUTRITION-PAD SCREENSHOT AUTOMATION")
        print("=" * 60)
        
        # Create temp directory for Flask app
        self.temp_dir = tempfile.mkdtemp(prefix="nutrition_pad_")
        
        # Write Flask app to temp file
        flask_app_path = Path(self.temp_dir) / "app.py"
        with open(flask_app_path, 'w') as f:
            f.write(FLASK_APP_CODE)
        
        # Create screenshot directory
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📁 Created temp directory: {self.temp_dir}")
        print(f"📁 Screenshots will be saved to: {self.screenshot_dir}")
        
    def start_flask(self):
        """Start the Flask development server"""
        print(f"\n🚀 Starting nutrition-pad Flask app...")
        
        flask_app_path = Path(self.temp_dir) / "app.py"
        
        # Start Flask in subprocess
        self.flask_process = subprocess.Popen(
            [sys.executable, str(flask_app_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=self.temp_dir,
            text=True,
            bufsize=1
        )
        
        # Wait for Flask to start
        print(f"⏳ Waiting for Flask to start on {FLASK_URL}...")
        for attempt in range(1, MAX_START_ATTEMPTS + 1):
            time.sleep(1)
            try:
                import urllib.request
                urllib.request.urlopen(FLASK_URL, timeout=1)
                print(f"✅ Flask is ready after {attempt} attempts!")
                return True
            except:
                continue
        
        print("❌ Flask failed to start!")
        return False
    
    def stop_flask(self):
        """Stop the Flask server"""
        if self.flask_process:
            print("\n🛑 Stopping Flask app...")
            self.flask_process.terminate()
            self.flask_process.wait(timeout=5)
            print("✅ Flask stopped")
    
    def cleanup(self):
        """Clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def take_screenshots(self):
        """Open nutrition-pad in headless browser and take screenshots"""
        print("\n📸 Starting headless browser and taking screenshots...")
        
        with sync_playwright() as p:
            # Launch browser (headless mode)
            browser = p.chromium.launch(headless=True)
            
            # Create a new page with tablet viewport (Nexus 10 size)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                device_scale_factor=2
            )
            page = context.new_page()
            
            # Take screenshots of each page
            for page_info in PAGES:
                url = FLASK_URL + page_info['url']
                screenshot_path = self.screenshot_dir / f"{page_info['name']}.png"
                
                print(f"\n📄 Visiting: {page_info['description']}")
                print(f"   URL: {url}")
                
                # Navigate to page and wait for network to be idle
                page.goto(url, wait_until='networkidle')
                
                # Wait for any JavaScript to execute
                page.wait_for_timeout(3000)  # 3 seconds for JS execution
                
                # For amounts page, wait specifically for the preset grid to be populated
                if page_info['name'] == 'amounts':
                    try:
                        # Wait for the amounts tab to initialize
                        print("   ⏳ Waiting for amounts tab JavaScript to render...")
                        page.wait_for_timeout(2000)  # Wait 2 seconds for initialization
                        
                        # Check if preset grid exists and has buttons
                        preset_count = page.locator('.preset-btn').count()
                        if preset_count > 0:
                            print(f"   ✅ Found {preset_count} preset buttons")
                        else:
                            print("   ⚠️  No preset buttons found - checking page content...")
                            # Try to manually trigger the initialization
                            page.evaluate("if (typeof initializeAmountsTab === 'function') initializeAmountsTab();")
                            page.wait_for_timeout(1000)
                            preset_count = page.locator('.preset-btn').count()
                            print(f"   After manual init: {preset_count} buttons")
                    except Exception as e:
                        print(f"   ⚠️  Error: {e}")
                
                # Take screenshot
                page.screenshot(path=str(screenshot_path), full_page=True)
                print(f"   ✅ Screenshot saved: {screenshot_path.name}")
            
            # Close browser
            browser.close()
    
    def print_summary(self):
        """Print summary of screenshots taken"""
        print(f"\n✅ All screenshots saved to: {self.screenshot_dir}")
        
        print("\n" + "=" * 60)
        print("📊 SCREENSHOT SUMMARY")
        print("=" * 60)
        
        print(f"\n✅ {len(PAGES)} screenshots captured:")
        for screenshot_file in sorted(self.screenshot_dir.glob("*.png")):
            size_kb = screenshot_file.stat().st_size / 1024
            print(f"   • {screenshot_file.name} ({size_kb:.1f} KB)")
        
        print(f"\n📁 Location: {self.screenshot_dir}")
        print("=" * 60)
    
    def run(self):
        """Main execution flow"""
        try:
            self.setup()
            
            if not self.start_flask():
                return False
            
            self.take_screenshots()
            self.print_summary()
            
            print("\n✅ Test completed successfully!")
            return True
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.stop_flask()
            self.cleanup()


if __name__ == "__main__":
    harness = ScreenshotHarness()
    success = harness.run()
    sys.exit(0 if success else 1)