# Replace Single-Select Dropdowns with Multi-Select Pickers

## Why

The current workspace uses dedicated single-select dropdowns for primary standard and objective selection, alongside separate multi-select components for additional standards and objectives. This creates UI inconsistency and confusion. Users experience two different interaction patterns for the same conceptual operation (selecting standards/objectives). The multi-select picker component already built for "additional" selections is more powerful and user-friendly than the traditional dropdown approach.

## What Changes

- **BREAKING**: Replace the single-select Standard dropdown with a multi-select picker component
- **BREAKING**: Replace the single-select Objective dropdown with a multi-select picker component  
- Remove the concept of "primary" vs "additional" standards and objectives
- Unify the selection UX - all standards and objectives use the same multi-select picker pattern
- Update backend API to accept arrays instead of single values for `standard_id` and `selected_objectives`
- Update session storage to store all selections as comma-separated arrays
- Maintain backward compatibility during migration by treating first item in arrays as "primary" if needed

## Impact

**Affected specs:**
- `workspace-shell` - UI components and interaction patterns
- `session-management` - Session data model and API contracts

**Affected code:**
- Frontend:
  - `frontend/src/components/unified/RightPanel.tsx` - Replace dropdowns with multi-select pickers
  - `frontend/src/pages/UnifiedPage.tsx` - Update state management for arrays instead of single values
  - `frontend/src/hooks/useSession.ts` - Update session creation/restoration logic
  - `frontend/src/lib/types.ts` - Update type definitions
  - Remove distinction between `selectedStandard` and `additionalStandards`
  
- Backend:
  - `backend/api/models.py` - Update request/response models to use arrays
  - `backend/api/routes/sessions.py` - Update session endpoints to handle arrays
  - `backend/repositories/session_repository.py` - Update database queries if needed
  - Lesson generation logic that references "primary" standard may need updates

**Migration notes:**
- Existing sessions with single `standard_id` will be migrated to array format with one element
- UI will display all selected standards equally (no visual "primary" distinction)
- Backend lesson generation can treat first standard as primary for compatibility
