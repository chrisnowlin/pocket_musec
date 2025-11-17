# PocketMusec API Documentation - Web-Only Architecture

Complete API reference for PocketMusec backend server with enhanced embeddings management and file storage system.

**Base URL:** `http://localhost:8000/api`

All authenticated endpoints require a valid JWT access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Important: camelCase Convention

**All API request and response payloads use camelCase property names.** This is a mandatory standard throughout the entire API.

```json
// ✅ CORRECT - Use camelCase
{
  "userId": "123",
  "gradeLevel": "Grade 3",
  "createdAt": "2025-11-17T00:00:00Z"
}

// ❌ INCORRECT - Do NOT use snake_case
{
  "user_id": "123",
  "grade_level": "Grade 3",
  "created_at": "2025-11-17T00:00:00Z"
}
```

See [CODING_STANDARDS.md](./CODING_STANDARDS.md) for complete details on naming conventions.

**Note:** PocketMusec now operates as a web-only application. All functionality is accessible through the web interface at `http://localhost:5173`. The API is provided for developers who want to integrate with PocketMusec programmatically.

## Authentication Endpoints

### POST /auth/register
Create a new user account (admin only).

**Request:**
```json
{
  "email": "teacher@example.com",
  "password": "Teacher123",
  "role": "teacher",
  "full_name": "Jane Doe",
  "processing_mode": "cloud"
}
```

**Response:**
```json
{
  "id": "usr_abc123",
  "email": "teacher@example.com",
  "role": "teacher",
  "full_name": "Jane Doe",
  "processing_mode": "cloud",
  "created_at": "2025-11-10T12:00:00Z"
}
```

**Authorization:** Admin only

---

### POST /auth/login
Authenticate and receive access/refresh tokens.

