# OpenSpec Change Proposal Created

## Change ID: `replace-dropdowns-with-multiselect`

### Summary

Created a comprehensive OpenSpec change proposal to replace the single-select Standard and Objective dropdowns with unified multi-select picker components, eliminating the confusing "primary vs additional" distinction.

### What Was Created

**Change Directory:** `openspec/changes/replace-dropdowns-with-multiselect/`

**Files:**
1. **`proposal.md`** - Why, what changes, and impact assessment
2. **`tasks.md`** - 7 major implementation phases with 42 specific tasks
3. **`specs/workspace-shell/spec.md`** - UI interaction pattern changes
4. **`specs/session-management/spec.md`** - API and data model changes

### Key Changes

**Breaking Changes:**
- Replace single-select Standard dropdown → Multi-select Standards picker
- Replace single-select Objective dropdown → Multi-select Objectives picker
- Remove "primary" vs "additional" concept
- API contract changes: single values → arrays

**Benefits:**
- Consistent UX - same interaction pattern for all selections
- More powerful - users can select multiple standards/objectives upfront
- Cleaner UI - no confusing distinction between "primary" and "additional"
- Leverages existing multi-select components (already built and tested)

**Backward Compatibility:**
- Existing sessions migrated (single value → array with one element)
- Backend can treat first item as "primary" if needed for lesson generation

### Implementation Phases

1. **Frontend Type Updates** - Change types from single values to arrays
2. **Frontend Component Updates** - Replace dropdowns with multi-select pickers
3. **Frontend State Management** - Merge separate state variables into unified arrays
4. **Backend API Model Updates** - Accept/return arrays instead of single values
5. **Backend Session Handling** - Update session creation/retrieval logic
6. **Testing & Validation** - End-to-end testing of multi-select functionality
7. **Documentation** - Update API docs and migration guides

### Validation Status

✅ **Validated with `openspec validate --strict`**

The change proposal passes all validation checks and is ready for review and approval before implementation.

### Next Steps

1. **Review & Approve** - Proposal needs team review and approval
2. **Implement** - Follow tasks.md sequentially after approval
3. **Test** - Comprehensive testing per tasks.md section 6
4. **Archive** - Move to archive after deployment

### Additional Fix: ChatMessage Infinite Loop

**Issue:** `useLegacyCitations` hook was causing "Maximum update depth exceeded" errors due to array reference changes triggering infinite re-renders.

**Solution:** Removed the legacy citations hook entirely. Citations now only load via `lessonId` using the `useCitations` hook.

**Files Modified:**
- `frontend/src/hooks/useCitations.ts` - Removed `useLegacyCitations` export
- `frontend/src/components/unified/ChatMessage.tsx` - Removed legacy citations usage

**Result:** Infinite loop fixed, React console errors eliminated.

---

## Commands Reference

```bash
# View the proposal
openspec show replace-dropdowns-with-multiselect

# View affected specs
openspec diff replace-dropdowns-with-multiselect

# Validate again
openspec validate replace-dropdowns-with-multiselect --strict

# After implementation and deployment
openspec archive replace-dropdowns-with-multiselect --yes
```
