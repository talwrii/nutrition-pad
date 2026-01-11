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

# JavaScript for amounts functionality - simplified for older browsers
AMOUNTS_JAVASCRIPT = """
<script>
(function() {
    var currentAmount = parseInt('{{ current_amount }}') || 100;
    
    // Update amount display
    function updateDisplay(amount) {
        var display = document.getElementById('amount-display');
        if (display) {
            display.textContent = amount + 'g';
        }
        
        // Update global amount in parent page
        if (window.setAmount) {
            window.setAmount(amount);
        }
        
        // Update header display
        var headerAmount = document.querySelector('.current-amount');
        if (headerAmount) {
            headerAmount.textContent = amount + 'g';
        }
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
</script>
"""

def render_amounts_tab(current_amount):
    """Render the amounts tab HTML"""
    return AMOUNTS_TAB_HTML.replace('{{ current_amount }}', str(current_amount))

def get_amounts_javascript():
    """Get the amounts tab JavaScript"""
    return AMOUNTS_JAVASCRIPT