"""
Amounts display and management functionality.
Handles the amounts tab with slider, preset buttons, and amount setting.
Enhanced for older tablet compatibility.
"""
from flask import render_template_string

# HTML template for the amounts tab content
AMOUNTS_TAB_HTML = """
<div class="amounts-container">
    <div class="amount-display">{{ current_amount }}g</div>
    
    <div class="slider-container">
        <!-- Native HTML5 slider for modern browsers -->
        <input type="range" min="0" max="500" value="{{ current_amount }}" 
               class="slider native-slider" id="amountSlider" 
               onchange="setCurrentAmount(this.value)"
               oninput="setCurrentAmount(this.value)">
        
        <!-- Fallback custom slider for older browsers -->
        <div class="custom-slider" id="customSlider" style="display: none;">
            <div class="custom-slider-track" id="sliderTrack">
                <div class="custom-slider-thumb" id="sliderThumb"></div>
            </div>
        </div>
        
        <div style="display: flex; justify-content: space-between; color: rgba(255,255,255,0.5); font-size: 0.9em; margin-top: 10px;">
            <span>0g</span>
            <span>250g</span>
            <span>500g</span>
        </div>
    </div>
    
    <!-- Plus/Minus buttons for easier adjustment on touch devices -->
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
// Store current amount value
var currentAmountValue = 100;
var isCustomSlider = false;

function getCurrentAmount() {
    var displayEl = document.querySelector('.current-amount, .amount-display');
    debug('getCurrentAmount: displayEl = ' + (displayEl ? displayEl.textContent : 'null'));
    
    if (displayEl) {
        var match = displayEl.textContent.match(/(\d+\.?\d*)g/);
        debug('getCurrentAmount: regex match = ' + (match ? match[1] : 'null'));
        if (match) {
            var amount = parseFloat(match[1]);
            debug('getCurrentAmount: returning ' + amount);
            currentAmountValue = amount;
            return amount;
        }
    }
    debug('getCurrentAmount: falling back to ' + currentAmountValue);
    return currentAmountValue;
}

function setCurrentAmount(amount) {
    debug('=== setCurrentAmount called ===');
    debug('Input amount: ' + amount + ' (type: ' + typeof amount + ')');
    
    // Check for problematic values
    if (amount == 0) {
        debug('WARNING: Amount is 0! Call stack:');
        console.trace();
    }
    if (amount === undefined || amount === null) {
        debug('WARNING: Amount is undefined/null! Call stack:');
        console.trace();
        amount = 100; // Force fallback
    }
    if (isNaN(amount)) {
        debug('WARNING: Amount is NaN! Call stack:');
        console.trace();
        amount = 100; // Force fallback
    }
    
    // Convert to number and clamp to valid range
    amount = Math.max(0, Math.min(500, parseFloat(amount)));
    currentAmountValue = amount;
    debug('Clamped amount: ' + amount);
    
    // Generate nonce and set it so we don't refresh ourselves
    var nonce = generateNonce();
    debug('Setting amount with nonce: ' + nonce);
    setMyNonce(nonce);
    
    // Send amount to server
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/set-amount', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            debug('Amount set successfully to: ' + amount);
            updateAmountDisplay(amount);
        } else if (xhr.readyState === 4) {
            debug('Error setting amount: ' + xhr.status);
        }
    };
    
    debug('Sending to server: ' + JSON.stringify({amount: amount, nonce: nonce}));
    xhr.send(JSON.stringify({amount: amount, nonce: nonce}));
}

function adjustAmount(delta) {
    var currentAmount = getCurrentAmount();
    var newAmount = Math.max(0, Math.min(500, currentAmount + delta));
    debug('Adjusting amount from ' + currentAmount + ' by ' + delta + ' to ' + newAmount);
    setCurrentAmount(newAmount);
}

function updateAmountDisplay(amount) {
    debug('updateAmountDisplay called with: ' + amount + ' (type: ' + typeof amount + ')');
    
    if (amount == 0) {
        debug('WARNING: updateAmountDisplay received 0! Call stack:');
        console.trace();
    }
    
    currentAmountValue = amount;
    
    var amountEls = document.querySelectorAll('.current-amount, .amount-display');
    debug('Found ' + amountEls.length + ' amount display elements');
    
    amountEls.forEach(function(el) {
        debug('Updating element from "' + el.textContent + '" to "' + amount + 'g"');
        el.textContent = amount + 'g';
    });
    
    // Update amount indicators on food buttons
    var amountIndicators = document.querySelectorAll('.food-type-indicator.amount');
    amountIndicators.forEach(function(el) {
        el.textContent = amount + 'g';
    });
    
    // Update native slider if it exists and is working
    var sliderEl = document.getElementById('amountSlider');
    if (sliderEl && !isCustomSlider) {
        debug('Updating native slider from ' + sliderEl.value + ' to ' + amount);
        sliderEl.value = amount;
    }
    
    // Update custom slider if active
    if (isCustomSlider) {
        updateCustomSliderPosition(amount);
    }
}

// Custom slider implementation for older browsers
function initCustomSlider() {
    var customSlider = document.getElementById('customSlider');
    var nativeSlider = document.getElementById('amountSlider');
    var track = document.getElementById('sliderTrack');
    var thumb = document.getElementById('sliderThumb');
    
    if (!customSlider || !track || !thumb) return;
    
    // Test if native slider works with touch
    var needsCustomSlider = false;
    try {
        // Simple test - if we're on a touch device and the browser is old
        if ('ontouchstart' in window) {
            var userAgent = navigator.userAgent;
            if (userAgent.indexOf('Android') > -1 && userAgent.indexOf('Chrome') === -1) {
                // Old Android browser without Chrome
                needsCustomSlider = true;
            }
        }
    } catch (e) {
        // If there's any error, fall back to custom slider
        needsCustomSlider = true;
    }
    
    if (needsCustomSlider) {
        debug('Using custom slider for compatibility');
        isCustomSlider = true;
        nativeSlider.style.display = 'none';
        customSlider.style.display = 'block';
        
        var isDragging = false;
        var startX = 0;
        var trackRect = null;
        
        function updateSliderFromPosition(clientX) {
            if (!trackRect) trackRect = track.getBoundingClientRect();
            
            var x = clientX - trackRect.left;
            var percentage = Math.max(0, Math.min(1, x / trackRect.width));
            var amount = Math.round(percentage * 500);
            
            updateCustomSliderPosition(amount);
            setCurrentAmount(amount);
        }
        
        // Mouse events
        thumb.addEventListener('mousedown', function(e) {
            isDragging = true;
            startX = e.clientX;
            trackRect = track.getBoundingClientRect();
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', function(e) {
            if (isDragging) {
                updateSliderFromPosition(e.clientX);
            }
        });
        
        document.addEventListener('mouseup', function() {
            isDragging = false;
            trackRect = null;
        });
        
        // Touch events for mobile
        thumb.addEventListener('touchstart', function(e) {
            isDragging = true;
            startX = e.touches[0].clientX;
            trackRect = track.getBoundingClientRect();
            e.preventDefault();
        });
        
        document.addEventListener('touchmove', function(e) {
            if (isDragging) {
                updateSliderFromPosition(e.touches[0].clientX);
                e.preventDefault();
            }
        });
        
        document.addEventListener('touchend', function() {
            isDragging = false;
            trackRect = null;
        });
        
        // Track click/touch
        track.addEventListener('click', function(e) {
            trackRect = track.getBoundingClientRect();
            updateSliderFromPosition(e.clientX);
        });
        
        track.addEventListener('touchstart', function(e) {
            if (e.target === track) {
                trackRect = track.getBoundingClientRect();
                updateSliderFromPosition(e.touches[0].clientX);
                e.preventDefault();
            }
        });
        
        // Initialize position
        updateCustomSliderPosition(getCurrentAmount());
    } else {
        debug('Using native slider');
        // Enhance native slider for better touch support
        nativeSlider.addEventListener('input', function() {
            setCurrentAmount(this.value);
        });
    }
}

function updateCustomSliderPosition(amount) {
    var thumb = document.getElementById('sliderThumb');
    if (thumb && isCustomSlider) {
        var percentage = Math.max(0, Math.min(100, (amount / 500) * 100));
        thumb.style.left = percentage + '%';
        debug('Updated custom slider position to ' + percentage + '%');
    }
}

function createPresetButtons() {
    var presetGrid = document.querySelector('.preset-grid');
    if (!presetGrid) {
        debug('Warning: .preset-grid element not found');
        return;
    }
    
    var presets = [25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 300, 400, 500];
    presetGrid.innerHTML = '';
    
    debug('Creating ' + presets.length + ' preset buttons');
    
    presets.forEach(function(amount) {
        var btn = document.createElement('button');
        btn.className = 'preset-btn';
        btn.textContent = amount + 'g';
        btn.onclick = function() { 
            debug('Preset button clicked: ' + amount + 'g');
            setCurrentAmount(amount); 
        };
        presetGrid.appendChild(btn);
    });
    
    debug('Preset buttons created successfully');
}

// Initialize amounts tab with enhanced compatibility
function initializeAmountsTab() {
    debug('Initializing amounts tab with enhanced compatibility');
    
    // Update display
    if (typeof updateAmountDisplay === 'function') {
        updateAmountDisplay(getCurrentAmount());
    }
    
    // Initialize custom slider if needed
    setTimeout(function() {
        initCustomSlider();
        
        // Create preset buttons with retry logic
        createPresetButtons();
        
        // If no buttons were created, try again after a short delay
        var buttons = document.querySelectorAll('.preset-btn');
        if (buttons.length === 0) {
            debug('No preset buttons found, retrying...');
            setTimeout(createPresetButtons, 500);
        }
    }, 100);
}

function onAmountSliderChange(value) {
    setCurrentAmount(parseFloat(value));
}
"""

