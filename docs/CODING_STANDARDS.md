# PocketMusec Coding Standards

## Overview

This document defines the coding standards and conventions for the PocketMusec project. All contributors must follow these guidelines to ensure code consistency, maintainability, and quality across the codebase.

---

## Naming Conventions

### ⚠️ **REQUIRED: camelCase Standard**

**Effective immediately, all property names across the entire codebase MUST use camelCase.**

This is a **mandatory standard** that applies to:
- ✅ Backend Python models (automatically handled via `CamelModel`)
- ✅ Frontend TypeScript interfaces and types
- ✅ API request/response payloads
- ✅ Database field mappings
- ✅ JSON serialization

#### Why camelCase?

1. **Consistency with JavaScript/TypeScript ecosystem** - Frontend naturally uses camelCase
2. **Industry standard for APIs** - Most modern REST APIs use camelCase in JSON
3. **Reduced cognitive load** - Developers don't need to remember different conventions
4. **Automatic conversion** - Backend uses `CamelModel` for seamless snake_case → camelCase conversion

### Backend (Python)

#### Model Properties
**All Pydantic models MUST inherit from `CamelModel` instead of `BaseModel`:**

```python
# ✅ CORRECT
from backend.api.models import CamelModel

class UserResponse(CamelModel):
    userId: str
    fullName: str
    createdAt: datetime
    processingMode: str
```

```python
# ❌ INCORRECT - Do NOT use BaseModel directly
from pydantic import BaseModel

class UserResponse(BaseModel):
    user_id: str  # Wrong: snake_case
    full_name: str  # Wrong: snake_case
```

#### Internal Python Code
For internal Python code (not API models), follow PEP 8:
- **Variables/Functions:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`

```python
# ✅ CORRECT - Internal Python code
class LessonRepository:
    def get_user_lessons(self, user_id: str) -> List[Lesson]:
        max_results = MAX_LESSON_LIMIT
        return self._query_lessons(user_id, max_results)
```

### Frontend (TypeScript/JavaScript)

**All properties MUST use camelCase:**

```typescript
// ✅ CORRECT
interface SessionResponse {
  sessionId: string;
  userId: string;
  createdAt: string;
  gradeLevel: string;
  strandCode: string;
}
```

```typescript
// ❌ INCORRECT
interface SessionResponse {
  session_id: string;  // Wrong: snake_case
  user_id: string;     // Wrong: snake_case
  created_at: string;  // Wrong: snake_case
}
```

#### Component/Class Names
- **Components:** `PascalCase` (e.g., `ChatMessage`, `FileManager`)
- **Files:** `PascalCase.tsx` for components, `camelCase.ts` for utilities
- **Functions:** `camelCase` (e.g., `handleSubmit`, `fetchData`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `API_BASE_URL`, `MAX_FILE_SIZE`)

### Database

**Database columns internally use snake_case (SQLite standard), but are automatically converted to camelCase in API responses via `CamelModel`.**

You don't need to manually convert - the framework handles it:

```python
# Database schema (SQLite)
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    full_name TEXT,
    created_at TIMESTAMP
);

# Pydantic model - will automatically serialize to camelCase
class User(CamelModel):
    user_id: str      # Internally snake_case
    full_name: str    # Internally snake_case
    created_at: datetime  # Internally snake_case

# API Response (automatic conversion)
{
  "userId": "123",       # ✅ camelCase
  "fullName": "John",    # ✅ camelCase
  "createdAt": "2025-11-17T00:00:00Z"  # ✅ camelCase
}
```

---

## Code Organization

### Backend Structure

```
backend/
├── api/
│   ├── routes/          # API endpoint definitions
│   ├── models.py        # Shared Pydantic models (USE CamelModel)
│   └── dependencies.py  # Shared dependencies
├── models/              # Database and schema models
├── services/            # Business logic layer
├── repositories/        # Data access layer
└── utils/              # Utility functions
```

### Frontend Structure

```
frontend/src/
├── components/          # Reusable React components
├── pages/              # Page-level components
├── services/           # API client services
├── hooks/              # Custom React hooks
├── stores/             # State management (Zustand)
├── types/              # TypeScript type definitions
└── utils/              # Utility functions
```

---

## Type Safety

### Backend
- ✅ Use type hints for all function parameters and return values
- ✅ Use Pydantic models for all API request/response bodies
- ✅ Inherit from `CamelModel` for automatic camelCase conversion
- ✅ Use `Optional[T]` for nullable fields
- ✅ Use `List[T]`, `Dict[K, V]` for collections

```python
from typing import List, Optional
from backend.api.models import CamelModel

class LessonUpdate(CamelModel):
    lessonId: str
    title: Optional[str] = None
    objectives: List[str] = []
    
async def update_lesson(
    lesson_id: str,
    updates: LessonUpdate,
    user_id: str
) -> LessonResponse:
    """Update a lesson with new data."""
    # Implementation
    pass
```

### Frontend
- ✅ Define TypeScript interfaces for all data structures
- ✅ Use strict mode (`strict: true` in tsconfig.json)
- ✅ Avoid `any` type - use `unknown` if type is truly unknown
- ✅ Use type guards for runtime type checking

```typescript
// ✅ CORRECT - Well-typed
interface Lesson {
  lessonId: string;
  title: string;
  objectives: string[];
  createdAt: string;
}

