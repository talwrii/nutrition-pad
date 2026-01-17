"""
Amounts tab functionality - simplified for older browsers (no HTML5 slider)
Renders the amounts selection interface with buttons only
"""

# HTML template for amounts tab
AMOUNTS_TAB_HTML = """
<div id="amounts-tab-content">
    <style>
        .amount-display {
            text-align: center;
            font-size: 4em;
            font-weight: 700;
            color: #ffd93d;
            margin: 40px 0;
            text-shadow: 0 0 30px rgba(255, 217, 61, 0.5);
        }
        
        /* Slider styles */
        .slider-container {
            margin: 30px 20px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
        }
        
        .slider {
            width: 100%;
            height: 12px;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.2);
            outline: none;
            -webkit-appearance: none;
            margin: 20px 0;
        }
        
        .slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: linear-gradient(135deg, #ffd93d, #ff6b6b);
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(255, 217, 61, 0.4);
        }
        
        .slider::-moz-range-thumb {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: linear-gradient(135deg, #ffd93d, #ff6b6b);
            cursor: pointer;
            border: none;
            box-shadow: 0 4px 15px rgba(255, 217, 61, 0.4);
        }
        
        .slider-labels {
            display: flex;
            justify-content: space-between;
            color: rgba(255, 255, 255, 0.5);
            font-size: 0.9em;
            margin-top: 10px;
        }
        
        .amount-controls {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 30px 20px;
            flex-wrap: wrap;
        }
        
        .amount-btn {
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 15px;
            color: white;
            font-size: 1.5em;
            font-weight: 600;
            padding: 20px 30px;
            cursor: pointer;
            transition: all 0.3s ease;
            min-width: 100px;
            min-height: 60px;
        }
        
        .amount-btn:hover {
            background: rgba(0, 212, 255, 0.2);
            border-color: #00d4ff;
            transform: translateY(-2px);
        }
        
        .amount-btn:active {
            transform: translateY(0);
        }
        
        .preset-amounts {
            margin: 40px 20px;
            text-align: center;
        }
        
        .preset-amounts h3 {
            color: rgba(255, 255, 255, 0.7);
            font-size: 1.3em;
            margin-bottom: 20px;
        }
        
        .preset-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            max-width: 600px;
            margin: 0 auto;
        }
        
        .preset-btn {
            background: rgba(78, 205, 196, 0.15);
            border: 2px solid rgba(78, 205, 196, 0.3);
            border-radius: 12px;
            color: #4ecdc4;
            font-size: 1.3em;
            font-weight: 600;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .preset-btn:hover {
            background: rgba(78, 205, 196, 0.3);
            border-color: #4ecdc4;
            transform: scale(1.05);
        }
        
        .preset-btn:active {
            transform: scale(0.95);
        }
        
        @media (max-width: 768px) {
            .amount-display {
                font-size: 3em;
                margin: 30px 0;
            }
            
            .amount-btn {
                font-size: 1.2em;
                padding: 15px 20px;
                min-width: 80px;
            }
            
            .preset-grid {
                grid-template-columns: repeat(4, 1fr);
                gap: 10px;
            }
            
            .preset-btn {
                font-size: 1.1em;
                padding: 15px 10px;
            }
        }
    </style>
    
    <div class="amount-display" id="amount-display">{{ current_amount }}g</div>
    
    <!-- Slider for amount selection -->
    <div class="slider-container">
        <input type="range" min="0" max="400" value="{{ current_amount }}"
               class="slider" id="amountSlider"
               onchange="setAmountTo(parseInt(this.value))"
               oninput="updateSliderDisplay(this.value)">
        <div class="slider-labels">
            <span>0g</span>
            <span>100g</span>
            <span>200g</span>
            <span>300g</span>
            <span>400g</span>
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
        <div class="preset-grid" id="preset-grid"></div>
    </div>
</div>
"""

