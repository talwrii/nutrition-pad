"""
Amounts display and management functionality.
Handles the amounts tab with NO sliders - only buttons and simple controls.
Designed specifically for old tablets like Galaxy Note 10.1.
"""
from flask import render_template_string

# HTML template for the amounts tab content - NO SLIDERS AT ALL
AMOUNTS_TAB_HTML = """
<div class="amounts-container">
    <div class="amount-display">{{ current_amount }}g</div>
    
    <!-- Direct number input -->
    <div class="amount-input-section">
        <label for="amountInput">Enter Amount:</label>
        <input type="number" id="amountInput" min="0" max="500" value="{{ current_amount }}" 
               onchange="setCurrentAmountFromInput()" 
               style="width: 120px; padding: 15px; font-size: 20px; text-align: center; margin: 10px;">
        <button onclick="setCurrentAmountFromInput()" style="padding: 15px; font-size: 18px;">Set</button>
    </div>
    
    <!-- Common preset amounts - BIG BUTTONS -->
    <div class="quick-presets">
        <h3>Common Amounts</h3>
        <div class="preset-row">
            <button class="preset-large" onclick="setCurrentAmount(0)">0g</button>
            <button class="preset-large" onclick="setCurrentAmount(50)">50g</button>
            <button class="preset-large" onclick="setCurrentAmount(100)">100g</button>
            <button class="preset-large" onclick="setCurrentAmount(150)">150g</button>
        </div>
        <div class="preset-row">
            <button class="preset-large" onclick="setCurrentAmount(200)">200g</button>
            <button class="preset-large" onclick="setCurrentAmount(250)">250g</button>
            <button class="preset-large" onclick="setCurrentAmount(300)">300g</button>
            <button class="preset-large" onclick="setCurrentAmount(400)">400g</button>
        </div>
    </div>
    
    <!-- Adjustment buttons -->
    <div class="adjustment-section">
        <h3>Adjust Current Amount</h3>
        <div class="adjust-row">
            <button class="adjust-btn big" onclick="adjustAmount(-100)">-100g</button>
            <button class="adjust-btn big" onclick="adjustAmount(-50)">-50g</button>
            <button class="adjust-btn big" onclick="adjustAmount(-25)">-25g</button>
        </div>
        <div class="adjust-row">
            <button class="adjust-btn" onclick="adjustAmount(-10)">-10g</button>
            <button class="adjust-btn" onclick="adjustAmount(-5)">-5g</button>
            <button class="adjust-btn" onclick="adjustAmount(5)">+5g</button>
            <button class="adjust-btn" onclick="adjustAmount(10)">+10g</button>
        </div>
        <div class="adjust-row">
            <button class="adjust-btn big" onclick="adjustAmount(25)">+25g</button>
            <button class="adjust-btn big" onclick="adjustAmount(50)">+50g</button>
            <button class="adjust-btn big" onclick="adjustAmount(100)">+100g</button>
        </div>
    </div>
    
    <!-- Simple clickable bar -->
    <div class="click-bar-section">
        <h3>Quick Select (Click anywhere on bar)</h3>
        <div class="click-bar" onclick="handleBarClick(event)">
            <div class="click-bar-fill" id="clickBarFill"></div>
            <div class="click-bar-labels">
                <span>0g</span>
                <span>125g</span>
                <span>250g</span>
                <span>375g</span>
                <span>500g</span>
            </div>
        </div>
    </div>
    
    <!-- All preset amounts -->
    <div class="all-presets">
        <h3>All Preset Amounts</h3>
        <div class="preset-grid"></div>
    </div>
</div>
"""