function updateLesson(lesson: Lesson): Promise<Lesson> {
  return api.put<Lesson>(`/lessons/${lesson.lessonId}`, lesson);
}
```

---

## API Design

### Endpoints
- Use RESTful conventions
- Use plural nouns for resources: `/api/lessons`, `/api/sessions`
- Use HTTP methods appropriately: GET, POST, PUT, DELETE
- Use kebab-case for URL paths: `/api/lesson-plans`

### Request/Response Format
**ALL API payloads MUST use camelCase:**

```json
// ✅ CORRECT - Request
POST /api/sessions
{
  "gradeLevel": "Grade 3",
  "strandCode": "CN",
  "lessonDuration": "45 minutes"
}

// ✅ CORRECT - Response
{
  "sessionId": "sess_123",
  "userId": "user_456",
  "gradeLevel": "Grade 3",
  "createdAt": "2025-11-17T12:00:00Z"
}
```

### Error Responses
Use consistent error format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Grade level is required",
    "details": {
      "field": "gradeLevel",
      "constraint": "required"
    }
  }
}
```

---

## Documentation

### Code Comments
- ✅ Use docstrings for all functions, classes, and modules
- ✅ Explain **why**, not **what** (code should be self-explanatory)
- ✅ Update comments when code changes
- ❌ Don't comment obvious code

```python
# ✅ GOOD - Explains why
def normalize_grade_level(grade: str) -> str:
    """
    Normalize grade level to standard format.
    
    This ensures consistency when comparing grades from different sources
    (e.g., user input "3rd grade" vs database "Grade 3").
    """
    return grade.replace("rd", "").replace("th", "").strip()

# ❌ BAD - States the obvious
def add_numbers(a: int, b: int) -> int:
    """Adds two numbers together."""  # Comment adds no value
    return a + b
```

### API Documentation
- Keep `docs/API.md` up-to-date with all endpoints
- Include request/response examples with **camelCase properties**
- Document error responses
- Note authentication requirements

---

## Testing

### Backend Tests
- Use `pytest` for all backend tests
- Test file naming: `test_*.py`
- Use fixtures for common setup
- Aim for >80% code coverage

```python
# tests/test_api/test_lessons.py
def test_create_lesson_with_camelcase_response(client, auth_headers):
    """Ensure API returns camelCase properties."""
    response = client.post(
        "/api/lessons",
        json={"gradeLevel": "Grade 3", "strandCode": "CN"},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert "lessonId" in data  # ✅ camelCase
    assert "createdAt" in data  # ✅ camelCase
```

### Frontend Tests
- Use Vitest for unit/integration tests
- Test file naming: `*.test.tsx` or `*.test.ts`
- Use React Testing Library for component tests
- Mock API calls appropriately

---

## Git Workflow

### Branch Naming
- `feature/` - New features: `feature/add-lesson-export`
- `fix/` - Bug fixes: `fix/session-timeout`
- `refactor/` - Code refactoring: `refactor/standardize-camelcase`
- `docs/` - Documentation updates: `docs/update-api-guide`

### Commit Messages
Follow conventional commits:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:** feat, fix, docs, style, refactor, test, chore

```bash
# ✅ GOOD
git commit -m "feat(api): add lesson export endpoint with camelCase response"

# ✅ GOOD
git commit -m "fix(frontend): correct property name from snake_case to camelCase"

# ❌ BAD
git commit -m "fixed stuff"
```

---

## Code Review Checklist

Before submitting a PR, verify:

- [ ] All new models inherit from `CamelModel` (backend)
- [ ] All TypeScript interfaces use camelCase properties (frontend)
- [ ] No snake_case properties in API request/response payloads
- [ ] Tests pass (`npm run test` and `pytest`)
- [ ] TypeScript builds without errors (`npm run build`)
- [ ] Code follows naming conventions
- [ ] Documentation updated if needed
- [ ] No console.log or debugger statements in production code
- [ ] No commented-out code

---

## Migration from snake_case

If you encounter existing snake_case code:

1. **Backend:** Change `BaseModel` → `CamelModel`
2. **Frontend:** Update interface properties to camelCase
3. **Update all usages** of the changed properties
4. **Test thoroughly** to ensure nothing breaks

**Example Migration:**

```python
# Before
class OldModel(BaseModel):
    user_id: str
    created_at: datetime

# After
class NewModel(CamelModel):
    user_id: str  # Keep snake_case internally
    created_at: datetime  # Auto-converts to camelCase in JSON
```

---

## Tools and Linting

### Python
- **Formatter:** `black` (line length: 88)
- **Linter:** `ruff`
- **Type Checker:** `mypy`

### TypeScript
- **Formatter:** `prettier`
- **Linter:** `eslint`
- **Type Checker:** Built-in TypeScript compiler

### Pre-commit Hooks
Set up pre-commit hooks to enforce standards:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

---

## Questions?

If you have questions about these standards or need clarification, please:

1. Check existing code examples in the repository
2. Review the `CamelModel` implementation in `backend/api/models.py`
3. Ask in team discussions or code reviews

**Remember: Consistency is key! Following these standards makes the codebase more maintainable for everyone.**