**Request:**
```json
{
  "email": "admin@example.com",
  "password": "Admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Rate Limit:** 5 requests per minute

---

### POST /auth/logout
Invalidate refresh token and end session.

**Request:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

**Authorization:** Required

---

### POST /auth/refresh
Exchange refresh token for new access token.

**Request:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

### GET /auth/me
Get current user information.

**Response:**
```json
{
  "id": "usr_abc123",
  "email": "admin@example.com",
  "role": "admin",
  "full_name": "Admin User",
  "processing_mode": "cloud",
  "created_at": "2025-11-01T10:00:00Z"
}
```

**Authorization:** Required

---

### PUT /auth/password
Change current user's password.

**Request:**
```json
{
  "current_password": "OldPass123",
  "new_password": "NewPass456"
}
```

**Response:**
```json
{
  "message": "Password updated successfully"
}
```

**Authorization:** Required

---

## User Management (Admin Only)

### GET /users
List all users.

**Query Parameters:**
- `skip` (int): Number of users to skip (default: 0)
- `limit` (int): Maximum users to return (default: 100)

**Response:**
```json
{
  "users": [
    {
      "id": "usr_abc123",
      "email": "admin@example.com",
      "role": "admin",
      "full_name": "Admin User",
      "processing_mode": "cloud",
      "created_at": "2025-11-01T10:00:00Z"
    }
  ],
  "total": 1
}
```

**Authorization:** Admin only

---

### GET /users/{user_id}
Get details for a specific user.

**Response:**
```json
{
  "id": "usr_abc123",
  "email": "teacher@example.com",
  "role": "teacher",
  "full_name": "Jane Doe",
  "processing_mode": "local",
  "created_at": "2025-11-05T14:30:00Z"
}
```

**Authorization:** Admin only

---

### DELETE /users/{user_id}
Delete a user account.

**Response:**
```json
{
  "message": "User deleted successfully"
}
```

**Authorization:** Admin only

---

## Image Processing

### POST /images
Upload a single image for processing.

**Request:** `multipart/form-data`
- `file` (file): Image file (PNG, JPEG, GIF, WebP, max 10MB)
- `processing_mode` (string, optional): "cloud" or "local" (default: user's preference)
- `vision_prompt` (string, optional): Custom prompt for vision AI

**Response:**
```json
{
  "id": "img_xyz789",
  "filename": "sheet_music.png",
  "uploaded_at": "2025-11-10T15:00:00Z",
  "ocr_text": "Allegro moderato\nC Major Scale...",
  "vision_analysis": "This sheet music shows a C major scale in 4/4 time...",
  "file_size": 524288,
  "mime_type": "image/png",
  "user_id": "usr_abc123"
}
```

**Authorization:** Required

---

### POST /images/batch
Upload multiple images.

**Request:** `multipart/form-data`
- `files` (file[]): Multiple image files
- `processing_mode` (string, optional): "cloud" or "local"

**Response:**
```json
{
  "results": [
    {
      "filename": "image1.png",
      "success": true,
      "image": { /* image object */ }
    },
    {
      "filename": "image2.png",
      "success": false,
      "error": "File too large"
    }
  ]
}
```

**Authorization:** Required

---

### GET /images
List user's uploaded images.

**Query Parameters:**
- `skip` (int): Number of images to skip (default: 0)
- `limit` (int): Maximum images to return (default: 50)

**Response:**
```json
{
  "images": [
    {
      "id": "img_xyz789",
      "filename": "sheet_music.png",
      "uploaded_at": "2025-11-10T15:00:00Z",
      "ocr_text": "...",
      "vision_analysis": "...",
      "file_size": 524288,
      "mime_type": "image/png"
    }
  ],
  "total": 1
}
```

**Authorization:** Required

---

### GET /images/search
Search images by content.

**Query Parameters:**
- `query` (string): Search query (searches filename, OCR text, vision analysis)
- `limit` (int): Maximum results (default: 20)

**Response:**
```json
{
  "results": [
    {
      "id": "img_xyz789",
      "filename": "sheet_music.png",
      "match_score": 0.95,
      "ocr_text": "...",
      "vision_analysis": "..."
    }
  ]
}
```

**Authorization:** Required

---

### GET /images/{image_id}
Get details for a specific image.

**Response:**
```json
{
  "id": "img_xyz789",
  "filename": "sheet_music.png",
  "uploaded_at": "2025-11-10T15:00:00Z",
  "ocr_text": "Allegro moderato\nC Major Scale...",
  "vision_analysis": "This sheet music shows a C major scale...",
  "file_size": 524288,
  "mime_type": "image/png",
  "user_id": "usr_abc123"
}
```

**Authorization:** Required (owner or admin)

---

### DELETE /images/{image_id}
Delete an image.

**Response:**
```json
{
  "message": "Image deleted successfully"
}
```

**Authorization:** Required (owner or admin)

---

### GET /images/storage/info
Get storage usage information.

**Response:**
```json
{
  "total_images": 15,
  "total_size_bytes": 52428800,
  "total_size_mb": 50.0,
  "quota_mb": 5120,
  "used_percentage": 0.98
}
```

**Authorization:** Required

---

## Settings

### GET /settings/processing-modes
List available processing modes.

**Response:**
```json
{
  "modes": [
    {
      "mode": "cloud",
      "display_name": "Cloud Processing",
      "description": "Fast processing using Chutes AI API",
      "is_available": true,
      "features": [
        "Fastest processing speed",
        "Latest AI models",
        "No local setup required"
      ]
    },
    {
      "mode": "local",
      "display_name": "Local Processing",
      "description": "Private processing using Ollama on your machine",
      "is_available": true,
      "features": [
        "Complete privacy",
        "Works offline",
        "No API costs"
      ]
    }
  ]
}
```

**Authorization:** Required

---

### POST /settings/processing-mode
Update user's processing mode preference.

**Request:**
```json
{
  "processing_mode": "local"
}
```

**Response:**
```json
{
  "message": "Processing mode updated to local",
  "processing_mode": "local"
}
```

**Authorization:** Required

---

### GET /settings/local-model-status
Check status of local Ollama model.

**Response:**
```json
{
  "is_installed": true,
  "model_name": "qwen2.5:8b",
  "model_size": "4.7GB",
  "is_running": true
}
```

Or if unavailable:
```json
{
  "is_installed": false,
  "model_name": "qwen2.5:8b",
  "is_running": false,
  "error": "Ollama service not running"
}
```

**Authorization:** Required

---

### POST /settings/download-local-model
Trigger download of local Ollama model.

**Response:**
```json
{
  "message": "Model download initiated",
  "model_name": "qwen2.5:8b",
  "estimated_size": "4.7GB"
}
```

**Note:** This initiates the download but returns immediately. Check status with `/settings/local-model-status`.

**Authorization:** Required

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid input: email is required"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid or expired token"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

- **General endpoints:** 60 requests per minute per user
- **Auth endpoints:** 5 requests per minute per IP
- **Image upload:** Subject to storage quota limits

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1699632000
```

