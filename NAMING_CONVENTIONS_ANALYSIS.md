# PocketMusec Naming Conventions Analysis

## Executive Summary

The PocketMusec codebase exhibits **inconsistent naming conventions** across the stack, with clear separation between Python backend (snake_case) and TypeScript frontend (camelCase). The API layer uses a conversion mechanism via Pydantic's `CamelModel` to bridge these worlds, but this creates friction points and opportunities for standardization.

---

## 1. PYTHON BACKEND - Naming Patterns

### Functions
**Convention: `snake_case`**
- ✓ `create_lesson()`
- ✓ `list_lessons_for_user()`
- ✓ `list_lessons_for_session()`
- ✓ `_validate_presentation_step()`
- ✓ `export_presentation()`
- ✓ `setup_interceptors()`

### Variables
**Convention: `snake_case`**
- ✓ `grade_level`
- ✓ `strand_code`
- ✓ `lesson_duration`
- ✓ `class_size`
- ✓ `additional_context`
- ✓ `standard_id`
- ✓ `session_error`
- ✓ `is_draft`
- ✓ `user_id`

### Classes
**Convention: `PascalCase`**
- ✓ `CamelModel` (base class for API responses)
- ✓ `ExportService`
- ✓ `ExportOptions`
- ✓ `PresentationRepository`
- ✓ `LessonRepository`
- ✓ `Standard`
- ✓ `Objective`
- ✓ `StandardWithObjectives`

### Module/File Names
**Convention: `snake_case`**
- ✓ `export_service.py`
- ✓ `presentation_service.py`
- ✓ `lesson_repository.py`
- ✓ `user_storage_manager.py`
- ✓ `presentation_jobs.py`
- ✓ `progress_websocket.py`
- ✓ `field_converter.py`
- ✓ `database_field_mapper.py`

### API Models/Pydantic Classes
**Convention: `PascalCase` for class names, `snake_case` for fields**
```python
class SessionCreateRequest(CamelModel):
    grade_level: Optional[str] = None
    strand_code: Optional[str] = None
    standard_id: Optional[str] = None
    additional_context: Optional[str] = None
    lesson_duration: Optional[str] = None
    class_size: Optional[int] = None
    selected_objectives: Optional[List[str]] = None
    selected_model: Optional[str] = None

class UserResponse(CamelModel):
    id: str
    email: str
    full_name: Optional[str]
    role: str
    processing_mode: str
    created_at: Optional[datetime]
    last_login: Optional[datetime]
    is_active: bool
```

**Note:** The `CamelModel` base class has `alias_generator=to_camel_case`, which automatically converts these snake_case Python fields to **camelCase in JSON responses**.

### Database Schema
**Convention: `snake_case` column names**
```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    grade_level TEXT,
    strand_code TEXT,
    selected_standards TEXT,
    selected_objectives TEXT,
    additional_context TEXT,
    lesson_duration TEXT,
    class_size INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    selected_model TEXT
)

CREATE TABLE presentations (
    id TEXT PRIMARY KEY,
    lesson_id TEXT NOT NULL,
    lesson_revision INTEGER NOT NULL,
    version TEXT DEFAULT 'p1.0',
    status TEXT DEFAULT 'pending',
    style TEXT DEFAULT 'default',
    slides TEXT NOT NULL,
    export_assets TEXT,
    error_code TEXT,
    error_message TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

CREATE TABLE lessons (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    user_id TEXT,
    title TEXT,
    content TEXT,
    metadata TEXT,
    processing_mode TEXT,
    is_draft INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

---

## 2. TYPESCRIPT/REACT FRONTEND - Naming Patterns

### Functions
**Convention: `camelCase`**
- ✓ `useSession()`
- ✓ `useChat()`
- ✓ `useDrafts()`
- ✓ `useImages()`
- ✓ `useToast()`
- ✓ `loadStandards()`
- ✓ `initSession()`
- ✓ `processChatMessage()`
- ✓ `formatSessionsAsConversations()`
- ✓ `setupInterceptors()`
- ✓ `handleTextareaInput()`
- ✓ `removeStandard()`

### Variables
**Convention: `camelCase`**
- ✓ `sessionError`
- ✓ `selectedStandards`
- ✓ `lessonDuration`
- ✓ `classSize`
- ✓ `additionalContext`
- ✓ `standardId`
- ✓ `isLoadingSessions`
- ✓ `isFetching`
- ✓ `isDraft`
- ✓ `userId`
- ✓ `uploadedAt`
- ✓ `createdAt`
- ✓ `updatedAt`
- ✓ `mimeType`
- ✓ `fileSize`
- ✓ `ocrText`
- ✓ `visionAnalysis`

### React Components
**Convention: `PascalCase`**
- ✓ `ChatMessage`
- ✓ `ChatInput`
- ✓ `ChatPanel`
- ✓ `MultiSelectStandard`
- ✓ `MultiSelectObjectives`
- ✓ `DraftsModal`
- ✓ `ImageUploadModal`
- ✓ `LessonEditor`
- ✓ `PresentationGenerator`

### TypeScript Interfaces/Types
**Convention: `PascalCase`**
- ✓ `DraftItem`
- ✓ `StandardRecord`
- ✓ `SessionResponsePayload`
- ✓ `ChatResponsePayload`
- ✓ `ImageData`
- ✓ `ImageClassification`
- ✓ `StorageInfo`
- ✓ `ConversationGroup`
- ✓ `ChatMessage`

### Type Properties
**Convention: `camelCase`**
```typescript
export interface DraftItem {
  id: string;
  title: string;
  content: string;
  originalContent?: string;
  metadata?: {
    lessonDocument?: LessonDocumentM2;
    [key: string]: unknown;
  };
  grade?: string;
  strand?: string;
  standard?: string;
  createdAt: string;
  updatedAt: string;
  presentationStatus?: {
    id?: string;
    presentationId?: string;
    status: PresentationStatus;
    lessonRevision?: number;
    updatedAt?: string;
  };
}

