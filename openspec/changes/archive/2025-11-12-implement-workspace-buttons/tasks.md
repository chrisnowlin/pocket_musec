## 1. Session Retry Functionality

- [ ] 1.1 Add `retrySession` method to `useSession` hook that re-initializes the session
- [ ] 1.2 Add click handler to Retry button in `RightPanel.tsx`
- [ ] 1.3 Add loading state during retry attempt
- [ ] 1.4 Display success/error feedback after retry
- [ ] 1.5 Test retry functionality with simulated session errors

## 2. Conversation History Loading

- [ ] 2.1 Add `loadSessions` method to `useSession` hook to fetch all user sessions
- [ ] 2.2 Update Sidebar to load sessions list on mount
- [ ] 2.3 Add click handler to conversation history buttons in Sidebar
- [ ] 2.4 Implement `loadConversation` function to restore session state
- [ ] 2.5 Load and display conversation messages when session is restored
- [ ] 2.6 Update active state styling for selected conversation
- [ ] 2.7 Add loading state while loading conversation
- [ ] 2.8 Test conversation history loading with multiple sessions

## 3. Drafts Management

- [ ] 3.1 Create `DraftsModal.tsx` component with list view of drafts
- [ ] 3.2 Create `useDrafts.ts` hook for draft operations (list, open, delete)
- [ ] 3.3 Add `is_draft` flag to lessons table migration (if not exists)
- [ ] 3.4 Add API endpoint `GET /api/drafts` to list user drafts
- [ ] 3.5 Add API endpoint `GET /api/drafts/{id}` to get draft details
- [ ] 3.6 Add API endpoint `DELETE /api/drafts/{id}` to delete drafts
- [ ] 3.7 Add click handler to Saved Drafts button in Sidebar
- [ ] 3.8 Implement draft opening (loads draft into lesson editor)
- [ ] 3.9 Update draft count in button hint dynamically
- [ ] 3.10 Test draft creation, listing, opening, and deletion

## 4. Templates Management

- [ ] 4.1 Create `TemplatesModal.tsx` component with list view of templates
- [ ] 4.2 Create `useTemplates.ts` hook for template operations (list, create, select)
- [ ] 4.3 Implement template storage in localStorage (v1 approach)
- [ ] 4.4 Add "Save as Template" functionality from lesson view
- [ ] 4.5 Add click handler to Templates button in Sidebar
- [ ] 4.6 Implement template selection to pre-populate lesson structure
- [ ] 4.7 Add template metadata (name, description, grade, strand)
- [ ] 4.8 Test template creation, listing, and selection

## 5. Integration & Testing

- [ ] 5.1 Update UnifiedPage to manage templates/drafts modal state
- [ ] 5.2 Add error handling for all new operations
- [ ] 5.3 Add loading states for all async operations
- [ ] 5.4 Write unit tests for new hooks (useTemplates, useDrafts)
- [ ] 5.5 Write integration tests for button click handlers
- [ ] 5.6 Test all buttons work correctly in different UI states
- [ ] 5.7 Verify no regressions in existing functionality
- [ ] 5.8 Update FRONTEND_BUTTON_TEST_REPORT.md with completion status

## 6. Documentation

- [ ] 6.1 Update component documentation for new modals
- [ ] 6.2 Add JSDoc comments to new hooks
- [ ] 6.3 Update user guide with templates and drafts features
- [ ] 6.4 Document API endpoints (if backend changes made)