# JavaScript for amounts functionality - VERY SIMPLE, NO SLIDERS
AMOUNTS_JAVASCRIPT = """
var currentAmountValue = 100;

function getCurrentAmount() {
    try {
        var displayEl = document.querySelector('.amount-display');
        if (displayEl && displayEl.textContent) {
            var match = displayEl.textContent.match(/(\\d+\\.?\\d*)/);
            if (match) {
                var amount = parseFloat(match[1]);
                if (!isNaN(amount)) {
                    currentAmountValue = amount;
                    return amount;
                }
            }
        }
    } catch (e) {
        console.log('Error getting current amount: ' + e);
    }
    return currentAmountValue;
}

function setCurrentAmount(amount) {
    try {
        // Convert and validate
        amount = parseFloat(amount);
        if (isNaN(amount)) amount = 100;
        if (amount < 0) amount = 0;
        if (amount > 500) amount = 500;
        
        currentAmountValue = amount;
        
        // Generate nonce - use simple method
        var nonce = new Date().getTime().toString() + Math.floor(Math.random() * 1000);
        
        // Try to set nonce if function exists
        try {
            if (typeof setMyNonce === 'function') {
                setMyNonce(nonce);
            }
        } catch (e) {
            console.log('setMyNonce not available');
        }
        
        // Send to server
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/set-amount', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    updateAmountDisplay(amount);
                } else {
                    console.log('Error setting amount: ' + xhr.status);
                }
            }
        };
        
        var data = JSON.stringify({amount: amount, nonce: nonce});
        xhr.send(data);
        
    } catch (e) {
        console.log('Error in setCurrentAmount: ' + e);
        // Still update display even if server call fails
        updateAmountDisplay(amount);
    }
}

function setCurrentAmountFromInput() {
    try {
        var input = document.getElementById('amountInput');
        if (input && input.value) {
            setCurrentAmount(input.value);
        }
    } catch (e) {
        console.log('Error setting from input: ' + e);
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
        console.log('Error adjusting amount: ' + e);
    }
}

function updateAmountDisplay(amount) {
    try {
        currentAmountValue = amount;
        
        // Update main display
        var displayEl = document.querySelector('.amount-display');
        if (displayEl) {
            displayEl.textContent = amount + 'g';
        }
        
        // Update header display
        var headerEl = document.querySelector('.current-amount');
        if (headerEl) {
            headerEl.textContent = amount + 'g';
        }
        
        // Update food button indicators
        var indicators = document.querySelectorAll('.food-type-indicator.amount');
        for (var i = 0; i < indicators.length; i++) {
            indicators[i].textContent = amount + 'g';
        }
        
        // Update number input
        var input = document.getElementById('amountInput');
        if (input) {
            input.value = amount;
        }
        
        // Update click bar
        updateClickBar(amount);
        
    } catch (e) {
        console.log('Error updating display: ' + e);
    }
}

function updateClickBar(amount) {
    try {
        var fill = document.getElementById('clickBarFill');
        if (fill) {
            var percentage = (amount / 500) * 100;
            if (percentage < 0) percentage = 0;
            if (percentage > 100) percentage = 100;
            fill.style.width = percentage + '%';
        }
    } catch (e) {
        console.log('Error updating click bar: ' + e);
    }
}

function handleBarClick(event) {
    try {
        var bar = event.currentTarget;
        var rect = bar.getBoundingClientRect();
        var x = event.clientX - rect.left;
        var percentage = x / rect.width;
        if (percentage < 0) percentage = 0;
        if (percentage > 1) percentage = 1;
        
        var amount = Math.round(percentage * 500);
        setCurrentAmount(amount);
        
    } catch (e) {
        console.log('Error handling bar click: ' + e);
    }
}

function createPresetButtons() {
    try {
        var grid = document.querySelector('.preset-grid');
        if (!grid) return;
        
        var presets = [25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400, 450, 500];
        grid.innerHTML = '';
        
        for (var i = 0; i < presets.length; i++) {
            var amount = presets[i];
            var btn = document.createElement('button');
            btn.className = 'preset-btn';
            btn.textContent = amount + 'g';
            
            // Use closure to capture amount
            (function(amt) {
                btn.onclick = function() {
                    setCurrentAmount(amt);
                };
            })(amount);
            
            grid.appendChild(btn);
        }
    } catch (e) {
        console.log('Error creating preset buttons: ' + e);
    }
}

function initializeAmountsTab() {
    try {
        var currentAmount = getCurrentAmount();
        updateAmountDisplay(currentAmount);
        
        setTimeout(function() {
            createPresetButtons();
            updateClickBar(currentAmount);
        }, 100);
        
    } catch (e) {
        console.log('Error initializing amounts tab: ' + e);
        // Try minimal initialization
        setTimeout(function() {
            try {
                createPresetButtons();
            } catch (e2) {
                console.log('Error in fallback initialization: ' + e2);
            }
        }, 300);
    }
}

// Legacy compatibility
function onAmountSliderChange(value) {
    setCurrentAmount(value);
}
"""

