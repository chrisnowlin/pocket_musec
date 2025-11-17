# Comprehensive Error Handling System for Presentation Generation

This guide documents the comprehensive error handling system implemented across the presentation generation pipeline, from backend services to frontend components.

## Overview

The error handling system provides:
- **Structured error types** for different failure scenarios
- **User-friendly messages** with actionable suggestions
- **Automatic retry logic** with exponential backoff
- **Graceful degradation** and fallback options
- **Detailed logging** for monitoring and debugging
- **Error recovery strategies** specific to error types

## Backend Error Handling

### Error Types

Located in `/backend/services/presentation_errors.py`:

```python
class PresentationErrorCode(str, Enum):
    # Lesson-related errors
    LESSON_NOT_FOUND = "lesson_not_found"
    LESSON_ACCESS_DENIED = "lesson_access_denied"
    LESSON_INVALID_FORMAT = "lesson_invalid_format"
    LESSON_PARSE_FAILED = "lesson_parse_failed"

    # LLM-related errors
    LLM_TIMEOUT = "llm_timeout"
    LLM_RATE_LIMITED = "llm_rate_limited"
    LLM_UNAVAILABLE = "llm_unavailable"
    LLM_QUOTA_EXCEEDED = "llm_quota_exceeded"
    LLM_CONTENT_FILTERED = "llm_content_filtered"
    LLM_INVALID_RESPONSE = "llm_invalid_response"

    # Export-related errors
    EXPORT_PPTX_FAILED = "export_pptx_failed"
    EXPORT_PDF_FAILED = "export_pdf_failed"
    EXPORT_JSON_FAILED = "export_json_failed"
    EXPORT_MARKDOWN_FAILED = "export_markdown_failed"
    EXPORT_PERMISSION_DENIED = "export_permission_denied"
    EXPORT_STORAGE_FAILED = "export_storage_failed"

    # Job system errors
    JOB_NOT_FOUND = "job_not_found"
    JOB_ACCESS_DENIED = "job_access_denied"
    JOB_TIMEOUT = "job_timeout"
    JOB_CANCELLED = "job_cancelled"
    JOB_ALREADY_RUNNING = "job_already_running"

    # Validation errors
    VALIDATION_FAILED = "validation_failed"
    INVALID_STYLE = "invalid_style"
    INVALID_TIMEOUT = "invalid_timeout"
    INVALID_EXPORT_FORMAT = "invalid_export_format"

    # System errors
    DATABASE_ERROR = "database_error"
    NETWORK_ERROR = "network_error"
    PERMISSION_DENIED = "permission_denied"
    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
```

### Service Layer Error handling

The `PresentationService` class in `/backend/services/presentation_service.py` includes:

