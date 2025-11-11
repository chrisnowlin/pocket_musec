# Technical Design: Milestone 3 Advanced Features

## Context

Milestone 2 delivered a functional web interface with real-time lesson generation. Teachers can now access PocketMusec through their browsers, but face limitations:

1. **Visual content gap**: Music education materials often include sheet music, notation, and diagrams that cannot be ingested
2. **Source opacity**: Generated lessons lack attribution, making it difficult to verify or reference source materials
3. **Privacy concerns**: Schools with sensitive data need local processing options to comply with data protection policies
4. **Single-user limitation**: No authentication system prevents deployment in shared school environments

This milestone addresses these gaps by adding image processing, comprehensive citation tracking, processing mode flexibility, and multi-user authentication.

### Constraints

- Must maintain backward compatibility with Milestones 1 & 2
- Local model must run on typical teacher laptops (16GB RAM, Apple Silicon or modern GPU)
- Image storage must not exceed 5GB default quota
- Authentication must support typical school IT security policies
- Citation system must not significantly slow lesson generation

### Stakeholders

- K-12 music teachers (primary users)
- School IT administrators (security, deployment, user management)
- School administrators (usage monitoring, accountability)
- Privacy officers (data protection compliance)

## Goals / Non-Goals

### Goals

- Enable ingestion of image-based music education materials
- Provide transparent source attribution in all lessons
- Offer privacy-compliant local processing option
- Support multi-teacher deployments with proper isolation
- Maintain performance comparable to Milestone 2

### Non-Goals

- Real-time collaborative editing (defer to future)
- Mobile native apps (web-responsive only)
- Advanced OMR features (transposition, playback)
- LDAP/Active Directory integration (local accounts only)
- Offline-first architecture (defer to Milestone 4)

## Decisions

### Decision: Tesseract + Vision API for Image Processing

**Choice**: Tesseract OCR for text extraction, Chutes Vision API for content understanding
**Rationale**:
- Tesseract: Open source, mature, handles multiple languages, good music notation support with custom training
- Chutes Vision: Consistent with existing LLM provider, semantic understanding beyond OCR
- Local fallback: CLIP models provide vision embeddings in local-only mode
**Alternatives Considered**:
- Google Vision API: Excellent but vendor lock-in, cost concerns
- AWS Textract: Music notation support unclear, higher complexity
- Audiveris (OMR): Specialized for music but heavyweight, defer to future enhancement

### Decision: IEEE Citation Style (Initially)

**Choice**: IEEE-style inline numeric citations with full bibliography
**Rationale**:
- Familiar to education professionals
- Compact inline format `[1]` doesn't disrupt lesson flow
- Easy to parse and generate programmatically
- Clear distinction between sources
**Alternatives Considered**:
- APA: Verbose in-text citations, harder to read in lessons
- MLA: Less common in technical/education materials
- Custom format: Reinventing the wheel
**Future**: Add citation style selector (APA, MLA) in Milestone 4

### Decision: Ollama + Qwen3 8B for Local Mode

**Choice**: Ollama runtime with Qwen3 8B Instruct (GGUF Q4_K_M quantization)
**Rationale**:
- Ollama: Simple installation, automatic model management, wide OS support
- Qwen3 8B: Excellent performance/size ratio, strong instruction following
- Q4_K_M: Balanced quantization (quality vs. speed)
- 8B: Fits in 16GB RAM with room for OS and browser
**Alternatives Considered**:
- llama.cpp direct: More complex to integrate, no model management
- GPT4All: Limited model selection, less active development
- LocalAI: Heavyweight, more setup complexity
- Smaller models (3B): Quality too low for lesson generation
- Larger models (13B+): Won't fit in 16GB RAM constraint

### Decision: JWT-Based Authentication

