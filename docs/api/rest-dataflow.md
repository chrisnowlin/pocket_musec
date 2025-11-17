# REST Dataflow Harmonization

This document describes the harmonized REST API contracts introduced to standardize data flow between frontend and backend.

## Overview

The REST dataflow harmonization introduces standardized response formats and event schemas to improve consistency, reduce frontend parsing complexity, and enable better error handling across all API endpoints.

## Key Changes

### 1. Field Normalization

All API responses now use camelCase field names and structured data types:

- **Sessions**: `selectedStandards` are arrays of objects instead of comma-separated strings
- **Drafts**: `selectedObjectives` are properly structured arrays
- **Presentations**: Status metadata uses consistent camelCase naming

**Before:**
```json
{
  "selected_standards": "K.CC.1,K.CC.2",
  "selected_objectives": "obj1,obj2"
}
```

**After:**
```json
{
  "selectedStandards": [
    {
      "id": "K.CC.1",
      "code": "K.CC.1",
      "grade": "Kindergarten",
      "title": "Know number names and the count sequence"
    }
  ],
  "selectedObjectives": ["obj1", "obj2"]
}
```

### 2. Dashboard Aggregation Endpoint

New `/api/workspace/dashboard` endpoint provides consolidated workspace data in a single request:

```http
GET /api/workspace/dashboard?include=sessions,drafts,presentations
```

**Response:**
```json
{
  "sessions": [...],
  "drafts": {
    "count": 5,
    "recent": [...]
  },
  "presentations": {
    "activeJobs": 2,
    "recentJobs": [...]
  },
  "stats": {
    "totalLessons": 15,
    "totalPresentations": 8
  },
  "lastUpdated": "2025-11-16T10:30:00Z"
}
```

### 3. Standardized Streaming Events

All Server-Sent Events (SSE) now follow a consistent structure:

```json
{
  "type": "delta|status|persisted|complete|error|progress",
  "payload": {
    // Type-specific data
  },
  "meta": {
    // Optional metadata
  },
  "timestamp": "2025-11-16T10:30:00Z"
}
```

#### Event Types

- **`delta`**: Incremental content updates
  ```json
  {
    "type": "delta",
    "payload": {
      "text": "Additional content..."
    }
  }
  ```

- **`status`**: Progress status messages
  ```json
  {
    "type": "status",
    "payload": {
      "message": "Processing your request..."
    }
  }
  ```

- **`persisted`**: Confirmation of data persistence
  ```json
  {
    "type": "persisted",
    "payload": {
      "message": "Conversation saved successfully",
      "sessionUpdated": true
    }
  }
  ```

- **`complete`**: Final response with complete data
  ```json
  {
    "type": "complete",
    "payload": {
      "response": "Complete response text",
      "lesson": {...},
      "session": {...}
    }
  }
  ```

- **`error`**: Error information
  ```json
  {
    "type": "error",
    "payload": {
      "message": "Processing failed",
      "code": "PROCESSING_ERROR",
      "retryRecommended": true
    }
  }
  ```

### 4. Job Status Envelope

Background job statuses (presentations, exports, etc.) use a standardized envelope:

```http
GET /api/presentations/jobs/{job_id}
```

**Response:**
```json
{
  "status": "pending|running|completed|failed|cancelled",
  "progress": {
    "completionPercentage": 75,
    "step": "Generating slides",
    "slideCount": 12,
    "processingTimeSeconds": 45
  },
  "retryAfter": 30,
  "error": {
    "code": "GENERATION_ERROR",
    "message": "Failed to generate slide 10",
    "retryRecommended": true
  },
  "meta": {
    "jobId": "abc-123",
    "lessonId": "lesson-456",
    "style": "modern",
    "createdAt": "2025-11-16T10:25:00Z"
  },
  "timestamp": "2025-11-16T10:30:00Z"
}
```

### 5. Ingestion Response Envelope

All ingestion endpoints (file uploads, image processing, embedding generation) return standardized responses:

```json
{
  "status": "success|error|partial|pending",
  "message": "Operation result message",
  "data": {
    // Original response data
  },
  "errors": [
    {
      "message": "File xyz.jpg failed",
      "code": "INVALID_FORMAT",
      "filePath": "xyz.jpg"
    }
  ],
  "meta": {
    "errorType": "validation|file_processing|network_error",
    "operationType": "single_upload|batch_upload|generation",
    "userId": "user-123"
  },
  "timestamp": "2025-11-16T10:30:00Z"
}
```

#### Status Types

- **`success`**: Operation completed successfully
- **`error`**: Operation failed completely
- **`partial`**: Batch operation with mixed results
- **`pending`**: Background processing started

## Migration Guide

### Frontend Migration

