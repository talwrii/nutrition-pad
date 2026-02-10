#!/usr/bin/env python3
"""
Test that meal mode syncs across browser sessions via server.

When meal mode is activated on one tablet, clicking foods on another tablet
should add them to the meal instead of logging directly.

Usage:
    python test_meal_mode_sync.py http://localhost:5001
    python test_meal_mode_sync.py  # defaults to http://127.0.0.1:5099
"""

import sys
import time
import asyncio
from pathlib import Path

import aiohttp
from playwright.async_api import async_playwright

# Configuration
BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5099"
SCREENSHOT_DIR = Path("screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

# Timeouts
SYNC_TIMEOUT = 15000  # ms to wait for meal mode sync
POLL_INTERVAL = 200  # ms between checks


async def screenshot(page, name):
    """Take a screenshot with timestamp."""
    path = SCREENSHOT_DIR / f"{name}.png"
    await page.screenshot(path=str(path))
    print(f"  📸 Screenshot: {path}")


async def wait_for_meal_mode_indicator(page, timeout_ms=SYNC_TIMEOUT):
    """Wait for the meal mode indicator to appear."""
    start = time.time()
    timeout_sec = timeout_ms / 1000

    while (time.time() - start) < timeout_sec:
        # Check if indicator is visible
        visible = await page.evaluate("""(() => {
            var ind = document.getElementById('meal-mode-indicator');
            return ind && ind.style.display !== 'none' && ind.offsetParent !== null;
        })()""")
        if visible:
            return True
        await asyncio.sleep(POLL_INTERVAL / 1000)

    return False


async def get_item_count(page):
    """Get number of items logged today from the page."""
    try:
        el = page.locator(".item-count").first
        if await el.count() > 0:
            text = await el.text_content()
            if text:
                import re
                match = re.search(r'(\d+)', text)
                if match:
                    return int(match.group(1))
    except Exception:
        pass
    return None


async def get_meal_items_count_from_server(base_url):
    """Get number of items in the current meal from server."""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{base_url}/get-meal-items") as resp:
            if resp.status == 200:
                data = await resp.json()
                return len(data.get('meal_items', []))
    return 0


async def test_meal_mode_sync():
    """Test that meal mode syncs and intercepts food clicks on other sessions."""
    print(f"\n🧪 Testing meal mode sync across sessions")
    print(f"   Server: {BASE_URL}")
    print(f"   Screenshots: {SCREENSHOT_DIR.absolute()}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Two separate browser contexts (like two tablets)
        context1 = await browser.new_context()
        context2 = await browser.new_context()

        page1 = await context1.new_page()
        page2 = await context2.new_page()

        try:
            # === Step 1: Open food pads on page2 first (before meal mode) ===
            print("1️⃣  Opening food pads on tablet 2...")
            await page2.goto(f"{BASE_URL}/?pad=proteins")
            await page2.wait_for_load_state("networkidle")
            await screenshot(page2, "meal_sync_01_foodpads_initial")

            initial_count = await get_item_count(page2)
            print(f"   Initial item count: {initial_count}")

            # === Step 2: Enter meal mode on page1 ===
            print("\n2️⃣  Entering meal mode on tablet 1...")
            await page1.goto(f"{BASE_URL}/meals/build")
            await page1.wait_for_load_state("networkidle")
            await screenshot(page1, "meal_sync_02_mealsbuild")
            print("   Meal build page loaded")

            # === Step 3: Wait for meal mode to sync to page2 ===
            print("\n3️⃣  Waiting for meal mode to sync to tablet 2...")

            synced = await wait_for_meal_mode_indicator(page2)
            await screenshot(page2, "meal_sync_03_foodpads_synced")

            if not synced:
                print("   ❌ FAILED: Meal mode indicator didn't appear within timeout")
                return False
            print("   ✓ Meal mode indicator visible (synced from server)")

            # === Step 4: Click a food on page2 ===
            print("\n4️⃣  Clicking food on tablet 2...")

            # Find first food button
            food_btn = page2.locator(".food-btn").first
            if await food_btn.count() == 0:
                print("   ❌ FAILED: No food buttons found")
                return False

            food_name = await food_btn.text_content()
            print(f"   Clicking: {food_name.strip()}")
            await food_btn.click()

            # Small delay for XHR
            await asyncio.sleep(0.5)
            await screenshot(page2, "meal_sync_04_after_click")

            # === Step 5: Verify food was added to meal, not logged ===
            print("\n5️⃣  Verifying food was added to meal (not logged)...")

            # Check item count didn't increase (food wasn't logged)
            final_count = await get_item_count(page2)
            print(f"   Item count after click: {final_count}")

            if final_count is not None and initial_count is not None:
                if final_count > initial_count:
                    print(f"   ❌ FAILED: Item count increased from {initial_count} to {final_count}")
                    print("   Food was logged instead of added to meal!")
                    return False
                print(f"   ✓ Item count unchanged ({initial_count} → {final_count})")

            # Check meal items on server (shared across all clients)
            meal_items = await get_meal_items_count_from_server(BASE_URL)
            print(f"   Meal items on server: {meal_items}")

            if meal_items > 0:
                print(f"   ✓ Food added to meal on server ({meal_items} item(s))")
            else:
                print("   ❌ FAILED: No meal items on server after click")
                return False

            # === Step 6: Cancel meal mode and verify sync ===
            print("\n6️⃣  Cancelling meal mode...")
            cancel_btn = page1.locator("button", has_text="Cancel")
            if await cancel_btn.count() > 0:
                await cancel_btn.click()
                await asyncio.sleep(1)

                # Check page2 reverts to normal background
                bg_after = await page2.evaluate("window.getComputedStyle(document.body).background")
                if '163e3e' not in bg_after and '0f4660' not in bg_after:
                    print("   ✓ Tablet 2 reverted to normal background")
                else:
                    print("   ⚠️  Tablet 2 still has meal mode background")

            await screenshot(page2, "meal_sync_05_after_cancel")

            print("\n✅ SUCCESS: Meal mode syncs across sessions!")
            return True

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            await context1.close()
            await context2.close()
            await browser.close()


async def main():
    success = await test_meal_mode_sync()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
