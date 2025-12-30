"""
Amounts display and management functionality.
Handles the amounts tab with slider, preset buttons, and amount setting.
Optimized for very old Android browsers (Galaxy Note 10.1).
"""
from flask import render_template_string

# HTML template for the amounts tab content - simplified for old browsers
AMOUNTS_TAB_HTML = """
<div class="amounts-container">
    <div class="amount-display">{{ current_amount }}g</div>
    
    <!-- Simple number input as fallback -->
    <div class="amount-input-container">
        <label for="amountInput">Enter Amount (0-500g):</label>
        <input type="number" id="amountInput" min="0" max="500" value="{{ current_amount }}" 
               onchange="setCurrentAmountFromInput()" 
               style="width: 100px; padding: 10px; font-size: 18px; text-align: center;">
    </div>
    
    <!-- Large adjustment buttons -->
    <div class="amount-controls">
        <button class="amount-btn large" onclick="setCurrentAmount(0)">0g</button>
        <button class="amount-btn large" onclick="setCurrentAmount(50)">50g</button>
        <button class="amount-btn large" onclick="setCurrentAmount(100)">100g</button>
        <button class="amount-btn large" onclick="setCurrentAmount(150)">150g</button>
        <button class="amount-btn large" onclick="setCurrentAmount(200)">200g</button>
    </div>
    
    <!-- Fine adjustment buttons -->
    <div class="amount-controls">
        <button class="amount-btn" onclick="adjustAmount(-50)">-50g</button>
        <button class="amount-btn" onclick="adjustAmount(-10)">-10g</button>
        <button class="amount-btn" onclick="adjustAmount(-5)">-5g</button>
        <button class="amount-btn" onclick="adjustAmount(5)">+5g</button>
        <button class="amount-btn" onclick="adjustAmount(10)">+10g</button>
        <button class="amount-btn" onclick="adjustAmount(50)">+50g</button>
    </div>
    
    <div class="preset-amounts">
        <h3>Common Amounts</h3>
        <div class="preset-grid"></div>
    </div>
    
    <!-- Fallback slider using a simple div-based approach -->
    <div class="simple-slider-container">
        <div class="simple-slider-label">Drag to adjust (0-500g):</div>
        <div class="simple-slider-track" id="simpleSliderTrack" onclick="handleSliderClick(event)">
            <div class="simple-slider-fill" id="simpleSliderFill"></div>
            <div class="simple-slider-handle" id="simpleSliderHandle"></div>
        </div>
    </div>
</div>
"""

# JavaScript for amounts functionality - simplified for old browsers
AMOUNTS_JAVASCRIPT = """
// Use very basic JavaScript for compatibility
var currentAmountValue = 100;

function getCurrentAmount() {
    try {
        var displayEl = document.querySelector('.amount-display');
        if (displayEl && displayEl.textContent) {
            var match = displayEl.textContent.match(/(\\d+)/);
            if (match) {
                var amount = parseInt(match[1], 10);
                if (!isNaN(amount)) {
                    currentAmountValue = amount;
                    return amount;
                }
            }
        }
    } catch (e) {
        // Ignore errors on old browsers
    }
    return currentAmountValue;
}

function setCurrentAmount(amount) {
    try {
        // Basic validation
        amount = parseInt(amount, 10);
        if (isNaN(amount)) amount = 100;
        if (amount < 0) amount = 0;
        if (amount > 500) amount = 500;
        
        currentAmountValue = amount;
        
        // Generate simple nonce
        var nonce = new Date().getTime().toString();
        if (typeof setMyNonce === 'function') {
            setMyNonce(nonce);
        }
        
        // Send to server using basic XMLHttpRequest
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/set-amount', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                updateAmountDisplay(amount);
            }
        };
        
        var data = JSON.stringify({amount: amount, nonce: nonce});
        xhr.send(data);
        
    } catch (e) {
        // Fallback for very old browsers
        alert('Set amount to: ' + amount + 'g');
        updateAmountDisplay(amount);
    }
}

function setCurrentAmountFromInput() {
    try {
        var input = document.getElementById('amountInput');
        if (input) {
            setCurrentAmount(input.value);
        }
    } catch (e) {
        // Ignore errors
    }
}

function adjustAmount(delta) {
    try {
        var currentAmount = getCurrentAmount();
        var newAmount = currentAmount + delta;
        if (newAmount < 0) newAmount = 0;
        if (newAmount > 500) newAmount = 500;
        setCurrentAmount(newAmount);
    } catch (e) {
        // Fallback
        var newAmount = currentAmountValue + delta;
        if (newAmount < 0) newAmount = 0;
        if (newAmount > 500) newAmount = 500;
        setCurrentAmount(newAmount);
    }
}

function updateAmountDisplay(amount) {
    try {
        currentAmountValue = amount;
        
        // Update all display elements
        var amountEls = document.querySelectorAll('.current-amount, .amount-display');
        for (var i = 0; i < amountEls.length; i++) {
            amountEls[i].textContent = amount + 'g';
        }
        
        // Update amount indicators on food buttons
        var amountIndicators = document.querySelectorAll('.food-type-indicator.amount');
        for (var i = 0; i < amountIndicators.length; i++) {
            amountIndicators[i].textContent = amount + 'g';
        }
        
        // Update number input
        var input = document.getElementById('amountInput');
        if (input) {
            input.value = amount;
        }
        
        // Update simple slider
        updateSimpleSlider(amount);
        
    } catch (e) {
        // Ignore errors on old browsers
    }
}

function createPresetButtons() {
    try {
        var presetGrid = document.querySelector('.preset-grid');
        if (!presetGrid) return;
        
        var presets = [25, 50, 75, 100, 125, 150, 200, 250, 300, 400, 500];
        presetGrid.innerHTML = '';
        
        for (var i = 0; i < presets.length; i++) {
            var amount = presets[i];
            var btn = document.createElement('button');
            btn.className = 'preset-btn';
            btn.textContent = amount + 'g';
            
            // Use closure to capture amount value
            (function(amt) {
                btn.onclick = function() {
                    setCurrentAmount(amt);
                };
            })(amount);
            
            presetGrid.appendChild(btn);
        }
    } catch (e) {
        // Ignore errors
    }
}

// Simple slider implementation
function updateSimpleSlider(amount) {
    try {
        var handle = document.getElementById('simpleSliderHandle');
        var fill = document.getElementById('simpleSliderFill');
        if (handle && fill) {
            var percentage = (amount / 500) * 100;
            if (percentage < 0) percentage = 0;
            if (percentage > 100) percentage = 100;
            
            handle.style.left = percentage + '%';
            fill.style.width = percentage + '%';
        }
    } catch (e) {
        // Ignore errors
    }
}

function handleSliderClick(event) {
    try {
        var track = document.getElementById('simpleSliderTrack');
        if (!track) return;
        
        // Calculate position
        var rect = track.getBoundingClientRect();
        var x = event.clientX - rect.left;
        var percentage = x / rect.width;
        if (percentage < 0) percentage = 0;
        if (percentage > 1) percentage = 1;
        
        var amount = Math.round(percentage * 500);
        setCurrentAmount(amount);
        
    } catch (e) {
        // Ignore errors
    }
}

// Initialize amounts tab - simplified
function initializeAmountsTab() {
    try {
        var currentAmount = getCurrentAmount();
        updateAmountDisplay(currentAmount);
        
        // Small delay to ensure DOM is ready
        setTimeout(function() {
            createPresetButtons();
            updateSimpleSlider(currentAmount);
        }, 200);
        
    } catch (e) {
        // Fallback initialization
        setTimeout(function() {
            try {
                createPresetButtons();
                updateSimpleSlider(100);
            } catch (e2) {
                // Final fallback - do nothing
            }
        }, 500);
    }
}

// Legacy function for compatibility
function onAmountSliderChange(value) {
    setCurrentAmount(value);
}
"""

