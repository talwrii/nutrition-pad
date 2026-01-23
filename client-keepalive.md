# Client-Side Keepalive System

## Overview
The tablet browser sometimes freezes or gets stuck. This system has **multiple layers** to detect problems and automatically refresh the page.

## How It Works - Multiple Defenses

### 1. XHR Timeout (45 seconds)
If a single poll request hangs, **refresh the page**:
```javascript
xhr.timeout = 45000; // 45 seconds
xhr.ontimeout = function() {
    debug('Poll timeout - XHR hung for 45s, refreshing page');
    window.location.reload();
};
```
**Catches:** Hung network requests that never complete
**Action:** Immediate page refresh

### 2. XHR Error Handler
Network errors trigger **immediate page refresh**:
```javascript
xhr.onerror = function() {
    debug('Poll error - network issue, refreshing page');
    window.location.reload();
};
```
**Catches:** Network failures, connection drops
**Action:** Immediate page refresh

### 3. Response Tracking
Every time ANY response comes back (success or error):
```javascript
lastPollResponse = Date.now();
```
**Tracks:** When we last heard from the server

### 4. Keepalive Checker (runs every 10 seconds)
Checks if too much time has passed without a response:
```javascript
function checkKeepalive() {
    var timeSinceLastPoll = Date.now() - lastPollResponse;
    if (timeSinceLastPoll > KEEPALIVE_TIMEOUT) {
        window.location.reload(); // Force page refresh
    }
}
```
**Catches:** Polling completely stopped (all other defenses failed)
**Action:** Page refresh after 60s of silence

### 5. Server Stuck Detection
Server includes `time.time()` timestamp in EVERY response. We check if **server's timestamp is advancing**:
```javascript
// Compare current server timestamp to PREVIOUS server timestamp
// (NOT comparing server time to client time!)
if (data.server_timestamp === lastServerTimestamp) {
    stuckServerCount++;
    if (stuckServerCount >= MAX_STUCK_RESPONSES) {
        window.location.reload(); // Server is stuck!
    }
} else {
    // Timestamp changed - server is alive
    lastServerTimestamp = data.server_timestamp;
    stuckServerCount = 0;
}
```
**Catches:** Server returning stale/cached responses (server process frozen)
**Action:** Page refresh after 3 identical timestamps
**Why:** If server sends the **exact same timestamp** 3 times in a row (~6 seconds), its clock stopped → server is frozen
**Note:** We only check if server timestamp **changes**, not comparing it to client time (avoids clock skew issues)

## Configuration
```javascript
var KEEPALIVE_TIMEOUT = 60000;  // 60 seconds - max time between poll responses
xhr.timeout = 45000;             // 45 seconds - max time for single XHR
checkKeepalive interval = 10000; // 10 seconds - how often to check
```

## Why This Multi-Layer Approach?
1. **XHR timeout**: Catches hung individual requests quickly (45s)
2. **Error handler**: Catches network failures
3. **Keepalive checker**: Final safety net if ALL polling stops (60s)
4. **Guaranteed restart**: Polling always restarts after timeout/error

## Files Modified
- `nutrition_pad/polling.py`:
  - Added `lastPollResponse` tracking
  - Added `KEEPALIVE_TIMEOUT` constant
  - Added `checkKeepalive()` function
  - Modified `poll()` to update `lastPollResponse`
  - Modified `startLongPolling()` to start keepalive checker

- `nutrition_pad/main.py`:
  - Removed `startHeartbeat()` call (not needed)

## What Happens When Tablet Freezes
1. User is viewing the page
2. Browser/JavaScript freezes
3. Polling stops (no XHR responses)
4. `checkKeepalive()` still runs (if browser is semi-responsive)
5. Detects 60+ seconds without poll response
6. Calls `window.location.reload()`
7. Page refreshes, tablet is unstuck

## Notes
- `watchdog.py` and `start-with-watchdog.sh` exist but are NOT used
- They were for a server-side watchdog approach (not what we want)
- Current approach is purely client-side JavaScript
