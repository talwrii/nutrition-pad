"""
Long polling functionality for real-time updates across devices.
Handles food log updates and amount synchronization.
"""
import time
import threading
from flask import request, jsonify, Response

# Long polling update tracking
last_update = time.time()
update_lock = threading.Lock()
update_event = threading.Event()
current_nonce = None  # Store the nonce from the last update
current_amount = 100.0  # Server-side amount state - ensure it's a float
meal_mode_active = False  # Server-side meal mode state - shared across all clients

# JavaScript for polling functionality
POLLING_JAVASCRIPT = """
var lastUpdate = parseFloat(localStorage.getItem('lastUpdate') || '0');
var lastAmountUpdate = parseFloat(localStorage.getItem('lastAmountUpdate') || '0');
var isPolling = false;
var myNonce = null;
var debugMode = false; // Will be set by main template

// Keepalive tracking - if no poll response for this long, refresh the page
var lastPollResponse = Date.now();
var KEEPALIVE_TIMEOUT = 60000; // 60 seconds

// Server timestamp tracking - detect when server is stuck
// We check if server_timestamp CHANGES between responses (not comparing to client time!)
var lastServerTimestamp = 0;
var stuckServerCount = 0;
var MAX_STUCK_RESPONSES = 3; // If we get 3 responses with SAME server timestamp, server is stuck

function debug(msg) {
    if (debugMode) {
        console.log('[DEBUG] ' + msg);
        var debugEl = document.getElementById('debug') || document.createElement('div');
        if (!debugEl.id) {
            debugEl.id = 'debug';
            debugEl.style.cssText = 'position:fixed;top:0;right:0;background:red;color:white;padding:5px;font-size:12px;z-index:9999;max-width:200px;';
            document.body.appendChild(debugEl);
        }
        debugEl.innerHTML = new Date().toTimeString().substr(0,8) + ': ' + msg;
    }
}

function checkKeepalive() {
    var timeSinceLastPoll = Date.now() - lastPollResponse;
    if (timeSinceLastPoll > KEEPALIVE_TIMEOUT) {
        debug('KEEPALIVE TIMEOUT! No poll response for ' + Math.round(timeSinceLastPoll/1000) + 's - refreshing page');
        console.error('Polling stuck - no response for ' + Math.round(timeSinceLastPoll/1000) + ' seconds, forcing page refresh');
        window.location.reload();
    }
}

function generateNonce() {
    return Date.now().toString() + Math.random().toString(36).substr(2);
}

function poll() {
    if (isPolling) {
        debug('Poll already running, skipping');
        return;
    }

    isPolling = true;
    debug('Starting poll, lastUpdate: ' + lastUpdate + ', lastAmountUpdate: ' + lastAmountUpdate);

    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/poll-updates?since=' + lastUpdate + '&amount_since=' + lastAmountUpdate, true);

    // Set timeout on the XHR - if it hangs for 45 seconds, refresh the page
    xhr.timeout = 45000;

    xhr.ontimeout = function() {
        debug('Poll timeout - XHR hung for 45s, refreshing page');
        console.error('Polling XHR timeout after 45s - forcing page refresh');
        window.location.reload();
    };

    xhr.onerror = function() {
        debug('Poll error - network issue, refreshing page');
        console.error('Polling XHR error - forcing page refresh');
        window.location.reload();
    };

    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            isPolling = false;

            // Update keepalive timestamp - we got a response (any response)
            lastPollResponse = Date.now();

            if (xhr.status === 200) {
                try {
                    var data = JSON.parse(xhr.responseText);
                    debug('Poll response: updated=' + data.updated + ', current_amount=' + data.current_amount +
                          (data.server_timestamp ? ', server_ts=' + data.server_timestamp : ''));

                    // Check if server is stuck by seeing if its timestamp changes between responses
                    // (We're NOT comparing server time to client time - just checking if it advances)
                    if (data.server_timestamp) {
                        if (lastServerTimestamp > 0 && data.server_timestamp === lastServerTimestamp) {
                            // Server sent the EXACT SAME timestamp as last time - it's stuck!
                            stuckServerCount++;
                            debug('Server timestamp unchanged: ' + data.server_timestamp + ' (' + stuckServerCount + '/' + MAX_STUCK_RESPONSES + ')');
                            if (stuckServerCount >= MAX_STUCK_RESPONSES) {
                                debug('Server appears stuck - same timestamp ' + MAX_STUCK_RESPONSES + ' times, refreshing page');
                                console.error('Server stuck - returning same timestamp, forcing page refresh');
                                window.location.reload();
                                return;
                            }
                        } else {
                            // Server timestamp changed (or first response) - server is alive
                            lastServerTimestamp = data.server_timestamp;
                            stuckServerCount = 0;
                        }
                    }

                    if (data.updated && data.timestamp > lastUpdate) {
                        lastUpdate = data.timestamp;
                        localStorage.setItem('lastUpdate', lastUpdate.toString());

                        if (data.nonce && myNonce && data.nonce === myNonce) {
                            debug('Skipping refresh - this was my update (nonce: ' + myNonce + ')');
                            myNonce = null;
                        } else {
                            debug('Refreshing - update from other device (nonce: ' + data.nonce + ')');
                            var itemCountEl = document.querySelector('.item-count');
                            if (itemCountEl) {
                                itemCountEl.textContent = data.item_count + ' items logged today';
                            }

                            // Update amount display too
                            if (typeof updateAmountDisplay === 'function') {
                                updateAmountDisplay(data.current_amount);
                            }

                            setTimeout(function() {
                                window.location.reload();
                            }, 1000);
                            return;
                        }
                    }

                    if (!data.updated) {
                        debug('No updates');
                    }

                    // Handle meal mode changes from server
                    if (typeof data.meal_mode !== 'undefined') {
                        var mealBg = 'linear-gradient(135deg, #1a2a2e 0%, #163e3e 50%, #0f4660 100%)';
                        var normalBg = 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)';
                        if (data.meal_mode) {
                            document.body.style.background = mealBg;
                            sessionStorage.setItem('mealMode', '1');
                            // Update local mealMode variable if it exists (food pads page)
                            if (typeof window.setMealModeFromServer === 'function') {
                                window.setMealModeFromServer(true);
                            }
                            var ind = document.getElementById('meal-mode-indicator');
                            if (ind) ind.style.display = 'block';
                        } else {
                            document.body.style.background = normalBg;
                            sessionStorage.removeItem('mealMode');
                            if (typeof window.setMealModeFromServer === 'function') {
                                window.setMealModeFromServer(false);
                            }
                            var ind = document.getElementById('meal-mode-indicator');
                            if (ind) ind.style.display = 'none';
                        }
                    }
                } catch (e) {
                    debug('JSON parse error: ' + e.message);
                }
            } else {
                debug('HTTP error: ' + xhr.status);
            }

            setTimeout(poll, 2000); // Poll every 2 seconds for immediate syncing
        }
    };
    xhr.send();
}

function startLongPolling() {
    poll();
    // Check keepalive every 10 seconds
    setInterval(checkKeepalive, 10000);
}

// Expose functions that main.js might need
function setMyNonce(nonce) {
    myNonce = nonce;
    debug('Set my nonce to: ' + nonce);
}

function setDebugMode(enabled) {
    debugMode = enabled;
}
"""

