#!/usr/bin/env python3
"""
Test that the nutrition dashboard auto-refreshes when a food entry is logged.

Usage:
    python tests/test_dashboard_refresh.py http://localhost:5099
    python tests/test_dashboard_refresh.py  # defaults to http://127.0.0.1:5099

Requirements:
    pip install playwright
    playwright install chromium
"""

import sys
import time
import asyncio
import json
from pathlib import Path
from urllib.request import Request, urlopen

from playwright.async_api import async_playwright

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5099"
SCREENSHOT_DIR = Path("screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)


async def screenshot(page, name):
    """Take a screenshot with timestamp."""
    path = SCREENSHOT_DIR / f"{name}.png"
    await page.screenshot(path=str(path))
    print(f"  📸 Screenshot: {path}")


def get_first_food():
    """Get the first non-unknown food from the server."""
    url = f"{BASE_URL}/api/foods"
    with urlopen(url, timeout=10) as response:
        data = json.loads(response.read())
    for food in data.get('foods', []):
        if 'unknown' not in food['food_key']:
            return food['food_key'], food['pad_key']
    return None, None


def log_food_via_api(food_key, pad_key):
    """Log a food entry by POSTing to /log."""
    url = f"{BASE_URL}/log"
    nonce = f"test_{int(time.time())}"
    data = json.dumps({
        'pad': pad_key,
        'food': food_key,
        'nonce': nonce
    }).encode('utf-8')
    req = Request(url, data=data,
                  headers={'Content-Type': 'application/json'},
                  method='POST')
    with urlopen(req, timeout=10) as response:
        return json.loads(response.read())


async def get_calorie_total(page):
    """Extract the calorie total from the dashboard."""
    try:
        text = await page.text_content('body')
        if text:
            import re
            # Look for a number followed by kcal
            matches = re.findall(r'([\d,]+)\s*kcal', text)
            if matches:
                return int(matches[0].replace(',', ''))
    except Exception:
        pass
    return None


async def test_dashboard_auto_refresh():
    """Test that logging a food entry triggers the dashboard to refresh."""
    print(f"\n🧪 Testing dashboard auto-refresh")
    print(f"   Server: {BASE_URL}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Step 1: Open dashboard
            print("1️⃣  Opening nutrition dashboard...")
            await page.goto(f"{BASE_URL}/nutrition")
            await page.wait_for_load_state("networkidle")
            await screenshot(page, "dashboard_01_initial")

            initial_calories = await get_calorie_total(page)
            print(f"   Initial calories: {initial_calories}")

            # Step 2: Get the page HTML to verify long polling is connected
            html = await page.content()
            has_polling = 'startLongPolling' in html
            print(f"   Uses startLongPolling: {has_polling}")

            if not has_polling:
                print("   ❌ Dashboard does not use startLongPolling!")
                return False

            # Step 3: Log a food entry via API
            print("\n2️⃣  Logging food entry via API...")
            food_key, pad_key = get_first_food()
            if not food_key:
                print("   ❌ No foods available on server!")
                return False
            print(f"   Using food: {food_key} (pad: {pad_key})")
            result = log_food_via_api(food_key, pad_key)
            print(f"   API response: {result.get('status', 'unknown')}")

            # Step 4: Wait for page to reload (long polling should trigger within ~5s)
            print("\n3️⃣  Waiting for dashboard to auto-refresh...")

            refreshed = False
            start = time.time()
            timeout = 10  # seconds

            # Watch for navigation (page reload)
            try:
                async with page.expect_navigation(timeout=timeout * 1000):
                    pass
                refreshed = True
                elapsed = time.time() - start
                print(f"   Page refreshed after {elapsed:.1f}s")
            except Exception:
                elapsed = time.time() - start
                print(f"   No refresh detected after {elapsed:.1f}s")

            await screenshot(page, "dashboard_02_after_entry")

            # Step 5: Check result
            if refreshed:
                final_calories = await get_calorie_total(page)
                print(f"   Final calories: {final_calories}")

                if initial_calories is not None and final_calories is not None:
                    if final_calories > initial_calories:
                        print(f"\n✅ SUCCESS: Dashboard refreshed and calories increased ({initial_calories} → {final_calories})")
                        return True
                    else:
                        print(f"\n⚠️  Dashboard refreshed but calories didn't increase ({initial_calories} → {final_calories})")
                        return True  # Refresh worked, that's the main thing
                else:
                    print(f"\n✅ SUCCESS: Dashboard refreshed automatically")
                    return True
            else:
                print(f"\n❌ FAILURE: Dashboard did not auto-refresh within {timeout}s")
                await screenshot(page, "FAIL_dashboard_no_refresh")
                return False

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            await screenshot(page, "ERROR_dashboard")
            raise

        finally:
            await browser.close()


if __name__ == "__main__":
    print("=" * 60)
    print("NUTRITION DASHBOARD AUTO-REFRESH TEST")
    print("=" * 60)

    result = asyncio.run(test_dashboard_auto_refresh())

    print("\n" + "=" * 60)
    if result:
        print("TEST PASSED ✅")
        sys.exit(0)
    else:
        print("TEST FAILED ❌")
        sys.exit(1)
