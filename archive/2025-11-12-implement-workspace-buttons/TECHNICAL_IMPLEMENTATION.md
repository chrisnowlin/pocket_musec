# Technical Implementation Details

## Architecture Overview

The workspace buttons implementation follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                        │
├─────────────────────────────────────────────────────────────┤
│  UI Components    │  Custom Hooks    │  State Management   │
│  • DraftsModal    │  • useDrafts     │  • UnifiedPage      │
│  • TemplatesModal │  • useTemplates  │  • Modal States     │
│  • RightPanel     │  • useSession    │  • Event Handlers   │
├─────────────────────────────────────────────────────────────┤
│                    API Layer                               │
│  • axios client   │  Type Definitions │  Error Handling     │
│  • endpoint methods│  TypeScript interfaces │ Retry logic      │
├─────────────────────────────────────────────────────────────┤
│                    Backend (FastAPI)                       │
│  • Routes          │  Models           │  Database          │
│  • /api/drafts     │  Pydantic models  │  SQLite tables     │
│  • /api/templates  │  Request/Response │  Migrations        │
│  • /api/sessions   │  Validation       │  Relations         │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Patterns

### 1. Session Retry Flow
```
User Clicks Retry → RightPanel.onRetrySession() → useSession.retrySession() 
→ api.createSession() → Backend Session Creation → Frontend State Update 
→ UI Feedback → Auto-clear after 3 seconds
```

### 2. Draft Management Flow
```
Generate Lesson → Backend creates as draft → Frontend loads drafts list 
→ User selects draft → useDrafts.getDraft() → Load draft into lesson editor 
→ User can edit/delete → Backend CRUD operations
```

### 3. Template Management Flow
```
User saves lesson as template → useTemplates.createTemplateFromLesson() 
→ localStorage storage → UI updates template count → User can select template 
→ Load template settings into lesson editor → Pre-populate lesson fields
```

### 4. Conversation History Flow
```
Page Load → useSession.loadSessions() → Format as conversations 
→ Display in sidebar → User clicks conversation → loadConversation() 
→ Restore session state + messages → Update UI with historical context
```

## Key Implementation Decisions

### LocalStorage vs Database for Templates

**Decision:** Use localStorage for templates (v1)

**Rationale:**
- **Simplicity:** No backend storage needed initially
- **Performance:** Instant access without network calls
- **Offline Capability:** Templates available without server connection
- **Development Speed:** Faster implementation and testing

**Trade-offs:**
- **Device-specific:** Templates not shared between devices
- **Storage limits:** Browser localStorage limitations (~5-10MB)
- **Backup concerns:** User data backup responsibility

**Future Migration Path:**
```typescript
// Current localStorage implementation
const templates = localStorage.getItem('pocketmusec-templates')

// Future database implementation
const templates = await api.getTemplates()
```

### Draft Storage Strategy

**Decision:** Use existing `lessons` table with `is_draft` flag

**Rationale:**
- **Schema Simplicity:** No separate table needed
- **Data Consistency:** Drafts and lessons share same structure
- **Migration Simplicity:** Easy to convert draft to lesson
- **Query Efficiency:** Single table for all lesson-related data

**Implementation:**
```sql
-- Added column to distinguish drafts
ALTER TABLE lessons ADD COLUMN is_draft INTEGER DEFAULT 0;

-- Query for drafts only
SELECT * FROM lessons WHERE user_id = ? AND is_draft = 1;
```

### Session State Restoration

**Decision:** Store conversation state in database, restore on demand

**Rationale:**
- **Data Persistence:** Conversations survive page refreshes
- **User Experience:** Seamless continuation of previous sessions
- **State Integrity:** Complete session context restoration
- **Scalability:** Database storage scales with user base

## Database Schema Changes

### Version 5 Migration (Drafts Support)
```sql
-- Migration in backend/repositories/migrations.py
ALTER TABLE lessons ADD COLUMN is_draft INTEGER DEFAULT 0;

-- Update schema version tracking
INSERT INTO schema_version (version) VALUES (5);
```

### Template Storage (Future Migration)
```sql
-- Planned for v2 implementation
CREATE TABLE IF NOT EXISTS templates (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## Component Architecture

### Modal Component Pattern
```typescript
// Consistent modal structure across all new modals
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  isLoading: boolean;
  // Specific props per modal type
}

