# Implementation Tasks

## 1. Frontend Type Updates
- [x] 1.1 Update `frontend/src/lib/types.ts` - Change `selectedStandard` from `StandardRecord | null` to `StandardRecord[]`
- [x] 1.2 Update `frontend/src/lib/types.ts` - Change `selectedObjective` from `string | null` to `string[]`
- [x] 1.3 Update `frontend/src/types/unified.ts` - Update `LessonSettings` interface to use arrays

## 2. Frontend Component Updates  
- [x] 2.1 Replace Standard dropdown in `RightPanel.tsx` with MultiSelectStandard component
- [x] 2.2 Replace Objective dropdown in `RightPanel.tsx` with MultiSelectObjectives component
- [x] 2.3 Remove "Additional Standards" and "Additional Objectives" labels/sections (now unified)
- [x] 2.4 Update `RightPanel.tsx` props to use arrays instead of single values
- [x] 2.5 Update `MultiSelectStandard.tsx` label to "Standards" instead of "Additional Standards"
- [x] 2.6 Update `MultiSelectObjectives.tsx` label to "Objectives" instead of "Additional Objectives"

## 3. Frontend State Management
- [x] 3.1 Update `UnifiedPage.tsx` state variables from single values to arrays
- [x] 3.2 Update `UnifiedPage.tsx` handlers to work with arrays (add/remove instead of set)
- [x] 3.3 Update `useSession.ts` to create sessions with array-based standards/objectives
- [x] 3.4 Update session restoration logic to handle array format
- [x] 3.5 Merge `additionalStandards` and `selectedStandard` into single `standards` array
- [x] 3.6 Merge `additionalObjectives` and `selectedObjective` into single `objectives` array

## 4. Backend API Model Updates
- [x] 4.1 Update `backend/api/models.py` - `SessionCreateRequest.standard_id` to `standard_ids: List[str]`
- [x] 4.2 Update `backend/api/models.py` - `SessionCreateRequest.selected_objectives` to accept List[str]
- [x] 4.3 Update `backend/api/models.py` - `SessionResponse.selected_standard` to `selected_standards: List[Dict[str, Any]]`
- [x] 4.4 Update `backend/api/models.py` - `SessionResponse.selected_objectives` to `List[str]`
- [x] 4.5 Remove `additional_standards` and `additional_objectives` from models (now merged)

## 5. Backend Session Handling
- [x] 5.1 Update `backend/api/routes/sessions.py` - Session creation to handle arrays
- [x] 5.2 Update `_session_to_response()` to convert arrays properly
- [x] 5.3 Update `_create_lesson_agent()` to use first standard as primary for compatibility
- [x] 5.4 Update session repository if database schema changes needed
- [x] 5.5 Add migration logic for existing sessions (single → array format)

## 6. Testing & Validation
- [x] 6.1 Test multi-select standards picker (add, remove, search)
- [x] 6.2 Test multi-select objectives picker (add, remove, search)
- [x] 6.3 Test session creation with multiple standards
- [x] 6.4 Test session restoration maintains all selections
- [x] 6.5 Test lesson generation with multiple standards
- [x] 6.6 Test backward compatibility with existing sessions

## 7. Documentation
- [x] 7.1 Update API documentation for new array-based endpoints
- [x] 7.2 Document migration strategy for existing sessions
- [x] 7.3 Update user-facing docs if needed