# CSS styles - designed for touch and old browsers
AMOUNTS_CSS = """
.amounts-container {
    max-width: 700px;
    margin: 0 auto;
    padding: 20px;
}

.amount-display {
    text-align: center;
    font-size: 3.5em;
    font-weight: 700;
    color: #ffd93d;
    margin-bottom: 30px;
    text-shadow: 0 0 20px rgba(255, 217, 61, 0.3);
    padding: 20px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 15px;
}

/* Number input section */
.amount-input-section {
    text-align: center;
    margin: 30px 0;
    padding: 25px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 15px;
}

.amount-input-section label {
    display: block;
    margin-bottom: 15px;
    color: rgba(255, 255, 255, 0.9);
    font-size: 1.2em;
    font-weight: 600;
}

/* Quick presets - big buttons */
.quick-presets {
    margin: 30px 0;
    text-align: center;
}

.quick-presets h3 {
    font-size: 1.4em;
    margin-bottom: 20px;
    color: rgba(255, 255, 255, 0.8);
}

.preset-row {
    margin: 15px 0;
    display: block;
}

.preset-large {
    background: linear-gradient(135deg, #ffd93d, #ff6b6b);
    border: none;
    border-radius: 12px;
    padding: 20px 25px;
    color: white;
    font-size: 1.4em;
    font-weight: 700;
    cursor: pointer;
    margin: 5px;
    min-width: 120px;
    display: inline-block;
    box-shadow: 0 4px 15px rgba(255, 217, 61, 0.3);
}

.preset-large:hover, .preset-large:active {
    background: linear-gradient(135deg, #ffed4a, #ff8a80);
    transform: translateY(-2px);
}

/* Adjustment section */
.adjustment-section {
    margin: 30px 0;
    text-align: center;
    background: rgba(255, 255, 255, 0.05);
    padding: 25px;
    border-radius: 15px;
}

.adjustment-section h3 {
    font-size: 1.3em;
    margin-bottom: 20px;
    color: rgba(255, 255, 255, 0.8);
}

.adjust-row {
    margin: 12px 0;
}

.adjust-btn {
    background: rgba(255, 255, 255, 0.15);
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 10px;
    padding: 12px 18px;
    color: white;
    font-size: 1.1em;
    font-weight: 600;
    cursor: pointer;
    margin: 4px;
    min-width: 70px;
    display: inline-block;
}

.adjust-btn.big {
    background: rgba(78, 205, 196, 0.2);
    border-color: rgba(78, 205, 196, 0.5);
    padding: 15px 20px;
    font-size: 1.2em;
    min-width: 90px;
}

.adjust-btn:hover, .adjust-btn:active {
    background: rgba(78, 205, 196, 0.3);
    border-color: #4ecdc4;
}

/* Click bar */
.click-bar-section {
    margin: 30px 0;
    background: rgba(255, 255, 255, 0.05);
    padding: 25px;
    border-radius: 15px;
}

.click-bar-section h3 {
    text-align: center;
    font-size: 1.3em;
    margin-bottom: 20px;
    color: rgba(255, 255, 255, 0.8);
}

.click-bar {
    position: relative;
    width: 100%;
    height: 30px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 15px;
    cursor: pointer;
    margin: 20px 0;
}

.click-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #4ecdc4, #00d4ff);
    border-radius: 15px;
    width: 20%;
    transition: width 0.3s ease;
}

.click-bar-labels {
    display: flex;
    justify-content: space-between;
    margin-top: 8px;
    font-size: 0.9em;
    color: rgba(255, 255, 255, 0.6);
}

/* All presets section */
.all-presets {
    margin: 30px 0;
}

.all-presets h3 {
    text-align: center;
    font-size: 1.2em;
    margin-bottom: 15px;
    color: rgba(255, 255, 255, 0.7);
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

/* Mobile optimizations */
@media (max-width: 768px) {
    .amount-display {
        font-size: 3em;
        padding: 15px;
    }
    
    .preset-large {
        padding: 22px 20px;
        font-size: 1.3em;
        min-width: 110px;
        margin: 8px 3px;
    }
    
    .adjust-btn {
        padding: 15px 20px;
        font-size: 1.2em;
        margin: 6px 3px;
    }
    
    .adjust-btn.big {
        padding: 18px 22px;
        font-size: 1.3em;
    }
    
    .click-bar {
        height: 40px;
    }
    
    .preset-btn {
        padding: 15px 18px;
        font-size: 1.1em;
        margin: 5px 2px;
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