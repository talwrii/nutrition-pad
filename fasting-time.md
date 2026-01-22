# Fasting Time Display

## Issue
When unknowns are resolved, the "Since Last Ate" display doesn't update immediately.

## Expected Behavior
- Resolving unknowns should trigger an update to the fasting time display
- Recording new food entries should update the fasting time display
- The display should refresh automatically when food logs are modified

## Current Implementation (VERIFIED)
✅ `/api/resolve-unknown` calls `mark_updated("resolve_unknown")` (main.py:1691)
✅ `/log` calls `mark_updated(nonce)` (main.py:1272)
✅ Nutrition dashboard polls `/poll-updates` every 30 seconds (main.py:657)
✅ Page reloads when update detected with 1 second delay (main.py:650-652)

## Possible Issues
- **Polling interval too long**: 30 seconds between checks
- **Reload delay**: 1 second delay before reload
- **User doesn't notice**: Page reloads but user doesn't see the change

## Solutions to Consider
- [ ] Reduce polling interval from 30s to 5s or 10s
- [ ] Remove the 1 second delay before reload
- [ ] Add visual feedback when update is detected ("Refreshing...")
- [ ] Make the "Since Last Ate" update in-place without full page reload