export default function ModalComponent({
  isOpen,
  onClose,
  isLoading,
  ...specificProps
}: ModalProps) {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="workspace-card rounded-2xl max-w-4xl w-full max-h-[80vh] p-6">
        {/* Modal content */}
      </div>
    </div>
  );
}
```

### Hook Pattern for Data Management
```typescript
// Consistent hook pattern across useDrafts and useTemplates
export function useResource<T>() {
  const [items, setItems] = useState<T[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const loadItems = useCallback(async () => {
    setIsLoading(true);
    try {
      const result = await api.getItems();
      setItems(result.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  // CRUD operations...
  
  return { items, isLoading, error, loadItems, ...operations };
}
```

## Error Handling Strategy

### Frontend Error Handling
```typescript
// Centralized error handling in hooks
const handleApiError = (error: any, defaultMessage: string) => {
  const message = error.response?.data?.detail || error.message || defaultMessage;
  setError(message);
  console.error(`${defaultName} operation failed:`, error);
};

// Retry logic for transient failures
const retryOperation = async (operation: () => Promise<any>, maxRetries = 3) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
};
```

### Backend Error Handling
```python
# Consistent error responses across API endpoints
@router.post("/{resource_id}", response_model=ResourceResponse)
async def create_resource(
    resource_id: str,
    request: ResourceCreateRequest,
    current_user: User = Depends(get_current_user),
) -> ResourceResponse:
    try:
        # Operation logic
        result = create_resource_logic(request, current_user.id)
        return result
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

## Performance Optimizations

### Frontend Optimizations
1. **Memoization:** `useCallback` for expensive computations
2. **Lazy Loading:** Load conversation content on demand
3. **Debouncing:** Debounced search and filter operations
4. **State Management:** Efficient state updates with immutability

### Backend Optimizations
1. **Database Indexes:** Optimized queries for draft and session retrieval
2. **Connection Pooling:** Efficient database connection management
3. **Response Compression:** gzip compression for API responses
4. **Caching Headers:** Appropriate cache headers for static data

## Security Considerations

### Authentication & Authorization
```python
# All endpoints protected with user authentication
@router.get("/drafts", response_model=List[DraftResponse])
async def list_drafts(
    current_user: User = Depends(get_current_user),  # Auth check
) -> List[DraftResponse]:
    # Only return drafts belonging to authenticated user
    lessons = lesson_repo.list_lessons_for_user(current_user.id, is_draft=True)
    return lessons
```

### Input Validation
```python
# Pydantic models for request validation
class DraftCreateRequest(BaseModel):
    session_id: str
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = None
```

### Data Sanitization
```typescript
// Frontend input sanitization
const sanitizeInput = (input: string): string => {
  return input.trim().substring(0, MAX_LENGTH);
};

// XSS protection for user-generated content
const sanitizeHtml = (content: string): string => {
  return DOMPurify.sanitize(content);
};
```

## Testing Strategy

### Frontend Testing
1. **Unit Tests:** Hook logic and utility functions
2. **Component Tests:** Modal rendering and interactions
3. **Integration Tests:** End-to-end user workflows
4. **Error Scenario Tests:** Network failures, API errors

### Backend Testing
1. **Unit Tests:** Repository layer and business logic
2. **API Tests:** Endpoint functionality and responses
3. **Database Tests:** Migration and data integrity
4. **Security Tests:** Authentication and authorization

## Monitoring & Observability

### Frontend Monitoring
```typescript
// Error tracking for production
const trackError = (error: Error, context: string) => {
  console.error(`[${context}] ${error.message}`, error);
  // Send to error tracking service (e.g., Sentry)
  if (process.env.NODE_ENV === 'production') {
    errorTracking.captureException(error, { context });
  }
};

// Performance monitoring
const trackPerformance = (operation: string, duration: number) => {
  if (process.env.NODE_ENV === 'production') {
    analytics.track('performance', { operation, duration });
  }
};
```

### Backend Monitoring
```python
# Request logging and timing
import time
import logging

logger = logging.getLogger(__name__)

def timed_endpoint(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.2f}s: {e}")
            raise
    return wrapper
```

## Deployment Considerations

### Database Migration Strategy
```python
# Safe migration with rollback capability
def migrate_with_rollback(conn: sqlite3.Connection, migration_func: callable):
    """Execute migration with automatic rollback on failure"""
    try:
        migration_func(conn)
        conn.commit()
        logger.info("Migration completed successfully")
    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed, rolled back: {e}")
        raise
```

### Feature Flags
```typescript
// Feature flag system for gradual rollout
const FEATURES = {
  DRAFT_MANAGEMENT: process.env.VITE_ENABLE_DRAFTS === 'true',
  TEMPLATE_SYSTEM: process.env.VITE_ENABLE_TEMPLATES === 'true',
  SESSION_RETRY: process.env.VITE_ENABLE_RETRY === 'true',
};

// Conditional feature rendering
{FEATURES.DRAFT_MANAGEMENT && (
  <DraftsModal {...draftsProps} />
)}
```

## Future Scalability Considerations

### Database Scaling
1. **Connection Pooling:** Prepare for multi-user concurrent access
2. **Query Optimization:** Optimize for large datasets
3. **Index Strategy:** Comprehensive indexing for performance
4. **Sharding Preparedness:** Design for horizontal scaling

### API Scaling
1. **Rate Limiting:** Implement per-user rate limits
2. **Caching Layer:** Redis for frequently accessed data
3. **Load Balancing:** Prepare for multi-instance deployment
4. **Async Processing:** Background jobs for heavy operations

### Frontend Scaling
1. **Code Splitting:** Lazy load components and features
2. **State Management:** Prepare for complex state scenarios
3. **Performance Budget:** Monitor bundle size and performance
4. **Progressive Enhancement:** Graceful degradation for older browsers

---

**Implementation Complexity:** 🟡 Medium-High  
**Maintainability:** 🟢 High  
**Scalability:** 🟢 High  
**Documentation Quality:** 🟢 Complete