def mark_updated(nonce=None):
    """Mark that data has been updated for long polling"""
    global last_update, current_nonce
    with update_lock:
        last_update = time.time()
        current_nonce = nonce
    update_event.set()
    threading.Timer(0.1, update_event.clear).start()

def mark_amount_updated(nonce=None):
    """Mark that amount has been updated"""
    global last_update, current_nonce
    with update_lock:
        last_update = time.time()
        current_nonce = nonce
    # Use the same event mechanism to wake up long polling requests
    update_event.set()
    threading.Timer(0.1, update_event.clear).start()

def poll_updates():
    """Long polling endpoint using threading events"""
    # Import here to avoid circular imports
    from .data import calculate_daily_item_count, calculate_daily_total
    
    since = float(request.args.get('since', 0))
    amount_since = float(request.args.get('amount_since', 0))
    timeout = 30
    
    print(f"[DEBUG] Poll request: since={since}, amount_since={amount_since}, current_amount={current_amount}")
    
    with update_lock:
        if last_update > since:
            response = {
                'updated': last_update > since,
                'timestamp': last_update,
                'item_count': calculate_daily_item_count(),
                'total_protein': calculate_daily_total(),
                'nonce': current_nonce,
                'current_amount': current_amount,
                'server_timestamp': time.time(),
                'meal_mode': meal_mode_active
            }
            print(f"[DEBUG] Immediate response: {response}")
            return jsonify(response)
    
    event_occurred = update_event.wait(timeout)
    
    if event_occurred:
        with update_lock:
            if last_update > since:
                response = {
                    'updated': last_update > since,
                    'timestamp': last_update,
                    'item_count': calculate_daily_item_count(),
                    'total_protein': calculate_daily_total(),
                    'nonce': current_nonce,
                    'current_amount': current_amount,
                    'server_timestamp': time.time(),
                    'meal_mode': meal_mode_active
                }
                print(f"[DEBUG] Event response: {response}")
                return jsonify(response)
    
    # No update, but send server timestamp as keepalive
    return jsonify({
        'updated': False,
        'amount_changed': False,
        'current_amount': current_amount,
        'server_timestamp': time.time(),
        'meal_mode': meal_mode_active
    })