export interface ImageData {
  id: string;
  filename: string;
  uploadedAt: string;
  ocrText?: string | null;
  visionAnalysis?: string | null;
  fileSize: number;
  mimeType: string;
  classification?: ImageClassification | null;
}

export interface ConversationItem {
  id: string;
  title: string;
  hint: string;
  active: boolean;
  grade?: string;
  strand?: string;
  standard?: string;
  createdAt?: string;
  updatedAt?: string;
}
```

### Hooks
**Convention: `useXxx` (camelCase)**
- ✓ `useSession`
- ✓ `useChat`
- ✓ `useDrafts`
- ✓ `useImages`
- ✓ `useToast`
- ✓ `useLessons`
- ✓ `usePresentations`
- ✓ `useCitations`

### Stores (Zustand)
**Convention: `camelCase` with `Store` suffix**
- ✓ `useLessonStore`
- ✓ `useImageStore`
- ✓ `useConversationStore`
- ✓ `useUIStore`
- ✓ `useBrowseStore`

---

## 3. API LAYER - Naming Bridge

### Request Payloads
**Format: `snake_case` parameters**
```typescript
export interface SessionCreatePayload {
  grade_level?: string;
  strand_code?: string;
  standard_id?: string;
  additional_context?: string;
  lesson_duration?: string;
  class_size?: number;
  selected_objectives?: string[];
  selected_model?: string;
}

export interface ListStandardsParams {
  grade_level?: string;
  strand_code?: string;
  limit?: number;
}
```

### Response Payloads
**Format: Converted to `camelCase` by backend CamelModel**

When Pydantic models inherit from `CamelModel`:
```python
class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel_case,  # Converts snake_case → camelCase
        populate_by_name=True,          # Accepts both forms
        from_attributes=True,
    )
```

This means:
- Python fields: `grade_level` → JSON response: `gradeLevel`
- Python fields: `created_at` → JSON response: `createdAt`
- Python fields: `is_draft` → JSON response: `isDraft`

### API Endpoints
**Convention: `snake_case` in URL paths**
- ✓ `/api/sessions` (not /api/Sessions or /api/sessionList)
- ✓ `/api/lessons`
- ✓ `/api/presentations`
- ✓ `/api/standards`
- ✓ `/api/images`
- ✓ `/api/embeddings`
- ✓ `/api/workspace/dashboard`
- ✓ `/sessions/{sessionId}/messages` (path params are camelCase)
- ✓ `/sessions/{sessionId}/messages/stream`

---

## 4. KEY INCONSISTENCIES & FRICTION POINTS

### Problem 1: API Request/Response Mismatch
- **Frontend sends:** `snake_case` (grade_level, strand_code)
- **Frontend expects to receive:** `camelCase` (gradeLevel, strandCode)
- **Backend interprets:** `snake_case` → converts to `camelCase` only in response

**Impact:** Manual mapping needed in frontend hooks

### Problem 2: Missing Type Definitions
- Frontend imports from `./lib/types` but file doesn't exist:
  ```typescript
  import type { StandardRecord, SessionResponsePayload } from './lib/types'
  ```
- Types are imported but never defined (TypeScript would flag this)
- Shows incomplete refactoring or type generation setup

### Problem 3: Mixed Naming in Tests
- Some tests use `snake_case`: `created_at: '2025-01-01T00:00:00Z'`
- Some components expect `camelCase`: `createdAt`
- Example from tests:
  ```typescript
  created_at: '2025-01-01T00:00:00Z',  // snake_case
  ```
  But interface expects:
  ```typescript
  createdAt: string;  // camelCase
  ```

### Problem 4: Inconsistent Field Conversion
- Some frontend code uses `createdAt` (camelCase)
- Other frontend code uses `created_at` (snake_case)
- Example: `ExportQueueManager.tsx` uses `sortBy: 'createdAt'` but mock data uses `created_at`

### Problem 5: Configuration Inconsistency
- `to_camel_case()` function in Python converts snake_case to camelCase
- But frontend API types still define snake_case parameters
- This creates confusion about the contract

---

## 5. CONFIGURATION & CONVERSION UTILITIES

### Python Conversion Function
**Location:** `/home/user/pocket_musec/backend/utils/casing.py`
```python
def to_camel_case(value: str) -> str:
    """Convert snake_case or kebab-case strings to camelCase."""
    if not value:
        return value
    value = value.replace("-", "_")
    parts = value.split("_")
    if len(parts) == 1:
        return parts[0]
    head, *rest = parts
    return head + "".join(token.capitalize() if token else "" for token in rest)

