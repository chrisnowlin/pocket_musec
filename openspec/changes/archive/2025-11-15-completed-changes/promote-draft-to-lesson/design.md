# Design: Promote Draft to Lesson

## Architecture Overview

### Data Model
The existing `Lesson` model already supports the distinction via the `is_draft` boolean field:
```python
@dataclass
class Lesson:
    id: str
    session_id: str
    user_id: str
    title: str
    content: str
    metadata: Optional[str] = None
    processing_mode: ProcessingMode = ProcessingMode.CLOUD
    is_draft: bool = False  # <-- Key field for draft vs. permanent
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

No schema changes required—promotion is simply toggling `is_draft` and potentially updating metadata.

### Backend Design

#### New Endpoints
Add to `/api/lessons`:
- `POST /api/lessons/{lesson_id}/promote` - Promote draft to permanent lesson
- `POST /api/lessons/{lesson_id}/demote` - Demote permanent lesson to draft

These endpoints will:
1. Verify lesson ownership (`user_id` matches current user)
2. Toggle `is_draft` flag
3. Update `updated_at` timestamp
4. Return updated lesson in standard response format

#### Repository Layer
Extend `LessonRepository` with:
```python
def promote_lesson(self, lesson_id: str) -> Optional[Lesson]:
    """Toggle is_draft=False and update timestamp"""
    return self.update_lesson(lesson_id, is_draft=False)

def demote_lesson(self, lesson_id: str) -> Optional[Lesson]:
    """Toggle is_draft=True and update timestamp"""
    return self.update_lesson(lesson_id, is_draft=True)
```

These are thin wrappers around existing `update_lesson()` method for semantic clarity.

### Frontend Design

#### Drafts UI Enhancement
In `MusecDBPage` drafts tab, add "Promote to Lesson" button alongside existing actions (Edit, Export, Delete):
```tsx
<button
  onClick={(e) => {
    e.stopPropagation();
    handlePromoteDraft(draft.id);
  }}
  className="px-3 py-1.5 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700"
>
  Promote to Lesson
</button>
```

Handler calls new API endpoint and refreshes draft list on success.

#### My Lessons Tab
Add new tab "My Lessons" to `MusecDBPage` (alongside Saved Drafts, Database Browser, etc.):
- Lists all lessons where `is_draft=False` for current user
- Similar layout to drafts: searchable list with preview pane
- Actions: View, Export, Edit, Move to Drafts, Delete

#### State Management
Reuse existing `useDrafts` hook pattern but create parallel `useLessons` hook:
```tsx
export function useLessons() {
  const [lessons, setLessons] = useState<LessonItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Fetches lessons where is_draft=False
  const fetchLessons = async () => { ... };
  const promoteFromDraft = async (draftId: string) => { ... };
  const demoteToLesson = async (lessonId: string) => { ... };

  return { lessons, isLoading, fetchLessons, promoteFromDraft, demoteToLesson };
}
```

### UI Flow

#### Promotion Flow
1. Teacher browses saved drafts in MusecDB → Saved Drafts tab
2. Teacher clicks "Promote to Lesson" on a draft card
3. System calls `POST /api/lessons/{id}/promote`
4. Backend toggles `is_draft=False`, updates timestamp
5. Frontend removes draft from drafts list, shows success notification
6. Teacher can now find the lesson in "My Lessons" tab

#### Demotion Flow
1. Teacher browses permanent lessons in MusecDB → My Lessons tab
2. Teacher clicks "Move to Drafts" on a lesson card
3. System calls `POST /api/lessons/{id}/demote`
4. Backend toggles `is_draft=True`, updates timestamp
5. Frontend removes lesson from lessons list, shows success notification
6. Teacher can now find the draft in "Saved Drafts" tab

### Trade-offs

#### Toggle vs. Copy
**Decision**: Use toggle (update `is_draft` in-place) rather than creating a new record.

**Rationale**:
- Simpler implementation (no duplicate records)
- Preserves lesson ID for references/citations
- Teachers can easily undo via demotion
- Less database bloat

**Alternative**: Copy-on-promote would preserve draft as-is but adds complexity (managing two records, sync issues, increased storage).

#### Single-Click vs. Modal
**Decision**: Single-click promotion for speed, no confirmation modal required.

**Rationale**:
- Promotion is easily reversible via demotion
- Teachers value speed over safety for low-risk operations
- Metadata can be edited post-promotion if needed

**Alternative**: Confirmation modal with metadata review slows workflow but provides safety net—can add later if users request.

### Security & Validation
- All endpoints verify `user_id` matches current authenticated user
- Return 404 for non-existent or unauthorized lessons
- No special permissions required—all users can promote their own drafts

### Error Handling
- 404 if lesson not found or not owned by user
- 400 if lesson is already in target state (e.g., promoting a non-draft)
- 500 for database failures with rollback

### Performance Considerations
- Promotion/demotion is single UPDATE query, minimal overhead
- No cascading updates or complex transactions required
- Fetching lessons vs. drafts uses same index on `user_id` and `is_draft`
