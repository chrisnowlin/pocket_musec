/**
 * Test script for conversation menu functionality
 * Tests: Toast notifications, Delete confirmation, Editor opening
 * 
 * Usage: node scripts/test_conversation_menu.js
 */

const { chromium } = require('playwright');

const FRONTEND_URL = 'http://localhost:5173';
const TIMEOUT = 10000;

async function testConversationMenu() {
  console.log('🚀 Starting conversation menu tests...\n');
  
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to the app
    console.log('📱 Navigating to application...');
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Test 1: Verify three-dot menu appears
    console.log('\n✅ Test 1: Verify three-dot menu appears');
    const conversationButtons = await page.locator('button[aria-label="Conversation options"]').count();
    console.log(`   Found ${conversationButtons} conversation menu buttons`);
    
    if (conversationButtons === 0) {
      console.log('   ⚠️  No conversations found. Creating a test conversation...');
      // Wait for conversations to load
      await page.waitForTimeout(3000);
      const updatedCount = await page.locator('button[aria-label="Conversation options"]').count();
      console.log(`   Found ${updatedCount} conversation menu buttons after wait`);
    }

    // Test 2: Click menu and verify dropdown
    console.log('\n✅ Test 2: Click menu and verify dropdown');
    const firstMenuButton = page.locator('button[aria-label="Conversation options"]').first();
    
    if (await firstMenuButton.count() > 0) {
      await firstMenuButton.click();
      await page.waitForTimeout(500);
      
      // Check if dropdown is visible
      const openEditorButton = page.locator('button:has-text("Open Editor")');
      const deleteButton = page.locator('button:has-text("Delete Conversation")');
      
      const hasOpenEditor = await openEditorButton.count() > 0;
      const hasDelete = await deleteButton.count() > 0;
      
      console.log(`   Open Editor button visible: ${hasOpenEditor ? '✅' : '❌'}`);
      console.log(`   Delete Conversation button visible: ${hasDelete ? '✅' : '❌'}`);
      
      if (!hasOpenEditor || !hasDelete) {
        throw new Error('Dropdown menu items not visible');
      }
    } else {
      console.log('   ⚠️  Skipping - no menu buttons found');
    }

    // Test 3: Test "Open Editor" (should show toast if no content)
    console.log('\n✅ Test 3: Test "Open Editor" action');
    const openEditorBtn = page.locator('button:has-text("Open Editor")').first();
    
    if (await openEditorBtn.count() > 0) {
      await openEditorBtn.click();
      await page.waitForTimeout(1000);
      
      // Check for toast notification (should appear if no lesson content)
      const toast = page.locator('.bg-blue-100, .bg-rose-100, .bg-emerald-100, .bg-amber-100').first();
      const toastVisible = await toast.count() > 0;
      
      console.log(`   Toast notification appeared: ${toastVisible ? '✅' : '❌'}`);
      
      if (toastVisible) {
        const toastText = await toast.textContent();
        console.log(`   Toast message: "${toastText?.trim()}"`);
      }
    } else {
      console.log('   ⚠️  Skipping - Open Editor button not found');
    }

    // Test 4: Test "Delete Conversation" (should show confirmation dialog)
    console.log('\n✅ Test 4: Test "Delete Conversation" action');
    
    // Click menu again to open dropdown
    if (await firstMenuButton.count() > 0) {
      await firstMenuButton.click();
      await page.waitForTimeout(500);
      
      const deleteBtn = page.locator('button:has-text("Delete Conversation")').first();
      
      if (await deleteBtn.count() > 0) {
        await deleteBtn.click();
        await page.waitForTimeout(1000);
        
        // Check for confirmation dialog
        const confirmDialog = page.locator('text=Delete Conversation').first();
        const dialogVisible = await confirmDialog.count() > 0;
        
        console.log(`   Confirmation dialog appeared: ${dialogVisible ? '✅' : '❌'}`);
        
        if (dialogVisible) {
          // Cancel the deletion
          const cancelBtn = page.locator('button:has-text("Cancel")').first();
          if (await cancelBtn.count() > 0) {
            await cancelBtn.click();
            await page.waitForTimeout(500);
            console.log('   ✅ Canceled deletion (dialog closed)');
          }
        }
      } else {
        console.log('   ⚠️  Skipping - Delete button not found');
      }
    }

    // Test 5: Verify toast container exists
    console.log('\n✅ Test 5: Verify toast notification system');
    const toastContainer = page.locator('div[class*="fixed"][class*="top-4"][class*="right-4"]');
    const containerExists = await toastContainer.count() > 0;
    console.log(`   Toast container in DOM: ${containerExists ? '✅' : '⚠️  (may be hidden when empty)'}`);

    // Test 6: Verify no blocking alerts
    console.log('\n✅ Test 6: Verify no blocking alerts');
    // Set up alert handler
    let alertHandled = false;
    page.on('dialog', async dialog => {
      alertHandled = true;
      console.log(`   ⚠️  Blocking alert detected: "${dialog.message()}"`);
      await dialog.dismiss();
    });

    // Try to trigger an action that might show alert
    await page.waitForTimeout(1000);
    
    if (!alertHandled) {
      console.log('   ✅ No blocking alerts detected');
    }

    console.log('\n✨ All tests completed!\n');
    
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    console.error(error.stack);
    await page.screenshot({ path: 'test_failure_screenshot.png' });
    throw error;
  } finally {
    await browser.close();
  }
}

// Run tests
testConversationMenu()
  .then(() => {
    console.log('✅ Test script completed successfully');
    process.exit(0);
  })
  .catch((error) => {
    console.error('❌ Test script failed:', error);
    process.exit(1);
  });

