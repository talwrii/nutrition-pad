#!/usr/bin/env python3
"""
Test that slider changes on the amounts page propagate to other pages.

Usage:
    # With server already running:
    python test_slider_propagation.py http://localhost:5001
    
    # Or it will default to http://127.0.0.1:5001
    python test_slider_propagation.py

Requirements:
    pip install playwright
    playwright install chromium
"""

import sys
import time
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

# Configuration
BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5001"
SCREENSHOT_DIR = Path("screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

# Timeouts
PROPAGATION_TIMEOUT = 5000  # ms to wait for propagation
POLL_INTERVAL = 200  # ms between checks


async def screenshot(page, name):
    """Take a screenshot with timestamp."""
    path = SCREENSHOT_DIR / f"{name}.png"
    await page.screenshot(path=str(path))
    print(f"  📸 Screenshot: {path}")


async def get_displayed_amount(page):
    """Extract the current amount displayed on the page (e.g., '100g' -> 100)."""
    # Try different selectors that might contain the amount
    selectors = [
        ".current-amount",
        "#amount-display",
        ".amount-display",
    ]
    
    for selector in selectors:
        try:
            element = page.locator(selector).first
            if await element.count() > 0:
                text = await element.text_content()
                if text:
                    # Extract number from text like "100g" or "100.0g"
                    import re
                    match = re.search(r'([\d.]+)', text)
                    if match:
                        return int(float(match.group(1)))
        except Exception:
            continue
    
    return None


async def get_slider_value(page):
    """Get the current slider value."""
    slider = page.locator("input[type='range']").first
    if await slider.count() > 0:
        return int(await slider.input_value())
    return None


async def set_slider_value(page, value):
    """Set the slider to a specific value."""
    # Method 1: Direct value setting via JavaScript
    await page.evaluate(f"""
        const slider = document.querySelector("input[type='range']");
        if (slider) {{
            slider.value = {value};
            slider.dispatchEvent(new Event('input', {{ bubbles: true }}));
            slider.dispatchEvent(new Event('change', {{ bubbles: true }}));
        }}
    """)


async def wait_for_amount_change(page, expected_amount, timeout_ms=PROPAGATION_TIMEOUT):
    """Wait for the displayed amount to change to expected value."""
    start = time.time()
    timeout_sec = timeout_ms / 1000
    
    while (time.time() - start) < timeout_sec:
        current = await get_displayed_amount(page)
        if current == expected_amount:
            return True
        await asyncio.sleep(POLL_INTERVAL / 1000)
    
    return False


async def test_slider_propagation():
    """Main test: verify slider changes propagate between pages."""
    print(f"\n🧪 Testing slider propagation")
    print(f"   Server: {BASE_URL}")
    print(f"   Screenshots: {SCREENSHOT_DIR.absolute()}\n")
    
    async with async_playwright() as p:
        # Launch browser (use chromium, could also test on webkit for old Android)
        browser = await p.chromium.launch(headless=True)
        
        # Create two separate browser contexts (like two different tablets)
        context1 = await browser.new_context()
        context2 = await browser.new_context()
        
        page_amounts = await context1.new_page()
        page_food = await context2.new_page()
        
        try:
            # === Step 1: Navigate both pages ===
            print("1️⃣  Opening pages...")
            
            # Amounts page
            await page_amounts.goto(f"{BASE_URL}/?pad=amounts")
            # Food page - use root URL, will redirect to first configured pad
            await page_food.goto(f"{BASE_URL}/")
            
            # Wait for pages to load
            await page_amounts.wait_for_load_state("networkidle")
            await page_food.wait_for_load_state("networkidle")
            
            await screenshot(page_amounts, "01_amounts_initial")
            await screenshot(page_food, "02_food_initial")
            
            # === Step 2: Get initial values ===
            print("\n2️⃣  Reading initial values...")
            
            initial_slider = await get_slider_value(page_amounts)
            initial_food_display = await get_displayed_amount(page_food)
            
            print(f"   Amounts page slider: {initial_slider}g")
            print(f"   Food page display: {initial_food_display}g")
            
            # === Step 3: Change the slider ===
            print("\n3️⃣  Moving slider...")
            
            # Pick a new value that's different from current
            if initial_slider is None:
                print("   ❌ ERROR: Could not find slider on amounts page!")
                await screenshot(page_amounts, "ERROR_no_slider")
                return False
            
            # Move to a distinctly different value
            new_value = 150 if initial_slider != 150 else 200
            print(f"   Setting slider: {initial_slider}g → {new_value}g")
            
            await set_slider_value(page_amounts, new_value)
            await screenshot(page_amounts, "03_amounts_after_slide")
            
            # Verify slider actually changed on amounts page
            after_slide = await get_slider_value(page_amounts)
            print(f"   Slider now shows: {after_slide}g")
            
            # === Step 4: Wait for propagation ===
            print("\n4️⃣  Waiting for propagation to food page...")
            
            propagated = await wait_for_amount_change(page_food, new_value)
            
            await screenshot(page_food, "04_food_after_propagation")
            
            # === Step 5: Check result ===
            final_food_display = await get_displayed_amount(page_food)
            print(f"   Food page now shows: {final_food_display}g")
            
            if propagated and final_food_display == new_value:
                print("\n✅ SUCCESS: Slider change propagated correctly!")
                return True
            else:
                print(f"\n❌ FAILURE: Expected {new_value}g, got {final_food_display}g")
                print(f"   Propagation detected: {propagated}")
                
                # Extra debugging screenshots
                await screenshot(page_amounts, "FAIL_amounts_final")
                await screenshot(page_food, "FAIL_food_final")
                
                # Check if there's any network activity
                print("\n   Debugging info:")
                print(f"   - Check if long-polling endpoint exists")
                print(f"   - Check browser console for errors")
                
                return False
                
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            await screenshot(page_amounts, "ERROR_amounts")
            await screenshot(page_food, "ERROR_food")
            raise
            
        finally:
            await browser.close()


async def test_slider_multiple_values():
    """Test multiple slider movements propagate correctly."""
    print(f"\n🧪 Testing multiple slider changes")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context1 = await browser.new_context()
        context2 = await browser.new_context()
        
        page_amounts = await context1.new_page()
        page_food = await context2.new_page()
        
        try:
            await page_amounts.goto(f"{BASE_URL}/?pad=amounts")
            await page_food.goto(f"{BASE_URL}/")
            await page_amounts.wait_for_load_state("networkidle")
            await page_food.wait_for_load_state("networkidle")
            
            test_values = [50, 100, 150, 200, 75]
            results = []
            
            for i, value in enumerate(test_values):
                print(f"\n   Test {i+1}/{len(test_values)}: Setting to {value}g")
                await set_slider_value(page_amounts, value)
                
                # Wait a bit for propagation
                propagated = await wait_for_amount_change(page_food, value)
                actual = await get_displayed_amount(page_food)
                
                status = "✓" if propagated else "✗"
                print(f"   {status} Expected {value}g, got {actual}g")
                results.append(propagated)
                
                await screenshot(page_food, f"multi_{i+1}_{value}g")
            
            passed = sum(results)
            print(f"\n   Results: {passed}/{len(test_values)} passed")
            return all(results)
            
        finally:
            await browser.close()


if __name__ == "__main__":
    print("=" * 60)
    print("NUTRITION-PAD SLIDER PROPAGATION TEST")
    print("=" * 60)
    
    # Run basic propagation test
    result1 = asyncio.run(test_slider_propagation())
    
    if result1:
        # If basic test passes, run multiple values test
        result2 = asyncio.run(test_slider_multiple_values())
    else:
        result2 = False
    
    print("\n" + "=" * 60)
    if result1 and result2:
        print("ALL TESTS PASSED ✅")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED ❌")
        sys.exit(1)