---

## Authentication Flow

### Initial Login
1. POST `/auth/login` with email/password
2. Receive `access_token` (15min lifetime) and `refresh_token` (7 day lifetime)
3. Store both tokens securely (access token in memory, refresh token in httpOnly cookie)
4. Include access token in all subsequent requests: `Authorization: Bearer <token>`

### Token Refresh
1. When access token expires (401 response)
2. POST `/auth/refresh` with refresh token
3. Receive new access token
4. Retry original request with new token

### Logout
1. POST `/auth/logout` with refresh token
2. Refresh token is invalidated
3. Clear stored tokens

---

## Image Upload Best Practices

1. **File Size:** Keep images under 10MB. Compress large images before upload.
2. **Batch Uploads:** Use `/images/batch` for multiple files to reduce overhead.
3. **Storage Management:** Monitor storage with `/images/storage/info` and delete unused images.
4. **Processing Mode:** Use "cloud" for speed, "local" for privacy.
5. **Vision Prompts:** Provide specific prompts for better vision AI analysis (e.g., "Identify the key signature and time signature").

---

## Security Considerations

1. **HTTPS Required:** Always use HTTPS in production
2. **Token Storage:** Never store tokens in localStorage (vulnerable to XSS). Use httpOnly cookies or memory.
3. **CORS:** Ensure `CORS_ORIGINS` is configured correctly
4. **Password Requirements:** Minimum 8 characters, mix of letters and numbers recommended
5. **Rate Limiting:** Respect rate limits to avoid being blocked
6. **File Upload:** Only upload trusted images. Server validates file types but malicious files may still pose risks.

---

## Websocket Support (Future)

Websocket endpoints for real-time updates are planned for future releases:
- `/ws/images/upload` - Real-time upload progress
- `/ws/generation` - Streaming lesson generation

Currently not implemented in Milestone 3.

---

## Embeddings Management

The embeddings system provides comprehensive semantic search and management capabilities for music education standards and objectives.

### GET /embeddings/stats
Get statistics about embeddings in the database with caching support.

**Response:**
```json
{
  "standard_embeddings": 125,
  "objective_embeddings": 48,
  "embedding_dimension": 1536,
  "last_updated": "2025-11-12T15:30:00Z"
}
```

**Authorization:** Required

**Notes:**
- Response is cached for 5 minutes to improve performance
- Use `force_refresh=true` query parameter to bypass cache

---

### POST /embeddings/generate
Generate embeddings for all standards and objectives with background processing.

**Request:**
```json
{
  "force": false,
  "batch_size": 10
}
```

**Response:**
```json
{
  "success": 0,
  "failed": 0,
  "skipped": 0,
  "message": "Embedding generation started in background",
  "task_id": "gen_abc123"
}
```

**Authorization:** Required

**Notes:**
- Generation runs in background to avoid blocking
- Progress can be tracked with the task_id
- Large datasets are processed in batches

---

### GET /embeddings/generate/progress
Get progress of ongoing embedding generation.

**Query Parameters:**
- `task_id` (string, optional): Specific task ID to track

**Response:**
```json
{
  "status": "running",
  "progress": 75,
  "message": "Generating embeddings...",
  "current_item": "Processing standard 3.M.P.5",
  "estimated_remaining": "2 minutes"
}
```

**Authorization:** Required

---

### POST /embeddings/search
Search for standards using semantic similarity with advanced pagination and filtering.

**Request:**
```json
{
  "query": "musical scales and patterns",
  "grade_level": "Grade 3",
  "strand_code": "M",
  "limit": 10,
  "threshold": 0.5,
  "offset": 0
}
```

