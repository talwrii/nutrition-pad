# Nutrition Pad Project Memory

## Project Overview
Nutrition tracking application with CGM integration and tablet UI. Flask backend with JavaScript polling for real-time updates across devices.

## Important Context
- This is a personal nutrition tracking app
- Runs on a tablet that sometimes gets stuck/frozen
- Uses long polling for real-time synchronization between devices
- Main branch: `master`

## Recent Changes

### Watchdog System (Added 2026-01-22)
Added a keepalive/watchdog system to detect and restart the server when the tablet gets stuck:

**Components:**
1. **Heartbeat endpoint**: `/heartbeat` - tracks client activity
2. **JavaScript heartbeat**: Client sends heartbeat every 10 seconds
3. **Watchdog script**: `watchdog.py` - monitors heartbeat and restarts server if stale
4. **Startup script**: `start-with-watchdog.sh` - runs both server and watchdog

**Usage:**
```bash
# Start with watchdog
./start-with-watchdog.sh

# Manual watchdog
python3 watchdog.py --url http://localhost:5001/heartbeat --timeout 60
```

**Files modified:**
- `nutrition_pad/polling.py` - added heartbeat tracking and endpoint
- `nutrition_pad/main.py` - added PID file support and heartbeat initialization
- `watchdog.py` - new watchdog monitor script
- `start-with-watchdog.sh` - new startup script

## Architecture
- **Backend**: Flask (Python)
- **Frontend**: Vanilla JavaScript with long polling
- **Data**: JSON log files in `logs/` directory
- **Config**: `foods.toml` for food database

## Key Files
- `nutrition_pad/main.py` - Main Flask app and routes
- `nutrition_pad/polling.py` - Long polling and real-time sync
- `nutrition_pad/data.py` - Data access layer
- `foods.toml` - Food database configuration

## Development Workflow
- Use worktrees for parallel development: `git worktree add worktrees/<branch-name>`
- Test server: `python3 -m nutrition_pad.main --host 0.0.0.0 --port 5001`
- Logs location: `/tmp/nutrition-pad.log`
- PID file: `/tmp/nutrition-pad.pid`

## Common Tasks
- Edit food database: `/edit-foods` route or edit `foods.toml` directly
- View logs: Check `.logs/` directory for daily JSON files
- Debug polling: Use `--js-debug` flag for client-side debug output
