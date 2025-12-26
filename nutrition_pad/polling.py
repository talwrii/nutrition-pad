"""
Long polling functionality for real-time updates across devices.
Handles food log updates and amount synchronization.
"""

import time
import threading
from flask import request, jsonify


# Long polling update tracking
last_update = time.time()
update_lock = threading.Lock()
update_event = threading.Event()
current_nonce = None  # Store the nonce from the last update
current_amount = 100  # Server-side amount state
amount_update = time.time()  # Track when amount was last updated


def mark_updated(nonce=None):
    """Mark that data has been updated for long polling"""
    global last_update, current_nonce
    with update_lock:
        last_update = time.time()
        current_nonce = nonce
    update_event.set()
    threading.Timer(0.1, update_event.clear).start()


def mark_amount_updated():
    """Mark that amount has been updated"""
    global amount_update
    with update_lock:
        amount_update = time.time()
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
    
    print(f"[DEBUG] Poll request: since={since}, amount_since={amount_since}, current_amount={current_amount}, amount_update={amount_update}")
    
    with update_lock:
        if last_update > since or amount_update > amount_since:
            response = {
                'updated': last_update > since,
                'timestamp': last_update,
                'item_count': calculate_daily_item_count(),
                'total_protein': calculate_daily_total(),
                'nonce': current_nonce,
                'amount_changed': amount_update > amount_since,
                'current_amount': current_amount
            }
            print(f"[DEBUG] Immediate response: {response}")
            return jsonify(response)
    
    event_occurred = update_event.wait(timeout)
    
    if event_occurred:
        with update_lock:
            if last_update > since or amount_update > amount_since:
                response = {
                    'updated': last_update > since,
                    'timestamp': last_update,
                    'item_count': calculate_daily_item_count(),
                    'total_protein': calculate_daily_total(),
                    'nonce': current_nonce,
                    'amount_changed': amount_update > amount_since,
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
        if new_amount < 0 or new_amount > 500:
            return jsonify({'error': 'Amount must be between 0 and 500'}), 400
        
        old_amount = current_amount
        with update_lock:
            current_amount = new_amount
        
        print(f"[DEBUG] Amount changed from {old_amount} to {current_amount}")
        mark_amount_updated()
        print(f"[DEBUG] Amount update marked, new timestamp: {amount_update}")
        
        return jsonify({'status': 'success', 'amount': current_amount})
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid amount'}), 400


def get_current_amount():
    """Get the current amount value"""
    return current_amount


def register_polling_routes(app):
    """Register polling routes with the Flask app"""
    
    @app.route('/poll-updates')
    def poll_updates_route():
        return poll_updates()
    
    @app.route('/set-amount', methods=['POST'])
    def set_amount_route():
        return set_amount()