**Response:**
```json
{
  "results": [
    {
      "standard_id": "K.M.P.1",
      "grade_level": "Kindergarten",
      "strand_code": "M",
      "strand_name": "Musical Expression",
      "standard_text": "Demonstrate musical expression through movement...",
      "similarity": 0.87,
      "objectives": [
        {
          "objective_id": "K.M.P.1.1",
          "text": "Demonstrate steady beat through movement"
        }
      ]
    }
  ],
  "total_count": 25,
  "limit": 10,
  "offset": 0,
  "has_next": true,
  "has_previous": false,
  "search_time": "0.05s"
}
```

**Authorization:** Required

**Notes:**
- Supports natural language queries
- Pagination prevents performance issues with large result sets
- Similarity scores range from 0.0 to 1.0
- Results are sorted by relevance

---

### DELETE /embeddings/clear
Clear all embeddings from the database with confirmation.

**Request:**
```json
{
  "confirm": true,
  "reason": "User requested cleanup"
}
```

**Response:**
```json
{
  "message": "All embeddings deleted from database",
  "deleted_count": 173,
  "operation_time": "0.2s"
}
```

**Authorization:** Required

**Notes:**
- Requires explicit confirmation to prevent accidental deletion
- Operation is logged for audit purposes
- Cannot be undone

---

### POST /embeddings/batch
Perform batch operations on embeddings with progress tracking.

**Request:**
```json
{
  "operation": "regenerate",
  "filters": {
    "grade_level": "Grade 3",
    "strand_code": "M"
  }
}
```

**Response:**
```json
{
  "success": 0,
  "failed": 0,
  "skipped": 0,
  "message": "Batch regenerate started in background",
  "task_id": "batch_def456"
}
```

**Authorization:** Required

**Available Operations:**
- `regenerate`: Regenerate embeddings for filtered items
- `delete`: Delete embeddings for filtered items
- `refresh`: Refresh embeddings cache
- `validate`: Validate embedding integrity

---

### GET /embeddings/usage/stats
Get comprehensive usage statistics for embeddings operations.

**Response:**
```json
{
  "total_searches": 42,
  "total_generations": 3,
  "searches_this_week": 12,
  "generations_this_week": 1,
  "last_search": "2025-11-12T10:30:00Z",
  "last_generation": "2025-11-10T15:45:00Z",
  "popular_queries": [
    {"query": "rhythm activities", "count": 8},
    {"query": "music composition", "count": 5}
  ],
  "weekly_trends": {
    "searches": [5, 8, 12, 7, 9],
    "generations": [0, 1, 0, 0, 0]
  }
}
```

**Authorization:** Required

---

### POST /embeddings/usage/track/search
Track a search operation for analytics.

**Query Parameters:**
- `query` (string): Search query
- `result_count` (int): Number of results returned
- `filters_applied` (boolean): Whether filters were used

**Response:**
```json
{
  "message": "Search usage tracked",
  "tracked_at": "2025-11-12T10:30:00Z"
}
```

**Authorization:** Required

---

### POST /embeddings/usage/track/generation
Track a generation operation for analytics.

**Query Parameters:**
- `success` (int): Number of successfully generated embeddings
- `failed` (int): Number of failed generations
- `skipped` (int): Number of skipped generations
- `operation_type` (string): Type of generation (full, batch, filtered)

**Response:**
```json
{
  "message": "Generation usage tracked",
  "tracked_at": "2025-11-10T15:45:00Z"
}
```

**Authorization:** Required

---

### GET /embeddings/stats/export/csv
Export embedding statistics as CSV file with proper headers.

**Query Parameters:**
- `include_usage` (boolean): Include usage statistics (default: false)
- `date_range` (string): Date range filter (optional)

**Response:** CSV file download with headers:
```
timestamp,standard_embeddings,objective_embeddings,embedding_dimension,last_updated
2025-11-12T15:30:00Z,125,48,1536,2025-11-12T15:30:00Z
```

**Authorization:** Required

---

### GET /embeddings/stats/export/json
Export embedding statistics as JSON with metadata.

**Query Parameters:**
- `include_usage` (boolean): Include usage statistics (default: false)
- `date_range` (string): Date range filter (optional)

**Response:**
```json
{
  "export_timestamp": "2025-11-12T15:30:00Z",
  "export_version": "1.0",
  "embedding_statistics": {
    "standard_embeddings": 125,
    "objective_embeddings": 48,
    "embedding_dimension": 1536,
    "last_updated": "2025-11-12T15:30:00Z"
  },
  "usage_statistics": {
    "total_searches": 42,
    "total_generations": 3,
    "searches_this_week": 12,
    "generations_this_week": 1,
    "last_search": "2025-11-12T10:30:00Z",
    "last_generation": "2025-11-10T15:45:00Z"
  }
}
```