def camelize(value: Any) -> Any:
    """Recursively convert dictionary keys to camelCase."""
    if isinstance(value, dict):
        return {to_camel_case(str(key)): camelize(child) for key, child in value.items()}
    if isinstance(value, (list, tuple, set)):
        return type(value)(camelize(item) for item in value)
    return value
```

### Ruff Configuration
**Location:** `pyproject.toml`
```toml
[tool.ruff]
line-length = 88
target-version = "py311"
select = ["E", "F", "W", "I", "N", "B", "C90"]
ignore = ["E501", "B008"]
```
- `"N"` enforces PEP 8 naming conventions
- This ensures snake_case for functions, variables, and modules

---

## 6. ENVIRONMENT & BUILD CONFIGURATION

### Frontend TypeScript Config
**tsconfig.json:**
- `strict: true` - Type checking enabled
- `skipLibCheck: true` - Skip type checking for external libraries
- `noUnusedLocals: false` - Allows unused variables (not strict)
- Path mapping configured for `@/*` → `./src/*`

### Backend Configuration
**pyproject.toml:**
- Python 3.11+ required
- Type checking via MyPy enabled
- Linting via Ruff (enforces snake_case)
- Pydantic 2.0+ required (supports CamelModel alias_generator)

---

## 7. SUMMARY TABLE: NAMING CONVENTIONS BY AREA

| Area | Pattern | Examples | Status |
|------|---------|----------|--------|
| **Backend Python** | | | |
| Functions | snake_case | `create_lesson()`, `list_sessions()` | ✓ Consistent |
| Variables | snake_case | `grade_level`, `user_id`, `is_draft` | ✓ Consistent |
| Classes | PascalCase | `ExportService`, `CamelModel` | ✓ Consistent |
| Modules | snake_case | `export_service.py`, `lesson_repository.py` | ✓ Consistent |
| **Database** | | | |
| Columns | snake_case | `grade_level`, `created_at`, `user_id` | ✓ Consistent |
| **API Layer** | | | |
| Endpoints | snake_case | `/api/lessons`, `/api/sessions` | ✓ Consistent |
| Request fields | snake_case | `grade_level`, `standard_id` | ⚠ Mixed (see below) |
| Response fields | camelCase | `gradeLevel`, `standardId` | ✓ Via CamelModel |
| **Frontend TypeScript** | | | |
| Functions | camelCase | `useSession()`, `loadStandards()` | ✓ Consistent |
| Variables | camelCase | `sessionError`, `selectedStandards` | ✓ Consistent |
| Components | PascalCase | `ChatMessage`, `MultiSelectStandard` | ✓ Consistent |
| Interfaces | PascalCase | `DraftItem`, `StandardRecord` | ✓ Consistent |
| Interface properties | camelCase | `createdAt`, `uploadedAt`, `userId` | ✓ Consistent |
| Hooks | useXxx | `useSession`, `useDrafts` | ✓ Consistent |

---

## 8. RECOMMENDATIONS FOR CAMELCASE STANDARDIZATION

### Current State
The codebase is partially ready for camelCase standardization:
- ✓ Frontend already uses camelCase throughout
- ✓ API layer has conversion mechanism in place (CamelModel)
- ✓ Conversion utilities exist (to_camel_case, camelize)
- ✗ Backend still uses snake_case (per Python convention)
- ✗ Database still uses snake_case
- ✗ API request payloads are snake_case
- ✗ Missing type definitions need to be created/fixed

### Conversion Strategy

**Option 1: Frontend-Only camelCase (Recommended - Minimal Impact)**
- Keep backend Python as snake_case (Python convention)
- Keep database as snake_case
- Keep API requests as snake_case
- Ensure all API responses are camelCase (already done via CamelModel)
- Fix missing type definitions
- This minimizes backend changes while providing consistent frontend experience

**Option 2: Full Stack camelCase (Higher Impact)**
- Convert backend Python to camelCase (breaks Python convention)
- Convert database to camelCase
- Convert API to full camelCase
- Much more invasive, requires extensive refactoring

**Option 3: Hybrid Approach (Balanced)**
- Keep Python code as snake_case (respects convention)
- Optionally convert database to camelCase (for consistency)
- Ensure API layer fully converts both directions
- Create comprehensive type definitions for frontend

---

## CONCLUSION

The PocketMusec codebase exhibits **well-organized naming conventions within each layer**, but **inconsistencies at the API boundary**. The conversion mechanism via `CamelModel` is already in place, making Option 1 (Frontend-only standardization with proper type definitions) the most practical path forward. The main work involves:

1. Creating proper TypeScript type definitions for API responses
2. Ensuring all API response fields are properly camelCased
3. Adding conversion middleware to handle request field conversion if needed
4. Fixing test data to match expected camelCase format
5. Documenting the API contract clearly