- **Input validation** with structured error responses
- **Graceful fallback** for LLM failures (uses scaffold slides)
- **Export error isolation** (export failures don't crash generation)
- **Comprehensive error logging** with context
- **Automatic recovery** attempts where possible

### Job System Error Handling

The job system in `/backend/services/presentation_jobs.py` provides:

- **Retry logic** with configurable attempts and delays
- **Timeout enforcement** using ThreadPoolExecutor
- **Graceful shutdown** handling
- **Job cancellation** for pending and running jobs
- **Health metrics** for monitoring system health

### API Layer Error Handling

The API endpoints in `/backend/api/routes/presentations.py` include:

- **HTTP status code mapping** appropriate to error types
- **Structured error responses** with recovery information
- **Request validation** with detailed error messages
- **Error context logging** for monitoring

## Frontend Error Handling

### Error Handler Service

Located in `/frontend/src/errors/presentationErrors.ts`:

```typescript
export class PresentationErrorHandler {
  handleError(error: any, context?: Record<string, any>): PresentationError | null
  getRecoveryActions(error: PresentationError): ErrorRecoveryAction[]
  scheduleRetry(key: string, maxRetries?: number, baseDelay?: number): Promise<void>
  cancelRetry(key: string): void
  isRecoverable(error: PresentationError): boolean
}
```

### API Client with Error Handling

The enhanced API client in `/frontend/src/services/presentationApiClient.ts` provides:

- **Automatic error conversion** to structured types
- **Retry logic with exponential backoff**
- **Progress tracking** for long-running operations
- **Fallback export formats**
- **Job polling with error recovery**

### Error Boundaries

React error boundaries in `/frontend/src/components/PresentationErrorBoundary.tsx`:

- **Catch unhandled exceptions** in component trees
- **Display user-friendly error messages**
- **Provide recovery actions** specific to error types
- **Development mode debug information**
- **Component fallback options**

### Enhanced Components

Updated components like `/frontend/src/components/unified/PresentationViewer.tsx` include:

- **Error-aware export functionality** with fallbacks
- **Progress indicators** for long operations
- **User-friendly error messages** with action buttons
- **Retry mechanisms** with intelligent conditions
- **Error state management** and clearing

## Error Scenarios and Recovery

### Lesson Not Found
- **Message:** "Lesson '{id}' could not be found. Please check the lesson ID and try again."
- **Actions:** [Verify lesson, Check permissions, Contact support if needed]
- **Retry:** No (user action required)

### LLM Timeout
- **Message:** "The presentation generation took too long. Try again with a longer timeout or disable AI polishing for faster results."
- **Actions:** [Retry, Increase timeout, Try without AI]
- **Retry:** Yes (after 5 seconds)

### Export Failed (PPTX/PDF)
- **Message:** "Failed to generate {format} export. Please try again or contact support if the issue persists."
- **Actions:** [Retry, Try JSON/MD export, Check disk space, Contact support]
- **Retry:** Yes (after 10 seconds)

### Job Timeout
- **Message:** "Presentation generation is taking too long. The job has been cancelled. Try with simpler content or a longer timeout."
- **Actions:** [Retry, Reduce content complexity, Increase timeout, Try without AI]
- **Retry:** Yes (after 15 seconds)

### Service Unavailable
- **Message:** "The {service} service is temporarily unavailable. Please try again later."
- **Actions:** [Wait and retry, Try alternative method, Contact support for ETA]
- **Retry:** Yes (after 30 seconds)

## Usage Examples

### Backend Service

```python
try:
    presentation = service.generate_presentation(
        lesson_id=lesson_id,
        user_id=user_id,
        use_llm_polish=True,
        timeout_seconds=30
    )
except PresentationError as e:
    logger.error(f"Presentation generation failed: {e.user_message}")

    if e.retry_recommended:
        # Implement retry logic
        time.sleep(e.retry_after_seconds or 5)
        # retry...
```

### Frontend Component

```typescript
import { usePresentationErrorHandler } from '../errors/presentationErrors';

function MyComponent() {
  const { handleError, getRecoveryActions } = usePresentationErrorHandler();
  const [error, setError] = useState<PresentationError | null>(null);

  const handleOperation = async () => {
    try {
      await apiClient.generatePresentation(lessonId, options);
    } catch (error: any) {
      const structuredError = handleError(error, { context: 'generation_page' });
      setError(structuredError);
    }
  };

  if (error) {
    const actions = getRecoveryActions(error);
    return <ErrorDisplay error={error} actions={actions} onDismiss={() => setError(null)} />;
  }

  return <button onClick={handleOperation}>Generate</button>;
}
```

### Error Boundary Integration

```typescript
import PresentationErrorBoundary from './PresentationErrorBoundary';

function App() {
  return (
    <PresentationErrorBoundary
      onError={(error) => { /* log to monitoring */ }}>
      <Router>
        <Routes>
          <Route path="/presentations" element={<PresentationPage />} />
          <Route path="/presentations/:id" element={<PresentationViewer />} />
        </Routes>
      </Router>
    </PresentationErrorBoundary>
  );
}
```

## Monitoring and Logging

### Error Logging Levels

- **CRITICAL:** Errors requiring immediate attention/escalation
- **ERROR:** System errors affecting functionality (database, services)
- **WARNING:** Expected failures with recovery paths (timeouts, rate limits)
- **INFO:** Normal error conditions and recovery attempts

### Metrics Collection

The system tracks:
- **Error rates** by type and endpoint
- **Retry success/failure rates**
- **Job completion/failure statistics**
- **Export format success rates**
- **Error recovery effectiveness**

### Monitoring Integration

Error data includes:
- **Error code and message**
- **User context (lesson_id, user_id)**
- **Operation context**
- **Recovery actions taken**
- **Retry attempts and outcomes**

## Best Practices

1. **Always use structured error types** instead of generic exceptions
2. **Provide user-friendly messages** with actionable guidance
3. **Include technical details** for debugging (in development)
4. **Log errors with context** for monitoring
5. **Implement retry logic** with exponential backoff
6. **Graceful degradation** when possible (scaffold without LLM)
7. **Clear error states** when issues are resolved
8. **Monitor error patterns** for system health

## Testing Error Handling

### Backend Tests

```python
def test_lesson_not_found_error():
    with pytest.raises(PresentationError) as exc_info:
        service.generate_presentation("invalid_lesson", "user_id")

    assert exc_info.value.code == PresentationErrorCode.LESSON_NOT_FOUND
    assert "could not be found" in exc_info.value.user_message
```

### Frontend Tests

```typescript
test('handles LLM timeout error', async () => {
  mockApiTimeout();

  render(<PresentationGenerator lesson={mockLesson} />);

  fireEvent.click(screen.getByText('Generate Presentation'));

  expect(await screen.findByText(/took too long/)).toBeInTheDocument();
  expect(screen.getByText('Try Without AI')).toBeInTheDocument();
});
```

## Future Enhancements

1. **Circuit breaker pattern** for repeatedly failing services
2. **Error analytics dashboard** for administrators
3. **Automated error reporting** to monitoring services
4. **Custom error types** for specific lesson content issues
5. **Predictive error prevention** based on content analysis
6. **Multi-language error messages** for internationalization

---

This comprehensive error handling system ensures that users receive clear, actionable feedback when things go wrong, while enabling developers to monitor, debug, and improve system reliability effectively.