**Authorization:** Required

---

### GET /embeddings/usage/export/csv
Export usage statistics as CSV file with detailed analytics.

**Query Parameters:**
- `date_range` (string): Date range filter (optional)
- `include_trends` (boolean): Include weekly trends (default: true)

**Response:** CSV file download with headers:
```
date,total_searches,total_generations,searches_this_week,generations_this_week,last_search,last_generation
2025-11-12,42,3,12,1,2025-11-12T10:30:00Z,2025-11-10T15:45:00Z
```

**Authorization:** Required

---

### GET /embeddings/texts
List all prepared embedding text files with metadata.

**Response:**
```json
{
  "standards": [
    {
      "item_id": "K.M.P.1",
      "grade_level": "Kindergarten",
      "strand_code": "M",
      "text_length": 245,
      "last_prepared": "2025-11-10T12:00:00Z"
    }
  ],
  "objectives": [
    {
      "item_id": "K.M.P.1.1",
      "parent_standard": "K.M.P.1",
      "text_length": 89,
      "last_prepared": "2025-11-10T12:05:00Z"
    }
  ],
  "total_count": 173
}
```

**Authorization:** Required

---

### GET /embeddings/texts/{item_id}
Show prepared text for a specific standard or objective with context.

**Query Parameters:**
- `item_type` (string): "standard" or "objective" (default: "standard")
- `include_context` (boolean): Include related items (default: false)

**Response:**
```json
{
  "text": "Demonstrate musical expression through movement...",
  "item_id": "K.M.P.1",
  "item_type": "standard",
  "metadata": {
    "grade_level": "Kindergarten",
    "strand_code": "M",
    "text_length": 245,
    "last_prepared": "2025-11-10T12:00:00Z"
  },
  "related_objectives": [
    {
      "objective_id": "K.M.P.1.1",
      "text": "Demonstrate steady beat through movement"
    }
  ]
}
```

**Authorization:** Required

---

### DELETE /embeddings/texts/clear
Clear all prepared text files with confirmation.

**Request:**
```json
{
  "confirm": true,
  "reason": "User requested cleanup"
}
```

**Response:**
```json
{
  "message": "All prepared text files deleted",
  "deleted_count": 173,
  "operation_time": "0.15s"
}
```

**Authorization:** Required

---

## Embeddings Best Practices

1. **Pagination:** Use pagination for search results to improve performance
2. **Batch Operations:** Use batch operations for large-scale changes
3. **Usage Monitoring:** Monitor usage statistics to understand system utilization
4. **Export Data:** Use export features for backup and analysis
5. **Error Handling:** Implement proper retry logic with exponential backoff
6. **Accessibility:** Use ARIA labels and keyboard navigation support
7. **Caching:** Leverage server-side caching for statistics endpoint
8. **Virtual Scrolling:** Enable for large result sets in UI implementations

---

## Enhanced Features

The embeddings system includes several enhancements for improved usability and performance:

- **Advanced Pagination:** Efficient handling of large result sets with metadata
- **Virtual Scrolling:** Optional virtual scrolling for large result lists in the UI
- **Retry Logic:** Automatic retry with exponential backoff for failed requests
- **Usage Analytics:** Comprehensive usage tracking with trends and insights
- **Export Functionality:** Export statistics and usage data in multiple formats
- **Batch Operations:** Perform bulk operations on embeddings efficiently
- **Accessibility:** Full WCAG 2.1 AA compliance with ARIA support
- **Performance Optimization:** Server-side caching and efficient query patterns
- **Progress Tracking:** Real-time progress monitoring for long-running operations
- **Error Resilience:** Graceful error handling with user-friendly messages

---

## Web Search Configuration

Web search functionality is integrated into the lesson generation system and configured through environment variables. There are no direct web search endpoints, as the feature is automatically utilized during lesson generation.

### Configuration Options

