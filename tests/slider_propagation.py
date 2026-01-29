#!/usr/bin/env python3
"""
Test that slider changes on the amounts page propagate to other browser sessions.

Usage:
    python test_slider_propagation.py http://localhost:5001
    python test_slider_propagation.py  # defaults to http://127.0.0.1:5001

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
    count = await slider.count()
    print(f"   DEBUG: slider count = {count}")
    if count > 0:
        value = await slider.input_value()
        print(f"   DEBUG: slider.input_value() = {value}")
        return int(value)
    return None


async def set_slider_value(page, value):
    """Set the slider to a specific value."""
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
    """Main test: verify slider changes propagate between two pages."""
    print(f"\n🧪 Testing slider propagation")
    print(f"   Server: {BASE_URL}")
    print(f"   Screenshots: {SCREENSHOT_DIR.absolute()}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Create two separate browser contexts (like two different tablets)
        context1 = await browser.new_context()
        context2 = await browser.new_context()
        
        page1 = await context1.new_page()
        page2 = await context2.new_page()
        
        try:
            # === Step 1: Navigate pages ===
            print("1️⃣  Opening amounts page and proteins page...")
            
            await page1.goto(f"{BASE_URL}/?pad=amounts")
            await page2.goto(f"{BASE_URL}/?pad=proteins")
            
            await page1.wait_for_load_state("networkidle")
            await page2.wait_for_load_state("networkidle")

            # Wait for slider to appear on amounts page
            print("   DEBUG: Waiting for slider element...")
            try:
                await page1.wait_for_selector("input[type='range']", timeout=5000, state="visible")
                print("   DEBUG: wait_for_selector succeeded")
                # Add small delay to ensure JS has finished
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"   ⚠️  Warning: Slider didn't appear within 5s: {e}")

            # Check the actual URL
            url = page1.url
            print(f"   DEBUG: page1 URL = {url}")

            await screenshot(page1, "01_amounts_initial")
            await screenshot(page2, "02_proteins_initial")

            # === Step 2: Get initial values ===
            print("\n2️⃣  Reading initial values...")

            initial_slider1 = await get_slider_value(page1)
            initial_display2 = await get_displayed_amount(page2)
            
            print(f"   Amounts page slider: {initial_slider1}g")
            print(f"   Proteins page display: {initial_display2}g")
            
            if initial_slider1 is None:
                print("   ❌ ERROR: Could not find slider on amounts page!")
                await screenshot(page1, "ERROR_no_slider")
                return False
            
            if initial_display2 is None:
                print("   ❌ ERROR: Could not find amount display on proteins page!")
                await screenshot(page2, "ERROR_no_display")
                return False
            
            # === Step 3: Change the slider on amounts page ===
            print("\n3️⃣  Moving slider on amounts page...")
            
            new_value = 150 if initial_slider1 != 150 else 200
            print(f"   Setting slider: {initial_slider1}g → {new_value}g")
            
            await set_slider_value(page1, new_value)
            await screenshot(page1, "03_amounts_after_slide")
            
            after_slide = await get_slider_value(page1)
            print(f"   Amounts page slider now shows: {after_slide}g")
            
            # === Step 4: Wait for propagation to proteins page ===
            print("\n4️⃣  Waiting for propagation to proteins page...")
            
            propagated = await wait_for_amount_change(page2, new_value)
            
            await screenshot(page2, "04_proteins_after_propagation")
            
            # === Step 5: Check result ===
            final_display2 = await get_displayed_amount(page2)
            print(f"   Proteins page now shows: {final_display2}g")
            
            if propagated and final_display2 == new_value:
                print("\n✅ SUCCESS: Slider change propagated correctly!")
                return True
            else:
                print(f"\n❌ FAILURE: Expected {new_value}g, got {final_display2}g")
                print(f"   Propagation detected: {propagated}")
                
                await screenshot(page1, "FAIL_amounts_final")
                await screenshot(page2, "FAIL_proteins_final")
                
                return False
                
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            await screenshot(page1, "ERROR_amounts")
            await screenshot(page2, "ERROR_proteins")
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
        
        page1 = await context1.new_page()
        page2 = await context2.new_page()
        
        try:
            await page1.goto(f"{BASE_URL}/?pad=amounts")
            await page2.goto(f"{BASE_URL}/?pad=proteins")
            await page1.wait_for_load_state("networkidle")
            await page2.wait_for_load_state("networkidle")
            
            test_values = [50, 100, 150, 200, 75]
            results = []
            
            for i, value in enumerate(test_values):
                print(f"\n   Test {i+1}/{len(test_values)}: Setting to {value}g")
                await set_slider_value(page1, value)
                
                propagated = await wait_for_amount_change(page2, value)
                actual = await get_displayed_amount(page2)
                
                status = "✓" if propagated else "✗"
                print(f"   {status} Expected {value}g, got {actual}g")
                results.append(propagated)
                
                await screenshot(page2, f"multi_{i+1}_{value}g")
            
            passed = sum(results)
            print(f"\n   Results: {passed}/{len(test_values)} passed")
            return all(results)
            
        finally:
            await browser.close()


if __name__ == "__main__":
    print("=" * 60)
    print("NUTRITION-PAD SLIDER PROPAGATION TEST")
    print("=" * 60)
    
    result1 = asyncio.run(test_slider_propagation())
    
    if result1:
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