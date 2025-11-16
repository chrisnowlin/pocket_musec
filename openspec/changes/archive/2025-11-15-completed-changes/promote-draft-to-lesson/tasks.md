# Tasks: Promote Draft to Lesson

## Backend Tasks

### 1. Add promotion/demotion repository methods
**Dependencies**: None
**Deliverable**: `LessonRepository.promote_lesson()` and `LessonRepository.demote_lesson()` methods

- [x] Add `promote_lesson(lesson_id: str)` method to `LessonRepository`
- [x] Add `demote_lesson(lesson_id: str)` method to `LessonRepository`
- [x] Both methods should call `update_lesson()` with `is_draft` flag toggled
- [x] Ensure `updated_at` timestamp is refreshed automatically
- [x] Write unit tests for both methods covering success and error cases

**Validation**: pytest tests pass for promotion/demotion logic

---

### 2. Create lesson promotion API endpoint
**Dependencies**: Task 1
**Deliverable**: `POST /api/lessons/{lesson_id}/promote` endpoint

- [x] Create route handler in `/api/routes/lessons.py`
- [x] Verify lesson exists and belongs to authenticated user (return 404 if not)
- [x] Call `LessonRepository.promote_lesson(lesson_id)`
- [x] Return updated lesson in `LessonSummary` format with 200 OK
- [x] Add endpoint to router and update OpenAPI docs
- [x] Write integration tests for successful promotion and error cases

**Validation**: API tests pass; manual testing via curl or Postman confirms behavior

---

### 3. Create lesson demotion API endpoint
**Dependencies**: Task 1
**Deliverable**: `POST /api/lessons/{lesson_id}/demote` endpoint

- [x] Create route handler in `/api/routes/lessons.py`
- [x] Verify lesson exists and belongs to authenticated user (return 404 if not)
- [x] Call `LessonRepository.demote_lesson(lesson_id)`
- [x] Return updated lesson in `LessonSummary` format with 200 OK
- [x] Add endpoint to router and update OpenAPI docs
- [x] Write integration tests for successful demotion and error cases

**Validation**: API tests pass; manual testing confirms behavior

---

## Frontend Tasks

### 4. Create useLessons hook
**Dependencies**: None (parallel with backend tasks)
**Deliverable**: `frontend/src/hooks/useLessons.ts` hook for managing permanent lessons

- [x] Create `useLessons` hook following pattern from `useDrafts`
- [x] Fetch lessons where `is_draft=false` via `/api/lessons?is_draft=false` (extend existing endpoint or create new one)
- [x] Implement `promoteFromDraft(draftId)` method calling `POST /api/lessons/{id}/promote`
- [x] Implement `demoteToLesson(lessonId)` method calling `POST /api/lessons/{id}/demote`
- [x] Handle loading states, errors, and auto-refresh after mutations
- [x] Add TypeScript types for `LessonItem` (similar to `DraftItem`)

**Validation**: Hook compiles without errors; manual testing in dev tools console

---

### 5. Add "My Lessons" tab to MusecDB page
**Dependencies**: Task 4
**Deliverable**: New tab in `MusecDBPage.tsx` for viewing permanent lessons

- [x] Add `'lessons'` to `TabType` union in `MusecDBPage.tsx`
- [x] Create tab button in navigation bar (after "Saved Drafts")
- [x] Integrate `useLessons` hook to fetch and manage lesson data
- [x] Render lesson list with same layout as drafts tab (search, filters, preview pane)
- [x] Include actions: View, Export, Edit, Move to Drafts, Delete
- [x] Show empty state when no lessons exist
- [x] Ensure preview pane is resizable (reuse existing resizer logic)

**Validation**: Tab renders correctly; lessons are fetched and displayed

---

### 6. Add "Promote to Lesson" button in drafts UI
**Dependencies**: Task 4
**Deliverable**: Action button on each draft card to promote draft

- [x] Add "Promote to Lesson" button to draft card actions in `MusecDBPage.tsx` drafts tab
- [x] Style button distinctly (e.g., purple background per design)
- [x] Implement `handlePromoteDraft(draftId)` handler calling `useLessons.promoteFromDraft()`
- [x] Show success notification on promotion: "Draft promoted to lesson"
- [x] Show error notification on failure: "Failed to promote draft. Please try again."
- [x] Remove promoted draft from drafts list immediately on success
- [x] Ensure button is disabled during API call (prevent double-clicks)

**Validation**: Button appears, promotes draft, updates UI correctly

---

### 7. Add "Move to Drafts" button in lessons UI
**Dependencies**: Task 5
**Deliverable**: Action button on each lesson card to demote lesson

- [x] Add "Move to Drafts" button to lesson card actions in "My Lessons" tab
- [x] Style button appropriately (neutral or secondary color)
- [x] Implement `handleDemoteLesson(lessonId)` handler calling `useLessons.demoteToLesson()`
- [x] Show success notification on demotion: "Lesson moved to drafts"
- [x] Show error notification on failure: "Failed to move lesson. Please try again."
- [x] Remove demoted lesson from lessons list immediately on success
- [x] Ensure button is disabled during API call

**Validation**: Button appears, demotes lesson, updates UI correctly

---

### 8. Add search and filter to "My Lessons" tab
**Dependencies**: Task 5
**Deliverable**: Search bar and grade/strand filters for permanent lessons

- [x] Reuse filter component pattern from drafts tab
- [x] Implement search by title/content for lessons
- [x] Implement grade/strand dropdown filters
- [x] Show filtered result count (e.g., "5 of 10 lessons")
- [x] Add "Clear Filters" button
- [x] Ensure filters persist during session (optional enhancement)

**Validation**: Search and filters work correctly; result count updates

---

## Integration & Testing Tasks

### 9. End-to-end testing of promotion workflow
**Dependencies**: Tasks 1-8
**Deliverable**: Verified promotion/demotion flow works end-to-end

- [x] Create a draft lesson via UI
- [x] Promote draft to permanent lesson
- [x] Verify draft disappears from "Saved Drafts" tab
- [x] Verify lesson appears in "My Lessons" tab
- [x] Verify lesson data (title, content, metadata) is preserved
- [x] Demote lesson back to draft
- [x] Verify lesson disappears from "My Lessons" tab
- [x] Verify draft reappears in "Saved Drafts" tab
- [x] Test error handling (network failures, unauthorized access)

**Validation**: Complete workflow functions without errors

---

### 10. Update documentation and examples
**Dependencies**: Tasks 1-9
**Deliverable**: Updated API docs and user-facing documentation

- [x] Add promotion/demotion endpoints to OpenAPI/Swagger docs
- [x] Update user guide or README with workflow explanation
- [x] Add screenshots or GIFs of promotion workflow (if applicable)
- [x] Document keyboard shortcuts or quick actions (future enhancement)

**Validation**: Documentation is accurate and helpful

---

## Parallelizable Work
- Tasks 1-3 (backend) can proceed independently of tasks 4-8 (frontend)
- Task 4 (`useLessons` hook) can be developed in parallel with backend tasks
- Tasks 6 and 7 can be worked on simultaneously by different developers
- Task 8 (search/filter) can be added after task 5 is complete

## Sequencing Constraints
- Task 5 depends on task 4 (needs `useLessons` hook)
- Task 6 depends on task 4 (needs `promoteFromDraft` method)
- Task 7 depends on task 5 (needs lessons UI to exist)
- Task 9 depends on all previous tasks being complete