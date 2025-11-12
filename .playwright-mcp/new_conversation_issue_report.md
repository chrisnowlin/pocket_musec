# New Conversation Issue Report

**Date:** November 12, 2025  
**Tested By:** Chrome DevTools Testing  
**Issue:** Current selections data not populating initial message when starting new conversation

## Test Environment
- Frontend: http://localhost:5173/
- Backend: http://localhost:8000/
- Browser: Chrome DevTools MCP

## Issue Description

When clicking the "New Conversation" button in the Sidebar, a new session is created but only minimal data is sent to the backend. The current lesson settings and context from the right panel are not being included in the session creation request.

## Current Behavior

### Data Sent on New Conversation Click
```json
{
  "grade_level": "Grade 3",
  "strand_code": "Connect"
}
```

### API Response
```json
{
  "id": "ed80ce80-1538-43d7-8327-7ccbdb6495c2",
  "grade_level": "Grade 3",
  "strand_code": "Connect",
  "selected_standard": null,
  "additional_context": null,
  "conversation_history": null,
  "created_at": "2025-11-12T20:08:48.814002",
  "updated_at": "2025-11-12T20:08:48.814002"
}
```

### Data Available in UI (Not Sent)
- **Grade Level:** "Grade 3" ✓ (sent)
- **Strand:** "Connect" ✓ (sent)
- **Standard:** "" (empty, but should be sent if selected)
- **Objective:** "" (disabled until standard selected)
- **Additional Context:** "Class has recorders and a 30-minute block with mixed instruments." ✗ (NOT sent)
- **Lesson Duration:** "30 minutes" ✗ (NOT sent, not supported by backend)
- **Class Size:** "25" ✗ (NOT sent, not supported by backend)

## Root Cause

### Code Location
**File:** `/frontend/src/hooks/useSession.ts`  
**Function:** `initSession` (lines 59-86)

### Current Implementation
```typescript
const initSession = useCallback(
  async (defaultGrade: string = 'Grade 3', defaultStrand: string = 'Connect') => {
    try {
      const result = await api.createSession({
        grade_level: defaultGrade,
        strand_code: defaultStrand,
      });
      // ... rest of function
    }
  },
  [loadStandards]
);
```

### Called From
**File:** `/frontend/src/pages/UnifiedPage.tsx`  
**Function:** `handleNewConversation`

```typescript
const handleNewConversation = async () => {
  const newSession = await initSession(
    lessonSettings.selectedGrade,
    lessonSettings.selectedStrand
  );
  // ... rest of function
};
```

## Backend API Support

The backend API endpoint `POST /api/sessions` **does support** additional fields:

```python
class SessionCreateRequest(BaseModel):
    """Request to start a new session"""
    grade_level: Optional[str] = None
    strand_code: Optional[str] = None
    standard_id: Optional[str] = None
    additional_context: Optional[str] = None
```

The frontend `SessionCreatePayload` type also includes these fields:

```typescript
export interface SessionCreatePayload {
  grade_level?: string
  strand_code?: string
  standard_id?: string
  additional_context?: string
}
```

## Impact

When a user:
1. Fills in lesson context (e.g., "Class has recorders and a 30-minute block with mixed instruments")
2. Selects a specific standard
3. Clicks "New Conversation"

The AI assistant receives **no context** about the lesson settings, requiring the user to re-type this information in the chat, which defeats the purpose of having a context panel.

## Recommended Fix

### Solution 1: Pass LessonSettings to initSession

Modify `initSession` to accept and use the current lesson settings:

**File:** `/frontend/src/hooks/useSession.ts`

```typescript
const initSession = useCallback(
  async (
    grade: string = 'Grade 3',
    strand: string = 'Connect',
    standardId?: string | null,
    additionalContext?: string | null
  ) => {
    try {
      const result = await api.createSession({
        grade_level: grade,
        strand_code: strand,
        ...(standardId && { standard_id: standardId }),
        ...(additionalContext && { additional_context: additionalContext }),
      });
      
      // ... rest of function
    }
  },
  [loadStandards]
);
```

**File:** `/frontend/src/pages/UnifiedPage.tsx`

```typescript
const handleNewConversation = async () => {
  const newSession = await initSession(
    lessonSettings.selectedGrade,
    lessonSettings.selectedStrand,
    lessonSettings.selectedStandard?.id || null,
    lessonSettings.lessonContext || null
  );
  
  // ... rest of function
};
```

### Solution 2: Send Initial AI Message with Context

Alternatively (or additionally), after creating the session, automatically send an initial system/user message to the AI that includes all the lesson context. This would provide the AI with the full context immediately.

## Testing Steps

1. ✓ Load the application at http://localhost:5173/
2. ✓ Verify current selections in right panel show:
   - Grade 3
   - Connect strand
   - Additional context textarea with content
3. ✓ Click "New Conversation" button
4. ✓ Inspect network request to `/api/sessions`
5. ✓ Verify request body only contains grade_level and strand_code
6. ✓ Verify response shows `additional_context: null`

## Console Logs
No console errors detected during testing.

## Network Requests
- Session creation: `POST /api/sessions` - Status 200 OK
- Standards loading: `GET /api/standards?grade_level=3&strand_code=CN` - Status 200 OK
- Sessions list refresh: `GET /api/sessions` - Status 200 OK

## Additional Notes

The backend does NOT currently support storing `lessonDuration` or `classSize` in the session model. These fields are only stored in the frontend state. If these need to be persisted to the session, the backend Session model would need to be updated.

## Priority
**HIGH** - This is a core UX issue that requires users to re-enter information they've already provided.