# JavaScript for amounts functionality - NOW WITH SERVER SYNC
# NOTE: No <script> tags here - this is injected into an existing script block
AMOUNTS_JAVASCRIPT = """
(function() {
    var currentAmount = parseInt('{{ current_amount }}') || 100;
    var syncTimeout = null;
    var myNonce = null;
    
    // Generate a unique nonce for this client
    function generateNonce() {
        return Date.now().toString() + Math.random().toString(36).substr(2);
    }
    
    // Sync amount to server
    function syncToServer(amount) {
        myNonce = generateNonce();
        
        // Set the nonce for the polling system to recognize our own updates
        if (typeof setMyNonce === 'function') {
            setMyNonce(myNonce);
        }
        
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/set-amount', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    console.log('[Amounts] Synced to server: ' + amount + 'g');
                } else {
                    console.error('[Amounts] Sync failed: ' + xhr.status);
                }
            }
        };
        xhr.send(JSON.stringify({amount: amount, nonce: myNonce}));
    }
    
    // Debounced sync - wait for slider to stop moving before syncing
    function debouncedSync(amount) {
        if (syncTimeout) {
            clearTimeout(syncTimeout);
        }
        syncTimeout = setTimeout(function() {
            syncToServer(amount);
        }, 100);  // 100ms debounce
    }
    
    // Update amount display only (no server call) - for drag feedback
    function updateSliderDisplay(amount) {
        var display = document.getElementById('amount-display');
        if (display) {
            display.textContent = amount + 'g';
        }
    }
    
    // Update amount display AND sync to server
    function updateDisplay(amount) {
        var display = document.getElementById('amount-display');
        if (display) {
            display.textContent = amount + 'g';
        }
        
        // Update header display
        var headerAmount = document.querySelector('.current-amount');
        if (headerAmount) {
            headerAmount.textContent = amount + 'g';
        }
        
        // Update slider position
        var slider = document.getElementById('amountSlider');
        if (slider) {
            slider.value = amount;
        }
        
        // SYNC TO SERVER - this was the missing piece!
        debouncedSync(amount);
    }
    
    // Adjust amount by delta
    window.adjustAmount = function(delta) {
        currentAmount = currentAmount + delta;
        if (currentAmount < 0) currentAmount = 0;
        if (currentAmount > 400) currentAmount = 400;
        updateDisplay(currentAmount);
    };
    
    // Set amount to specific value
    window.setAmountTo = function(amount) {
        currentAmount = amount;
        updateDisplay(currentAmount);
    };
    
    // Update display during slider drag (without server call for smooth UX)
    window.updateSliderDisplay = function(amount) {
        var display = document.getElementById('amount-display');
        if (display) {
            display.textContent = amount + 'g';
        }
        currentAmount = parseInt(amount);
        // Debounced sync while dragging
        debouncedSync(currentAmount);
    };
    
    // Get current amount (for other scripts)
    window.getCurrentAmount = function() {
        return currentAmount;
    };
    
    // Update amount from server (called by polling)
    window.updateAmountDisplay = function(amount) {
        currentAmount = parseInt(amount);
        var display = document.getElementById('amount-display');
        if (display) {
            display.textContent = currentAmount + 'g';
        }
        var headerAmount = document.querySelector('.current-amount');
        if (headerAmount) {
            headerAmount.textContent = currentAmount + 'g';
        }
        var slider = document.getElementById('amountSlider');
        if (slider) {
            slider.value = currentAmount;
        }
    };
    
    // Initialize preset buttons
    function initializePresets() {
        var presetGrid = document.getElementById('preset-grid');
        if (!presetGrid) return;
        
        var presets = [50, 100, 150, 200, 250, 300, 350, 400];
        presetGrid.innerHTML = '';
        
        for (var i = 0; i < presets.length; i++) {
            var amount = presets[i];
            var btn = document.createElement('button');
            btn.className = 'preset-btn';
            btn.textContent = amount + 'g';
            btn.onclick = (function(amt) {
                return function() {
                    setAmountTo(amt);
                };
            })(amount);
            presetGrid.appendChild(btn);
        }
    }
    
    // Initialize on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializePresets);
    } else {
        initializePresets();
    }
})();
"""

def render_amounts_tab(current_amount):
    """Render the amounts tab HTML"""
    return AMOUNTS_TAB_HTML.replace('{{ current_amount }}', str(current_amount))

def get_amounts_javascript(current_amount=100):
    """Get the amounts tab JavaScript"""
    return AMOUNTS_JAVASCRIPT.replace('{{ current_amount }}', str(current_amount))