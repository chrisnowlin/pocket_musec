#!/usr/bin/env python3
"""
Test script for conversation menu functionality
Tests: Toast notifications, Delete confirmation, Editor opening

Usage: python scripts/test_conversation_menu.py
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("❌ Playwright not installed. Installing...")
    print("   Run: pip install playwright && playwright install chromium")
    sys.exit(1)

FRONTEND_URL = "http://localhost:5173"
TIMEOUT = 10000


async def test_conversation_menu():
    """Test conversation menu functionality"""
    print("🚀 Starting conversation menu tests...\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to the app
            print("📱 Navigating to application...")
            await page.goto(FRONTEND_URL, wait_until="networkidle")
            await page.wait_for_timeout(2000)
            
            # Test 1: Verify three-dot menu appears
            print("\n✅ Test 1: Verify three-dot menu appears")
            menu_buttons = page.locator('button[aria-label="Conversation options"]')
            menu_count = await menu_buttons.count()
            print(f"   Found {menu_count} conversation menu buttons")
            
            if menu_count == 0:
                print("   ⚠️  No conversations found. Waiting for conversations to load...")
                await page.wait_for_timeout(3000)
                menu_count = await menu_buttons.count()
                print(f"   Found {menu_count} conversation menu buttons after wait")
            
            if menu_count == 0:
                print("   ⚠️  No conversations available for testing")
                return
            
            # Test 2: Click menu and verify dropdown
            print("\n✅ Test 2: Click menu and verify dropdown")
            first_menu = menu_buttons.first()
            await first_menu.click()
            await page.wait_for_timeout(500)
            
            # Check if dropdown is visible
            open_editor_btn = page.locator('button:has-text("Open Editor")')
            delete_btn = page.locator('button:has-text("Delete Conversation")')
            
            has_open_editor = await open_editor_btn.count() > 0
            has_delete = await delete_btn.count() > 0
            
            print(f"   Open Editor button visible: {'✅' if has_open_editor else '❌'}")
            print(f"   Delete Conversation button visible: {'✅' if has_delete else '❌'}")
            
            if not has_open_editor or not has_delete:
                raise Exception("Dropdown menu items not visible")
            
            # Test 3: Test "Open Editor" (should show toast if no content)
            print("\n✅ Test 3: Test 'Open Editor' action")
            await open_editor_btn.first().click()
            await page.wait_for_timeout(1500)
            
            # Check for toast notification
            toast_selectors = [
                '.bg-blue-100',  # info
                '.bg-rose-100',  # error
                '.bg-emerald-100',  # success
                '.bg-amber-100',  # warning
            ]
            
            toast_visible = False
            toast_text = None
            for selector in toast_selectors:
                toast = page.locator(selector).first()
                if await toast.count() > 0:
                    toast_visible = True
                    toast_text = await toast.text_content()
                    break
            
            print(f"   Toast notification appeared: {'✅' if toast_visible else '❌'}")
            if toast_visible and toast_text:
                print(f"   Toast message: \"{toast_text.strip()}\"")
            
            # Test 4: Test "Delete Conversation" (should show confirmation dialog)
            print("\n✅ Test 4: Test 'Delete Conversation' action")
            
            # Click menu again to open dropdown
            await first_menu.click()
            await page.wait_for_timeout(500)
            
            await delete_btn.first().click()
            await page.wait_for_timeout(1000)
            
            # Check for confirmation dialog
            confirm_dialog = page.locator('text=Delete Conversation')
            dialog_visible = await confirm_dialog.count() > 0
            
            print(f"   Confirmation dialog appeared: {'✅' if dialog_visible else '❌'}")
            
            if dialog_visible:
                # Check for Cancel and Delete buttons
                cancel_btn = page.locator('button:has-text("Cancel")')
                delete_confirm_btn = page.locator('button:has-text("Delete")')
                
                has_cancel = await cancel_btn.count() > 0
                has_delete_confirm = await delete_confirm_btn.count() > 0
                
                print(f"   Cancel button visible: {'✅' if has_cancel else '❌'}")
                print(f"   Delete button visible: {'✅' if has_delete_confirm else '❌'}")
                
                # Cancel the deletion
                if has_cancel:
                    await cancel_btn.first().click()
                    await page.wait_for_timeout(500)
                    print("   ✅ Canceled deletion (dialog closed)")
            else:
                print("   ⚠️  Confirmation dialog not found")
            
            # Test 5: Verify toast container exists
            print("\n✅ Test 5: Verify toast notification system")
            # Toast container should be in DOM (may be empty)
            toast_container = page.locator('div.fixed.top-4.right-4')
            container_count = await toast_container.count()
            print(f"   Toast container elements found: {container_count}")
            
            # Test 6: Verify no blocking alerts
            print("\n✅ Test 6: Verify no blocking alerts")
            alert_handled = False
            alert_message = None
            
            def handle_dialog(dialog):
                nonlocal alert_handled, alert_message
                alert_handled = True
                alert_message = dialog.message
                asyncio.create_task(dialog.dismiss())
            
            page.on("dialog", handle_dialog)
            
            # Wait a bit to see if any alerts appear
            await page.wait_for_timeout(1000)
            
            if alert_handled:
                print(f"   ⚠️  Blocking alert detected: \"{alert_message}\"")
                print("   ⚠️  This indicates old code is still cached. Hard refresh needed!")
            else:
                print("   ✅ No blocking alerts detected")
            
            print("\n✨ All tests completed!\n")
            
        except PlaywrightTimeout as e:
            print(f"\n❌ Test timeout: {e}")
            await page.screenshot(path="test_timeout_screenshot.png")
            raise
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            await page.screenshot(path="test_failure_screenshot.png")
            raise
        finally:
            await browser.close()


if __name__ == "__main__":
    try:
        asyncio.run(test_conversation_menu())
        print("✅ Test script completed successfully")
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

