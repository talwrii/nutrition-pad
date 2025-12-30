"""
Amounts display and management functionality.
Custom slider built from basic HTML elements - no HTML5 range input.
Works perfectly on old tablets like Galaxy Note 10.1.
"""
from flask import render_template_string

# HTML template with custom slider built from divs
AMOUNTS_TAB_HTML = """
<div class="amounts-container">
    <div class="amount-display">{{ current_amount }}g</div>
    
    <div class="slider-container">
        <!-- Custom slider built from basic HTML -->
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
    
    <!-- Plus/Minus buttons for fine adjustment -->
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

# JavaScript for custom slider functionality
AMOUNTS_JAVASCRIPT = """
var currentAmountValue = 100;
var isDragging = false;
var sliderTrack = null;
var sliderThumb = null;
var sliderFill = null;

function getCurrentAmount() {
    var displayEl = document.querySelector('.current-amount, .amount-display');
    if (displayEl) {
        var match = displayEl.textContent.match(/(\\d+\\.?\\d*)g/);
        if (match) {
            var amount = parseFloat(match[1]);
            currentAmountValue = amount;
            return amount;
        }
    }
    return currentAmountValue;
}

function setCurrentAmount(amount) {
    // Convert and validate
    amount = parseFloat(amount);
    if (isNaN(amount)) amount = 100;
    if (amount < 0) amount = 0;
    if (amount > 500) amount = 500;
    
    currentAmountValue = amount;
    
    // Generate nonce
    var nonce = new Date().getTime().toString() + Math.floor(Math.random() * 1000);
    if (typeof setMyNonce === 'function') {
        setMyNonce(nonce);
    }
    
    // Send to server
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/set-amount', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            updateAmountDisplay(amount);
        }
    };
    
    xhr.send(JSON.stringify({amount: amount, nonce: nonce}));
}

function adjustAmount(delta) {
    var currentAmount = getCurrentAmount();
    var newAmount = Math.max(0, Math.min(500, currentAmount + delta));
    setCurrentAmount(newAmount);
}

function updateAmountDisplay(amount) {
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
    
    // Update custom slider position
    updateSliderPosition(amount);
}

function updateSliderPosition(amount) {
    if (!sliderThumb || !sliderFill) return;
    
    var percentage = Math.max(0, Math.min(100, (amount / 500) * 100));
    sliderThumb.style.left = percentage + '%';
    sliderFill.style.width = percentage + '%';
}

function getClientX(event) {
    if (event.touches && event.touches.length > 0) {
        return event.touches[0].clientX;
    }
    return event.clientX;
}

function handleSliderInteraction(clientX) {
    if (!sliderTrack) return;
    
    var rect = sliderTrack.getBoundingClientRect();
    var x = clientX - rect.left;
    var percentage = Math.max(0, Math.min(1, x / rect.width));
    var amount = Math.round(percentage * 500);
    
    // Update position immediately for smooth interaction
    updateSliderPosition(amount);
    
    // Set the amount
    setCurrentAmount(amount);
}

function initCustomSlider() {
    sliderTrack = document.getElementById('sliderTrack');
    sliderThumb = document.getElementById('sliderThumb');
    sliderFill = document.getElementById('sliderFill');
    
    if (!sliderTrack || !sliderThumb || !sliderFill) return;
    
    // Mouse events for desktop
    sliderThumb.addEventListener('mousedown', function(e) {
        isDragging = true;
        e.preventDefault();
    });
    
    document.addEventListener('mousemove', function(e) {
        if (isDragging) {
            handleSliderInteraction(e.clientX);
        }
    });
    
    document.addEventListener('mouseup', function() {
        isDragging = false;
    });
    
    // Touch events for mobile/tablet
    sliderThumb.addEventListener('touchstart', function(e) {
        isDragging = true;
        e.preventDefault();
    });
    
    document.addEventListener('touchmove', function(e) {
        if (isDragging) {
            handleSliderInteraction(e.touches[0].clientX);
            e.preventDefault();
        }
    });
    
    document.addEventListener('touchend', function() {
        isDragging = false;
    });
    
    // Click on track to jump to position
    sliderTrack.addEventListener('mousedown', function(e) {
        if (e.target === sliderTrack) {
            handleSliderInteraction(e.clientX);
        }
    });
    
    sliderTrack.addEventListener('touchstart', function(e) {
        if (e.target === sliderTrack) {
            handleSliderInteraction(e.touches[0].clientX);
            e.preventDefault();
        }
    });
    
    // Initialize position
    updateSliderPosition(getCurrentAmount());
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
        
        // Use closure to capture amount
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
    
    // Initialize custom slider
    initCustomSlider();
    
    // Create preset buttons
    setTimeout(function() {
        createPresetButtons();
    }, 100);
}

// Legacy compatibility
function onAmountSliderChange(value) {
    setCurrentAmount(value);
}
"""

# CSS styles for custom slider
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

/* Custom slider styles */
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
    transition: transform 0.1s ease, box-shadow 0.1s ease;
}

.slider-thumb:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 20px rgba(255, 217, 61, 0.5);
}

.slider-thumb:active {
    transform: scale(0.95);
}

.slider-labels {
    display: flex;
    justify-content: space-between;
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.9em;
    margin-top: 15px;
    margin-bottom: 10px;
}

/* Plus/minus controls */
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

.amount-btn:hover {
    background: rgba(255, 217, 61, 0.2);
    border-color: #ffd93d;
    transform: translateY(-2px);
}

.amount-btn:active {
    transform: translateY(0);
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

.preset-btn:active {
    transform: translateY(0);
}

/* Mobile optimizations */
@media (max-width: 768px) {
    .amount-display {
        font-size: 2.5em;
    }
    
    .slider-track {
        height: 16px;
    }
    
    .slider-thumb {
        width: 40px;
        height: 40px;
        margin-top: -20px;
        margin-left: -20px;
    }
    
    .amount-btn {
        padding: 15px 20px;
        font-size: 1.1em;
    }
    
    .preset-btn {
        padding: 18px 12px;
        font-size: 1.1em;
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