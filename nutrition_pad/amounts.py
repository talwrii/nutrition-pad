"""
Amounts display and management functionality.
Handles the amounts tab with slider, preset buttons, and amount setting.
"""

from flask import render_template_string


# HTML template for the amounts tab content
AMOUNTS_TAB_HTML = """
<div class="amounts-container">
    <div class="amount-display">{{ current_amount }}g</div>
    
    <div class="slider-container">
        <input type="range" min="0" max="500" value="{{ current_amount }}" 
               class="slider" id="amountSlider" 
               onchange="setCurrentAmount(this.value)">
        <div style="display: flex; justify-content: space-between; color: rgba(255,255,255,0.5); font-size: 0.9em; margin-top: 10px;">
            <span>0g</span>
            <span>250g</span>
            <span>500g</span>
        </div>
    </div>
    
    <div class="preset-amounts">
        <h3>Quick Amounts</h3>
        <div class="preset-grid"></div>
    </div>
</div>
"""

# JavaScript for amounts functionality
AMOUNTS_JAVASCRIPT = """
function getCurrentAmount() {
    // Amount is now synced with server, get from page data initially
    var displayEl = document.querySelector('.current-amount, .amount-display');
    if (displayEl) {
        var match = displayEl.textContent.match(/(\\d+)g/);
        if (match) return parseFloat(match[1]);
    }
    return 100;
}

function setCurrentAmount(amount) {
    // Send amount to server
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/set-amount', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            debug('Amount set successfully to: ' + amount);
            updateAmountDisplay(amount);
            // Update our local timestamp so we don't get our own update back
            lastAmountUpdate = new Date().getTime() / 1000;
            localStorage.setItem('lastAmountUpdate', lastAmountUpdate.toString());
        } else if (xhr.readyState === 4) {
            debug('Error setting amount: ' + xhr.status);
        }
    };
    xhr.send(JSON.stringify({amount: amount}));
}

function updateAmountDisplay(amount) {
    var amountEls = document.querySelectorAll('.current-amount, .amount-display');
    amountEls.forEach(function(el) {
        el.textContent = amount + 'g';
    });
    
    // Update amount indicators on food buttons
    var amountIndicators = document.querySelectorAll('.food-type-indicator.amount');
    amountIndicators.forEach(function(el) {
        el.textContent = amount + 'g';
    });
    
    var sliderEl = document.getElementById('amountSlider');
    if (sliderEl) {
        sliderEl.value = amount;
    }
}

function createPresetButtons() {
    var presetGrid = document.querySelector('.preset-grid');
    if (!presetGrid) return;
    
    var presets = [25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 300, 400, 500];
    presetGrid.innerHTML = '';
    
    presets.forEach(function(amount) {
        var btn = document.createElement('button');
        btn.className = 'preset-btn';
        btn.textContent = amount + 'g';
        btn.onclick = function() { setCurrentAmount(amount); };
        presetGrid.appendChild(btn);
    });
}

function onAmountSliderChange(value) {
    setCurrentAmount(parseFloat(value));
}
"""

# CSS styles specific to amounts (already included in main, but here for reference)
AMOUNTS_CSS = """
.amounts-container {
    max-width: 600px;
    margin: 0 auto;
    padding: 30px 20px;
}

.amount-display {
    text-align: center;
    font-size: 3em;
    font-weight: 700;
    color: #ffd93d;
    margin-bottom: 30px;
    text-shadow: 0 0 20px rgba(255, 217, 61, 0.3);
}

.slider-container {
    margin: 40px 0;
    padding: 20px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 20px;
    backdrop-filter: blur(20px);
}

.slider {
    width: 100%;
    height: 8px;
    border-radius: 4px;
    background: rgba(255, 255, 255, 0.2);
    outline: none;
    -webkit-appearance: none;
    margin: 20px 0;
}

.slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: linear-gradient(135deg, #ffd93d, #ff6b6b);
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(255, 217, 61, 0.3);
}

.slider::-moz-range-thumb {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: linear-gradient(135deg, #ffd93d, #ff6b6b);
    cursor: pointer;
    border: none;
    box-shadow: 0 4px 15px rgba(255, 217, 61, 0.3);
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

.preset-btn:hover {
    background: rgba(255, 217, 61, 0.2);
    border-color: #ffd93d;
    transform: translateY(-2px);
}
"""


def render_amounts_tab(current_amount):
    """Render the amounts tab content"""
    return render_template_string(AMOUNTS_TAB_HTML, current_amount=current_amount)


def get_amounts_javascript():
    """Get the JavaScript code for amounts functionality"""
    return AMOUNTS_JAVASCRIPT


def get_amounts_css():
    """Get the CSS styles for amounts functionality (for reference)"""
    return AMOUNTS_CSS


def get_preset_amounts():
    """Get the list of preset amounts"""
    return [25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 300, 400, 500]