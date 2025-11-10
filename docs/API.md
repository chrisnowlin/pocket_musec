# PocketMusec API Documentation - Milestone 3

Complete API reference for PocketMusec backend server.

**Base URL:** `http://localhost:8000/api`

All authenticated endpoints require a valid JWT access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

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
