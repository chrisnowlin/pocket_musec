# Conversation Menu Test Checklist

## Prerequisites
- Frontend running on http://localhost:5173
- Backend running on http://localhost:8000
- At least one conversation exists in the sidebar

## Test Steps

### 1. Test Three-Dot Menu Visibility
- [ ] Navigate to http://localhost:5173
- [ ] Verify "Recent Chats" section is visible
- [ ] Hover over a conversation button
- [ ] Verify three-dot menu button appears (opacity transition)
- [ ] Verify menu button is clickable

### 2. Test Menu Dropdown
- [ ] Click the three-dot menu button
- [ ] Verify dropdown menu appears
- [ ] Verify "Open Editor" option is visible
- [ ] Verify "Delete Conversation" option is visible
- [ ] Verify menu styling matches sidebar design

### 3. Test "Open Editor" Action
- [ ] Click "Open Editor" from the menu
- [ ] If conversation has lesson content:
  - [ ] Verify LessonEditor modal opens
  - [ ] Verify lesson content is displayed
  - [ ] Verify save and cancel buttons work
- [ ] If conversation has no lesson content:
  - [ ] Verify info toast notification appears (top-right)
  - [ ] Verify toast auto-dismisses after 5 seconds
  - [ ] Verify toast can be manually closed

### 4. Test "Delete Conversation" Action
- [ ] Click "Delete Conversation" from the menu
- [ ] Verify confirmation dialog appears (not browser alert)
- [ ] Verify dialog shows "Delete Conversation" title
- [ ] Verify dialog shows warning message
- [ ] Verify "Cancel" button works
- [ ] Verify "Delete" button is styled as danger variant
- [ ] Click "Delete" button
- [ ] Verify success toast notification appears
- [ ] Verify conversation is removed from sidebar
- [ ] Verify sessions list refreshes automatically

### 5. Test Toast Notifications
- [ ] Trigger an action that shows an error (e.g., delete non-existent conversation)
- [ ] Verify error toast appears with red styling
- [ ] Verify toast has close button
- [ ] Click close button
- [ ] Verify toast disappears immediately

### 6. Verify No Blocking Alerts
- [ ] Perform various actions
- [ ] Verify no browser alert() dialogs appear
- [ ] Verify all notifications are non-blocking toasts

## Expected Results

✅ All menu actions work correctly
✅ Toast notifications replace all alert() calls
✅ Confirmation dialog replaces confirm() calls
✅ No blocking dialogs interrupt user workflow
✅ Menu appears on hover and is properly styled