1. **Use Streaming Parser**:
   ```typescript
   import { parseEventStream, StreamingEventHandlers } from '../lib/streaming';

   const handlers: StreamingEventHandlers = {
     onDelta: (text) => updateContent(text),
     onStatus: (message) => updateStatus(message),
     onComplete: (payload) => finalizeResponse(payload),
     onError: (message) => showError(message)
   };

   await parseEventStream(response, handlers);
   ```

2. **Use Ingestion Service**:
   ```typescript
   import { IngestionService } from '../services/ingestionService';

   const response = await IngestionService.uploadImage(file);
   if (IngestionService.isSuccessful(response)) {
     const data = IngestionService.extractData(response);
   }
   ```

3. **Use Dashboard Endpoint**:
   ```typescript
   const dashboard = await api.get('/workspace/dashboard');
   // Contains sessions, drafts, presentations, and stats
   ```

### Backend Usage

1. **Create Streaming Events**:
   ```python
   from backend.models.streaming_schema import create_delta_event, emit_stream_event

   yield emit_stream_event(create_delta_event("Hello, world!"))
   ```

2. **Create Job Status Envelope**:
   ```python
   from backend.models.streaming_schema import create_job_status_envelope

   return create_job_status_envelope(
       status="completed",
       progress={"completion_percentage": 100},
       meta={"job_id": job_id}
   )
   ```

3. **Create Ingestion Response**:
   ```python
   from backend.models.ingestion_schema import create_success_response

   return create_success_response(
       message="File uploaded successfully",
       data=upload_data,
       meta={"file_type": "image"}
   ).to_dict()
   ```

## Error Handling

### Standardized Error Structure

All API errors follow this structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "user_message": "Human-readable error description",
    "technical_message": "Technical error details",
    "retry_recommended": true|false,
    "retry_after_seconds": 30
  },
  "timestamp": "2025-11-16T10:30:00Z",
  "request_id": "req-123"
}
```

### HTTP Status Mapping

- **200**: Success
- **400**: Validation/Client error
- **401**: Authentication required
- **403**: Access denied
- **404**: Resource not found
- **408**: Request timeout
- **429**: Rate limited
- **500**: Internal server error
- **503**: Service unavailable
- **507**: Insufficient storage

## Best Practices

### Frontend

1. **Use provided parsers** instead of manual SSE chunk parsing
2. **Check response status** using utility functions
3. **Handle retry recommendations** from error responses
4. **Use dashboard endpoint** for initial page load
5. **Normalize legacy responses** using ingestion service utilities

### Backend

1. **Use helper functions** for creating standardized responses
2. **Include meaningful metadata** in all responses
3. **Set appropriate HTTP status codes**
4. **Provide retry guidance** in error responses
5. **Maintain backward compatibility** through data envelope structure

## OpenAPI Documentation

The harmonized endpoints are automatically documented in the OpenAPI specification at `/api/docs`. Key changes:

- **Response models** updated to use standardized schemas
- **Examples** included for each endpoint
- **Error schemas** documented
- **Migration notes** in descriptions

## Testing

### Backend Tests

```python
# Test streaming events
def test_chat_streaming_events():
    response = client.post("/sessions/123/messages/stream", json={...})
    chunks = response.text.split("\n\n")

    for chunk in chunks:
        if chunk.startswith("data:"):
            event = parse_sse_chunk(chunk)
            assert event.type in ["delta", "status", "persisted", "complete"]

# Test ingestion envelope
def test_image_upload_envelope():
    response = client.post("/images/upload", files={"file": test_image})
    assert response.json()["status"] in ["success", "error"]
    assert "timestamp" in response.json()
```

### Frontend Tests

```typescript
// Test streaming parser
test('handles streaming events correctly', async () => {
  const mockResponse = createMockResponse(chunks);
  const handlers = {
    onDelta: jest.fn(),
    onComplete: jest.fn()
  };

  await parseEventStream(mockResponse, handlers);
  expect(handlers.onDelta).toHaveBeenCalled();
  expect(handlers.onComplete).toHaveBeenCalled();
});

// Test ingestion parsing
test('parses ingestion responses', () => {
  const legacyResponse = { id: '123', filename: 'test.jpg' };
  const standardized = IngestionService.parseStandardizedResponse(legacyResponse);

  expect(standardized.status).toBe('success');
  expect(standardized.data).toEqual(legacyResponse);
});
```

## Future Considerations

1. **Version Support**: Future API versions can be introduced without breaking changes
2. **Rate Limiting**: Standardized retry information enables smart client throttling
3. **Monitoring**: Consistent error formats simplify error tracking and alerting
4. **Caching**: Standardized metadata supports better caching strategies
5. **Offline Support**: Predictable response structures enable better offline handling

This harmonization provides a foundation for more robust frontend applications and clearer API contracts across the entire PocketMusec platform.