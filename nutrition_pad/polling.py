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

# Heartbeat tracking for watchdog
last_heartbeat = time.time()
heartbeat_lock = threading.Lock()

# JavaScript for polling functionality
POLLING_JAVASCRIPT = """
var lastUpdate = parseFloat(localStorage.getItem('lastUpdate') || '0');
var lastAmountUpdate = parseFloat(localStorage.getItem('lastAmountUpdate') || '0');
var isPolling = false;
var myNonce = null;
var debugMode = false; // Will be set by main template

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
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            isPolling = false;
            
            if (xhr.status === 200) {
                try {
                    var data = JSON.parse(xhr.responseText);
                    debug('Poll response: updated=' + data.updated + ', current_amount=' + data.current_amount);
                    
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
}

// Heartbeat functionality for watchdog
function sendHeartbeat() {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/heartbeat', true);
    xhr.send();
}

function startHeartbeat() {
    // Send heartbeat every 10 seconds
    setInterval(sendHeartbeat, 10000);
    // Send initial heartbeat immediately
    sendHeartbeat();
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
                'current_amount': current_amount
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
                    'current_amount': current_amount
                }
                print(f"[DEBUG] Event response: {response}")
                return jsonify(response)
    
    return jsonify({
        'updated': False,
        'amount_changed': False,
        'current_amount': current_amount
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

def get_polling_javascript():
    """Get the JavaScript code for polling functionality"""
    return POLLING_JAVASCRIPT

def heartbeat():
    """Heartbeat endpoint to track that the client is alive"""
    global last_heartbeat
    with heartbeat_lock:
        last_heartbeat = time.time()
    return jsonify({'status': 'ok', 'timestamp': last_heartbeat})

def get_last_heartbeat():
    """Get the last heartbeat timestamp (for watchdog monitoring)"""
    with heartbeat_lock:
        return last_heartbeat

def register_polling_routes(app):
    """Register polling routes with the Flask app"""

    @app.route('/poll-updates')
    def poll_updates_route():
        return poll_updates()

    @app.route('/set-amount', methods=['POST'])
    def set_amount_route():
        return set_amount()

    @app.route('/heartbeat', methods=['GET', 'POST'])
    def heartbeat_route():
        return heartbeat()

    @app.route('/static/polling.js')
    def polling_js():
        return Response(POLLING_JAVASCRIPT, mimetype='application/javascript')