**Choice**: JWT access tokens (short-lived) + refresh tokens (long-lived)
**Rationale**:
- Stateless: Scales well, no server-side session storage needed
- Standard: Well-understood, many libraries, good security practices
- Flexible: Easy to add claims (role, preferences)
- Mobile-ready: Works for future mobile apps
**Alternatives Considered**:
- Session cookies: Requires server-side storage, harder to scale
- OAuth2: Overkill for local deployment, complex setup
- Basic auth: Insecure, no expiration mechanism
**Security**:
- Access token: 15-minute expiration
- Refresh token: 7-day expiration, rotated on use
- Tokens stored in memory (not localStorage for XSS protection)
- HTTPS required in production

### Decision: SQLite User Table (No External Auth)

**Choice**: Local SQLite user management with bcrypt password hashing
**Rationale**:
- Simple: No external dependencies or network calls
- Sufficient: School deployments typically have <50 teachers
- Portable: Works with SQLite-based architecture
- Offline: No dependency on external auth servers
**Alternatives Considered**:
- LDAP/Active Directory: Complex integration, defer to M4
- OAuth (Google/Microsoft): Requires internet, privacy concerns
- SAML: Enterprise overkill for target audience
**Future Enhancement**: Add OAuth/LDAP as optional plugins in Milestone 4

### Decision: Per-User Processing Mode Preference

**Choice**: Store processing mode (cloud/local) per user, not globally
**Rationale**:
- Flexibility: One teacher can use cloud, another local
- Training: New users start with cloud, migrate to local
- Hardware: Teachers with powerful laptops can use local
- Default: Cloud for simplicity, local opt-in
**Alternatives Considered**:
- Global setting: Inflexible, doesn't match hardware diversity
- Per-session: Too granular, confusing UX
**Implementation**: User preference stored in `users` table, enforced at generation time

### Decision: Paragraph-Level Citations (Initially)

**Choice**: Attach citations to lesson sections/paragraphs, not sentences
**Rationale**:
- Simplicity: Easier to implement and maintain
- Readability: Fewer inline citations, less cluttered
- Accuracy: Paragraph scope matches RAG chunk size
- Sufficient: Teachers care about section-level sourcing
**Alternatives Considered**:
- Sentence-level: More precise but cluttered, complex parsing
- Section-level only: Too coarse, multiple sources per section
**Future**: Add sentence-level option if user feedback demands it

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│                  Browser                     │
│  ┌─────────────────────────────────────┐   │
│  │         React Application           │   │
│  │  ┌──────────┐  ┌──────────────┐   │   │
│  │  │Auth Store│  │  Processing  │   │   │
│  │  │(Zustand) │  │  Mode Config │   │   │
│  │  └──────────┘  └──────────────┘   │   │
│  │  ┌──────────────────────────────┐ │   │
│  │  │  Citation UI  │ Image Upload │ │   │
│  │  └──────────────────────────────┘ │   │
│  └─────────────────────────────────────┘   │
└──────────────────┬──────────────────────────┘
                   │ HTTP/WS (JWT Auth)