# CSS styles specific to amounts (enhanced for older browsers)
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

/* Native slider styles */
.slider.native-slider {
    width: 100%;
    height: 8px;
    border-radius: 4px;
    background: rgba(255, 255, 255, 0.2);
    outline: none;
    -webkit-appearance: none;
    margin: 20px 0;
}

.slider.native-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: linear-gradient(135deg, #ffd93d, #ff6b6b);
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(255, 217, 61, 0.3);
}

.slider.native-slider::-moz-range-thumb {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: linear-gradient(135deg, #ffd93d, #ff6b6b);
    cursor: pointer;
    border: none;
    box-shadow: 0 4px 15px rgba(255, 217, 61, 0.3);
}

/* Custom slider for older browsers */
.custom-slider {
    padding: 20px 0;
}

.custom-slider-track {
    position: relative;
    width: 100%;
    height: 8px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    cursor: pointer;
}

.custom-slider-thumb {
    position: absolute;
    top: 50%;
    width: 30px;
    height: 30px;
    background: linear-gradient(135deg, #ffd93d, #ff6b6b);
    border-radius: 50%;
    transform: translate(-50%, -50%);
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(255, 217, 61, 0.3);
    transition: box-shadow 0.2s ease;
}

.custom-slider-thumb:hover {
    box-shadow: 0 6px 20px rgba(255, 217, 61, 0.4);
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
    touch-action: manipulation; /* Improve touch responsiveness */
}

.amount-btn:hover {
    background: rgba(255, 217, 61, 0.2);
    border-color: #ffd93d;
    transform: translateY(-2px);
}

.amount-btn:active {
    transform: translateY(0);
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
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
    touch-action: manipulation; /* Improve touch responsiveness */
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
    
    .amount-controls {
        margin: 30px 0;
    }
    
    .amount-btn {
        padding: 15px 20px;
        font-size: 1.1em;
    }
    
    .custom-slider-thumb {
        width: 40px;
        height: 40px;
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