def set_amount():
    """Set the current amount"""
    global current_amount
    
    data = request.json
    if not data or 'amount' not in data:
        return jsonify({'error': 'No amount provided'}), 400
    
    try:
        new_amount = float(data['amount'])
        nonce = data.get('nonce')  # Extract nonce from request
        
        if new_amount < 0 or new_amount > 500:
            return jsonify({'error': 'Amount must be between 0 and 500'}), 400
        
        old_amount = current_amount
        with update_lock:
            current_amount = new_amount
        
        print(f"[DEBUG] Amount changed from {old_amount} to {current_amount} (nonce: {nonce})")
        mark_amount_updated(nonce)  # Pass nonce to mark_amount_updated
        print(f"[DEBUG] Amount update marked, new timestamp: {last_update}")
        
        return jsonify({'status': 'success', 'amount': current_amount})
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid amount'}), 400

def get_current_amount():
    """Get the current amount value"""
    return current_amount

def get_meal_mode():
    """Get the current meal mode state"""
    return meal_mode_active

def set_meal_mode(active):
    """Set the meal mode state and notify all clients"""
    global meal_mode_active
    with update_lock:
        meal_mode_active = active
    # Wake up polling clients to inform them of the change
    update_event.set()
    threading.Timer(0.1, update_event.clear).start()

def get_polling_javascript():
    """Get the JavaScript code for polling functionality"""
    return POLLING_JAVASCRIPT

def register_polling_routes(app):
    """Register polling routes with the Flask app"""

    @app.route('/poll-updates')
    def poll_updates_route():
        return poll_updates()

    @app.route('/set-amount', methods=['POST'])
    def set_amount_route():
        return set_amount()

    @app.route('/set-meal-mode', methods=['POST'])
    def set_meal_mode_route():
        data = request.json
        if data is None:
            return jsonify({'error': 'No JSON data'}), 400
        active = data.get('active', False)
        set_meal_mode(active)
        return jsonify({'status': 'success', 'meal_mode': active})

    @app.route('/static/polling.js')
    def polling_js():
        return Response(POLLING_JAVASCRIPT, mimetype='application/javascript')