┌──────────────────┴──────────────────────────┐
│              FastAPI Server                  │
│  ┌─────────────────────────────────────┐   │
│  │    Auth Middleware (JWT Verify)     │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │  API Routes                         │   │
│  │  ├─ /auth/* (login, register)       │   │
│  │  ├─ /ingest/image (OCR + Vision)    │   │
│  │  ├─ /generate (with citations)      │   │
│  │  └─ /settings/processing-mode       │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │   Model Router                      │   │
│  │   ├─ Cloud Provider (Chutes)        │   │
│  │   └─ Local Provider (Ollama)        │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │   Image Processing Pipeline         │   │
│  │   ├─ Tesseract OCR                  │   │
│  │   ├─ Vision API (Chutes/CLIP)       │   │
│  │   └─ Embedding Generator            │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │       PocketFlow Backend            │   │
│  │  ├─ Citation Tracking Nodes         │   │
│  │  ├─ RAG Retrieval (w/ provenance)   │   │
│  │  └─ Standards Repository            │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │   SQLite + sqlite-vec               │   │
│  │   ├─ users (auth)                   │   │
│  │   ├─ images (OCR results)           │   │
│  │   ├─ citations (source tracking)    │   │
│  │   └─ vec_embeddings (text + image)  │   │
│  └─────────────────────────────────────┘   │
└──────────────────────────────────────────────┘

External Services:
- Chutes LLM API (cloud mode)
- Chutes Vision API (image understanding)
- Ollama (local mode)
```

## Component Details

### 1. Image Processing Pipeline

```python
# Workflow
1. Image Upload (JPEG/PNG/TIFF)
   ↓
2. Preprocessing (deskew, denoise, resize)
   ↓
3. OCR (Tesseract) → Extracted Text
   ↓
4. Vision API → Semantic Understanding
   ↓
5. Embedding Generation → Vector
   ↓
6. Storage (SQLite + compressed image)
   ↓
7. Indexing (sqlite-vec)
```

**Key Classes**:
- `ImageParser`: Base class with preprocessing utilities
- `SheetMusicParser`: Specialized for musical notation
- `DiagramParser`: For instructional images
- `ImageEmbedder`: Generate vision + text embeddings
- `ImageStore`: Manage storage quota and retrieval

### 2. Citation System

```python
# Citation Flow
1. User requests lesson generation
   ↓
2. RAG retrieval returns chunks + metadata
   ↓
3. PocketFlow nodes track source provenance
   ↓
4. LLM prompt includes citation instructions
   ↓
5. Parser extracts citations from output
   ↓
6. Citation formatter creates IEEE-style refs
   ↓
7. Lesson includes inline [1] and bibliography
```

**Database Schema**:
```sql
CREATE TABLE citations (
    id TEXT PRIMARY KEY,
    lesson_id TEXT NOT NULL,
    source_type TEXT NOT NULL,  -- 'standard', 'document', 'image'
    source_id TEXT NOT NULL,
    source_title TEXT NOT NULL,
    page_number INTEGER,
    excerpt TEXT,
    citation_text TEXT NOT NULL,  -- IEEE formatted
    created_at TIMESTAMP,
    FOREIGN KEY (lesson_id) REFERENCES lessons(id)
);
```

**Citation Format**:
```
Inline: "Students will explore rhythm patterns [1] through
         movement activities [2]."

Bibliography:
[1] North Carolina Standard Course of Study, "K.CR.1: Create
    rhythmic and melodic patterns," 2024, p. 12.
[2] J. Smith, "Movement-Based Music Education," Music Teachers
    Journal, vol. 45, no. 3, pp. 123-130, 2023.
```

### 3. Processing Mode System

```python
# Mode Architecture
class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass

class CloudProvider(LLMProvider):
    """Chutes API implementation"""
    def __init__(self, api_key: str):
        self.client = ChutesClient(api_key)

    async def generate(self, prompt: str, **kwargs) -> str:
        return await self.client.complete(prompt, **kwargs)

class LocalProvider(LLMProvider):
    """Ollama implementation"""
    def __init__(self, model: str = "qwen3:8b"):
        self.client = ollama.AsyncClient()
        self.model = model

    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response['message']['content']

class ModelRouter:
    def __init__(self):
        self.providers = {
            "cloud": CloudProvider(api_key=settings.CHUTES_API_KEY),
            "local": LocalProvider(model="qwen3:8b")
        }

    async def generate(self, prompt: str, mode: str, **kwargs) -> str:
        provider = self.providers.get(mode)
        if not provider or not await provider.is_available():
            raise ProviderUnavailableError(mode)
        return await provider.generate(prompt, **kwargs)
```

**Network Blocking for Local Mode**:
```python
# Firewall logic
ALLOWED_DOMAINS_LOCAL_MODE = [
    "ollama.ai",  # Model downloads
    # No other external calls allowed
]

async def check_network_request(url: str, user_mode: str):
    if user_mode == "local":
        domain = urlparse(url).netloc
        if domain not in ALLOWED_DOMAINS_LOCAL_MODE:
            logger.warning(f"Blocked network request in local mode: {url}")
            raise NetworkBlockedError(url)
```

### 4. Authentication System

```python
# Auth Flow
1. POST /api/auth/login (email + password)
   ↓
2. Verify password (bcrypt.checkpw)
   ↓
3. Generate JWT access token (15 min exp)
   ↓
4. Generate JWT refresh token (7 day exp)
   ↓
5. Return both tokens to client
   ↓
6. Client stores in memory (not localStorage)
   ↓
7. Include access token in Authorization header
   ↓
8. Middleware validates JWT on each request
   ↓
9. On expiry, refresh using refresh token
```

**Database Schema**:
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT NOT NULL,  -- 'teacher', 'admin'
    processing_mode TEXT DEFAULT 'cloud',  -- 'cloud' or 'local'
    created_at TIMESTAMP NOT NULL,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Add user_id to existing tables
ALTER TABLE sessions ADD COLUMN user_id TEXT REFERENCES users(id);
ALTER TABLE lessons ADD COLUMN user_id TEXT REFERENCES users(id);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_lessons_user ON lessons(user_id);
```

**JWT Payload**:
```json
{
  "sub": "user_id",
  "email": "teacher@school.edu",
  "role": "teacher",
  "exp": 1699999999,
  "iat": 1699999000
}
```

**Authorization Decorator**:
```python
def require_auth(required_role: str = None):
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            try:
                payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
                request.state.user = payload
                if required_role and payload["role"] != required_role:
                    raise HTTPException(403, "Insufficient permissions")
                return await func(request, *args, **kwargs)
            except jwt.ExpiredSignatureError:
                raise HTTPException(401, "Token expired")
            except jwt.InvalidTokenError:
                raise HTTPException(401, "Invalid token")
        return wrapper
    return decorator

# Usage
@app.get("/api/users")
@require_auth(required_role="admin")
async def list_users(request: Request):
    # Only admins can access
    return await user_service.list_all()
```

## Data Flow Examples

### Example 1: Image Ingestion with Citations

```
1. Teacher uploads sheet music image (Bach Minuet)
2. Backend:
   a. Preprocessing: deskew, enhance contrast
   b. Tesseract OCR: extract "Minuet in G, J.S. Bach, measures 1-8"
   c. Chutes Vision: identify "baroque-era keyboard music, treble clef, 3/4 time"
   d. Generate embeddings from text + vision features
   e. Store in images table with metadata
   f. Index embeddings in sqlite-vec
3. Later, teacher generates lesson on baroque music
4. RAG retrieval finds Bach Minuet image as relevant source
5. Citation system adds:
   - Inline: "...as seen in Bach's Minuet in G [3]"
   - Bibliography: "[3] J.S. Bach, Minuet in G, uploaded by [Teacher Name], 2025."
```

### Example 2: Local Mode Lesson Generation

```
1. Teacher sets processing mode to "local" in Settings
2. Backend checks Ollama availability and Qwen3 model
3. Teacher starts lesson generation
4. Request routed to LocalProvider instead of CloudProvider
5. Network monitor blocks any external API calls
6. Ollama generates lesson using local Qwen3 model
7. Process takes ~90 seconds (vs. ~30s cloud) but data stays local
8. Teacher sees "Generated locally" badge on lesson
```

### Example 3: Multi-User Session Isolation

```
1. Admin creates accounts for 3 teachers (Alice, Bob, Carol)
2. Alice logs in, generates lesson on rhythm
3. Bob logs in, generates lesson on melody
4. Carol logs in, generates lesson on harmony
5. Each teacher sees only their own lessons:
   - Alice: 1 lesson (rhythm)
   - Bob: 1 lesson (melody)
   - Carol: 1 lesson (harmony)
6. Admin logs in, sees aggregate stats but not lesson content (privacy)
7. All sessions isolated by user_id foreign key filtering
```

## API Design

### Authentication Endpoints

```
POST /api/auth/register
Body: {"email": "...", "password": "...", "full_name": "...", "role": "teacher"}
Response: {"id": "...", "email": "...", "role": "..."}
Auth: Admin only

POST /api/auth/login
Body: {"email": "...", "password": "..."}
Response: {"access_token": "...", "refresh_token": "...", "user": {...}}

POST /api/auth/refresh
Body: {"refresh_token": "..."}
Response: {"access_token": "...", "refresh_token": "..."}

POST /api/auth/logout
Auth: Required
Response: 204 No Content

GET /api/auth/me
Auth: Required
Response: {"id": "...", "email": "...", "role": "...", "processing_mode": "..."}
```

### Image Ingestion Endpoints

```
POST /api/ingest/image
Auth: Required
Body: multipart/form-data with image file
Response: {
  "id": "...",
  "filename": "...",
  "extracted_text": "...",
  "vision_summary": "...",
  "metadata": {...}
}

POST /api/ingest/images/batch
Auth: Required
Body: multipart/form-data with multiple files
Response: [{"id": "...", "filename": "...", "status": "success"}, ...]

GET /api/images/{id}
Auth: Required
Response: {
  "id": "...",
  "filename": "...",
  "extracted_text": "...",
  "vision_summary": "...",
  "url": "/api/images/{id}/data",
  "metadata": {...}
}

GET /api/images/{id}/data
Auth: Required
Response: Image binary data
```

### Processing Mode Endpoints

```
GET /api/settings/processing-modes
Auth: Required
Response: {
  "modes": [
    {
      "id": "cloud",
      "name": "Cloud (Fast)",
      "description": "Uses Chutes API, requires internet",
      "available": true,
      "estimated_speed": "30s per lesson"
    },
    {
      "id": "local",
      "name": "Local (Private)",
      "description": "Uses local Qwen3 model, no data leaves device",
      "available": true,
      "estimated_speed": "90s per lesson",
      "requirements": "16GB RAM, Ollama installed"
    }
  ],
  "current": "cloud"
}

PUT /api/settings/processing-mode
Auth: Required
Body: {"mode": "local"}
Response: {"mode": "local", "updated_at": "..."}

GET /api/models/local/status
Auth: Required
Response: {
  "installed": true,
  "model": "qwen3:8b",
  "version": "Q4_K_M",
  "size": "4.8GB",
  "health": "healthy",
  "last_used": "..."
}
```

### Citation Endpoints

```
GET /api/lessons/{lesson_id}/citations
Auth: Required
Response: [
  {
    "id": "...",
    "source_type": "standard",
    "source_title": "North Carolina Standard Course of Study",
    "citation_text": "[1] North Carolina...",
    "excerpt": "Students will create..."
  },
  ...
]

GET /api/citations/{id}/source
Auth: Required
Response: {
  "source_type": "standard",
  "source_id": "K.CR.1",
  "full_text": "...",
  "metadata": {...}
}
```

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Image OCR processing | < 10s per page | 95th percentile |
| Image upload (5MB) | < 5s | Including network time |
| Citation resolution | < 200ms | Per lesson generation |
| Local model inference | < 2min per lesson | Qwen3 8B on M1 16GB |
| Cloud model inference | < 30s per lesson | Existing Milestone 2 performance |
| Auth token validation | < 5ms | Per request |
| User session isolation query | < 10ms | With proper indexes |
| Image storage quota check | < 50ms | Before upload |

## Security Considerations

### Authentication & Authorization
- Password hashing: bcrypt with cost factor 12
- JWT secret: 256-bit random key, rotated quarterly
- Token expiration: 15 min access, 7 day refresh
- Rate limiting: 5 login attempts per minute per IP
- HTTPS required: Reject HTTP in production
- CSRF protection: SameSite cookies, CSRF tokens

### Data Protection
- User passwords: Never logged or exposed in API responses
- Student data: Clear warnings before cloud processing
- Local mode: Network firewall prevents data leakage
- Database: Encrypted at rest (SQLite encryption extension)
- Backups: Encrypted, user data anonymized

### Input Validation
- Image uploads: Max 10MB, type whitelist (JPEG, PNG, TIFF)
- File scanning: Virus scan before processing (ClamAV)
- SQL injection: Parameterized queries only
- XSS protection: React escaping + CSP headers
- Path traversal: Validate all file paths

### Audit Logging
- Login attempts (success and failure)
- Password changes
- Role changes (admin actions)
- Processing mode switches
- Network blocks in local mode
- User creation/deletion

## Risks / Trade-offs

### Risk: Local Model Quality vs. Cloud

**Impact**: Local-generated lessons may be lower quality
**Likelihood**: Medium - 8B models generally good but not GPT-4 level
**Mitigation**:
- Default to cloud mode
- Show quality comparison in settings
- Collect feedback on local vs. cloud lessons
- Consider larger models (13B) for powerful hardware

### Risk: Image Storage Growth

**Impact**: Disk space exhaustion with many image uploads
**Likelihood**: Medium - Teachers may upload entire sheet music libraries
**Mitigation**:
- 5GB default quota per deployment
- LRU eviction for oldest images
- Image compression (JPEG quality 85)
- Admin dashboard showing storage usage
- Configurable quota per deployment

### Risk: OCR Errors in Citations

**Impact**: Incorrect citations due to OCR mistakes
**Likelihood**: High - OCR accuracy varies by image quality
**Mitigation**:
- Show confidence scores on extracted text
- Provide manual verification interface
- Allow teachers to edit extracted content
- Use vision API for semantic understanding, not just OCR text

### Risk: Authentication Complexity

**Impact**: User lockouts, forgotten passwords, support burden
**Likelihood**: Medium - Common with any auth system
**Mitigation**:
- Clear password reset flow (email required)
- Admin can reset user passwords
- Session timeout warnings before logout
- Comprehensive auth error messages

### Trade-off: Local Mode Performance

**Benefit**: Complete data privacy, no internet dependency
**Cost**: 3x slower generation, higher hardware requirements
**Decision**: Acceptable - privacy-conscious schools will accept trade-off
**Communication**: Clear performance comparison in UI

### Trade-off: Citation Readability

**Benefit**: Transparent sourcing, verification, accountability
**Cost**: More text in lessons, potential clutter
**Decision**: Acceptable - citations essential for trust
**Mitigation**: Collapsible reference sections, hover tooltips for inline

## Migration Plan

### Phase 1: Additive Features (Week 1-2)
1. Deploy image ingestion backend (no UI yet)
2. Deploy citation tracking (backend only)
3. Test with sample data
4. No impact on existing users

### Phase 2: Auth System (Week 3)
1. Create database migration script (add users table, user_id columns)
2. Deploy auth endpoints
3. Create initial admin account
4. All existing sessions/lessons assigned to admin temporarily
5. Existing users continue without login (admin session)

### Phase 3: Local Mode (Week 4)
1. Deploy Ollama integration
2. Add processing mode settings
3. Beta test with volunteers
4. Default remains cloud for all users

### Phase 4: Full Release (Week 5)
1. Deploy complete UI for all features
2. Migrate existing users to proper accounts
3. Enable auth requirement (grace period for migration)
4. Full feature documentation and training

### Rollback Strategy
- Auth can be disabled via config flag (single-user mode)
- Image ingestion can be disabled (text-only mode)
- Local mode optional (cloud-only deployment)
- Citation system can be hidden in UI (still tracked)
- No destructive changes to existing data

## Open Questions

1. **Should we support federated authentication (SAML/OAuth) in M3?**
   - Benefit: Easier school-wide adoption with SSO
   - Cost: Complex integration, testing burden
   - Decision: Defer to Milestone 4, start with local auth

2. **What OMR (Optical Music Recognition) library to use for advanced notation?**
   - Options: Audiveris (Java), OMR-Datasets (research), custom ML model
   - Decision: Start with Tesseract + Vision API, add specialized OMR in M4 if needed

3. **Should image embeddings be separate from text embeddings in sqlite-vec?**
   - Option A: Separate tables for different modalities
   - Option B: Unified embedding table with type field
   - Decision: Unified table for cross-modal search

4. **How to handle citation conflicts when multiple sources say different things?**
   - Option A: Show all conflicting citations
   - Option B: Prefer primary sources (standards) over secondary
   - Decision: Show all, let teachers decide (transparency over curation)

5. **Should local mode support fine-tuning on school-specific data?**
   - Benefit: Better lesson quality for school's specific needs
   - Cost: Complexity, data requirements, compute
   - Decision: Defer to future milestone, gather feedback first
