# Add this endpoint to nutrition_pad/main.py
# Insert before the existing @app.route('/api/foods', methods=['POST']) endpoint

@app.route('/api/resolve-unknown', methods=['POST'])
def api_resolve_unknown():
    """API endpoint to resolve unknown food entries"""
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    entry_ids = data.get('entry_ids', [])
    food_key = data.get('food_key')
    
    if not entry_ids or not food_key:
        return jsonify({'success': False, 'error': 'Missing entry_ids or food_key'}), 400
    
    # Find the food in the config
    pad_key = None
    food_data = None
    
    pads = get_all_pads()
    for pk, pad_data in pads.items():
        if pk == 'amounts':
            continue
        foods = pad_data.get('foods', {})
        if food_key in foods:
            pad_key = pk
            food_data = foods[food_key]
            break
    
    if not food_data:
        return jsonify({'success': False, 'error': f'Food "{food_key}" not found'}), 404
    
    # Find and update entries in log files
    updated_count = 0
    updated_entries = []
    
    for filename in sorted(os.listdir(LOGS_DIR), reverse=True):
        if not filename.endswith('.json') or filename.endswith('_notes.json'):
            continue
        
        filepath = os.path.join(LOGS_DIR, filename)
        
        try:
            with open(filepath, 'r') as f:
                entries = json.load(f)
        except:
            continue
        
        modified = False
        for entry in entries:
            if entry.get('id') in entry_ids:
                # Resolve the entry
                amount = entry.get('amount', 100)
                
                if food_data.get('type') == 'unit':
                    calories = food_data.get('calories', 0)
                    protein = food_data.get('protein', 0)
                    fiber = food_data.get('fiber', 0)
                    amount_display = "1 unit"
                else:
                    calories = food_data.get('calories_per_gram', 0) * amount
                    protein = food_data.get('protein_per_gram', 0) * amount
                    fiber = food_data.get('fiber_per_gram', 0) * amount
                    amount_display = f"{amount}g"
                
                entry['pad'] = pad_key
                entry['food'] = food_key
                entry['name'] = food_data.get('name', food_key)
                entry['calories'] = round(calories, 1)
                entry['protein'] = round(protein, 1)
                entry['fiber'] = round(fiber, 1)
                entry['amount_display'] = amount_display
                
                modified = True
                updated_count += 1
                updated_entries.append({
                    'id': entry['id'],
                    'date': filename.replace('.json', ''),
                    'calories': entry['calories'],
                    'protein': entry['protein']
                })
        
        if modified:
            with open(filepath, 'w') as f:
                json.dump(entries, f, indent=2)
            
            # Trigger update notification
            mark_updated("resolve_unknown")
    
    return jsonify({
        'success': True,
        'updated_count': updated_count,
        'total_requested': len(entry_ids),
        'updated_entries': updated_entries,
        'food_name': food_data.get('name', food_key)
    })