# CSS styles specific to amounts - simplified for old browsers
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

.amount-input-container {
    text-align: center;
    margin: 20px 0;
    padding: 20px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
}

.amount-input-container label {
    display: block;
    margin-bottom: 10px;
    color: rgba(255, 255, 255, 0.8);
    font-size: 1.1em;
}

/* Large preset buttons */
.amount-controls {
    display: block;
    text-align: center;
    margin: 20px 0;
}

.amount-btn {
    background: rgba(255, 255, 255, 0.1);
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-radius: 10px;
    padding: 15px 20px;
    color: white;
    font-size: 1.1em;
    font-weight: 600;
    cursor: pointer;
    margin: 5px;
    min-width: 80px;
    display: inline-block;
}

.amount-btn.large {
    background: rgba(255, 217, 61, 0.2);
    border-color: rgba(255, 217, 61, 0.5);
    padding: 20px 25px;
    font-size: 1.3em;
    min-width: 100px;
}

.amount-btn:hover, .amount-btn:active {
    background: rgba(255, 217, 61, 0.3);
    border-color: #ffd93d;
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
    text-align: center;
}

.preset-btn {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 12px 15px;
    color: white;
    font-size: 1em;
    font-weight: 600;
    cursor: pointer;
    margin: 3px;
    display: inline-block;
    min-width: 70px;
}

.preset-btn:hover, .preset-btn:active {
    background: rgba(255, 217, 61, 0.2);
    border-color: #ffd93d;
}

/* Simple slider */
.simple-slider-container {
    margin: 30px 0;
    padding: 20px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
}

.simple-slider-label {
    text-align: center;
    margin-bottom: 15px;
    color: rgba(255, 255, 255, 0.7);
}

.simple-slider-track {
    position: relative;
    width: 100%;
    height: 20px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 10px;
    cursor: pointer;
    margin: 10px 0;
}

.simple-slider-fill {
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    background: linear-gradient(90deg, #ffd93d, #ff6b6b);
    border-radius: 10px;
    width: 20%;
}

.simple-slider-handle {
    position: absolute;
    top: 50%;
    width: 30px;
    height: 30px;
    background: #ffd93d;
    border: 3px solid white;
    border-radius: 50%;
    cursor: pointer;
    left: 20%;
    margin-top: -15px;
    margin-left: -15px;
}

/* Mobile optimizations for old devices */
@media (max-width: 768px) {
    .amount-display {
        font-size: 2.5em;
    }
    
    .amount-btn {
        padding: 18px 22px;
        font-size: 1.2em;
        margin: 8px 5px;
    }
    
    .amount-btn.large {
        padding: 25px 30px;
        font-size: 1.4em;
    }
    
    .preset-btn {
        padding: 15px 18px;
        font-size: 1.1em;
        margin: 5px;
    }
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