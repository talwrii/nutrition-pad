"""
Amounts display and management functionality.
Custom slider built from basic HTML elements.
"""
from flask import render_template_string

# HTML template with custom slider
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

# JavaScript for amounts functionality
AMOUNTS_JAVASCRIPT = """
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

def render_amounts_tab(current_amount):
    """Render the amounts tab content"""
    return render_template_string(AMOUNTS_TAB_HTML, current_amount=current_amount)

def get_amounts_javascript():
    """Get the JavaScript code for amounts functionality"""
    return AMOUNTS_JAVASCRIPT