Web search behavior is controlled through the following environment variables:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `BRAVE_SEARCH_API_KEY` | string | Required | Brave Search API authentication key |
| `BRAVE_SEARCH_CACHE_TTL` | integer | 3600 | Cache time-to-live in seconds |
| `BRAVE_SEARCH_MAX_CACHE_SIZE` | integer | 100 | Maximum number of cached searches |
| `BRAVE_SEARCH_TIMEOUT` | integer | 30 | API request timeout in seconds |
| `BRAVE_SEARCH_EDUCATIONAL_ONLY` | boolean | true | Filter to educational domains only |
| `BRAVE_SEARCH_MIN_RELEVANCE_SCORE` | float | 0.5 | Minimum relevance score threshold |
| `CITATION_AUTO_INCLUDE` | boolean | true | Automatically include citations in generated lessons |
| `CITATION_FORMAT` | string | "footnote" | Citation format: "footnote" or "parenthetical" |

### Web Search Integration in Lesson Generation

Web search functionality is automatically integrated into the lesson generation process through existing session endpoints. When web search is enabled and configured, lesson generation responses include enhanced web search context.

#### Enhanced Lesson Response Format

When web search is enabled and successful, the lesson response includes:

```json
{
  "lesson_content": "Generated lesson with web-enhanced content and proper citations...",
  "web_search_summary": {
    "query": "grade 3 rhythm music education",
    "results_found": 5,
    "educational_sources": 3,
    "relevance_scores": [0.87, 0.82, 0.78, 0.74, 0.69],
    "search_time": 0.8
  },
  "citations_included": true,
  "bibliography_generated": true,
  "generation_time": 4.2,
  "cache_hit": false
}
```

#### Citation System Integration

The lesson generation system automatically includes proper citations when web search content is used:

**Citation Features:**
- **Inline Citations**: Web sources are cited inline using format `[Web Source: URL]` or citation numbers `[1]`, `[2]`, etc.
- **Bibliography Section**: Generated lessons include a comprehensive "Citations" section listing all web sources
- **Clickable URLs**: Frontend renders citation URLs as clickable hyperlinks that open in new tabs
- **Source Attribution**: Clear distinction between database sources and web search sources

**Citation Format Examples:**
```
Students will learn rhythm patterns using quarter and eighth notes [Web Source: https://www.teachingmusic.org/rhythm].

Interactive tools help reinforce musical concepts [Web Source: www.musictech.com/tools].

## Citations

1. [Web Source: https://www.teachingmusic.org/rhythm] - Comprehensive guide for teaching rhythm patterns
2. [Web Source: www.musictech.com/tools] - Interactive tools for rhythm composition
3. [Web Source: https://musiceducation.org/research] - Research-based pedagogy for music education
```

### Web Search Error Handling

The API gracefully handles web search failures:

#### Search Disabled Response
```json
{
  "lesson_content": "Generated lesson using RAG only...",
  "web_search_summary": {
    "status": "disabled",
    "reason": "API key not configured"
  },
  "fallback_mode": "rag_only"
}
```

#### Search Failed Response
```json
{
  "lesson_content": "Generated lesson with RAG fallback...",
  "web_search_summary": {
    "status": "failed",
    "reason": "API timeout",
    "fallback_used": true
  },
  "generation_time": 3.4,
  "web_search_time": 30.0
}
```

---

## Web Search Best Practices

### API Usage Guidelines

1. **Configuration**: Set up `BRAVE_SEARCH_API_KEY` in environment variables
2. **Cache Optimization**: Configure appropriate TTL for your usage patterns
3. **Error Handling**: Implement fallback handling for web search failures
4. **Performance Monitoring**: Monitor search times and success rates

### Performance Optimization

1. **Cache Utilization**: Higher TTL reduces API calls but may sacrifice freshness
2. **Relevance Threshold**: Increase `BRAVE_SEARCH_MIN_RELEVANCE_SCORE` for higher quality results
3. **Educational Filtering**: Keep `BRAVE_SEARCH_EDUCATIONAL_ONLY=true` for educational content
4. **Timeout Configuration**: Adjust timeout based on network conditions

For detailed web search configuration and troubleshooting, see the [Web Search Integration Guide](WEB_SEARCH_INTEGRATION.md) and [Web Search Configuration](WEB_SEARCH_CONFIGURATION.md) documentation.

---
