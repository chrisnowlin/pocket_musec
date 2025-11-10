# Technical Design

## Context

Milestone 1 delivered a functional CLI-based lesson generation system with comprehensive backend functionality. Teachers can generate standards-aligned lessons through a conversational interface, but the command-line interface limits adoption among non-technical users.

This milestone builds a web interface layer on top of the existing backend, providing a visual, intuitive experience while maintaining all existing CLI functionality.

### Constraints
- Must maintain backward compatibility with CLI
- Backend already uses PocketFlow, SQLite, and Chutes API
- Must work on typical teacher laptops (4GB RAM, older browsers)
- No authentication system in this milestone
- Must support both WebSocket and SSE for compatibility

### Stakeholders
- K-12 music teachers (primary users)
- School IT administrators (deployment)
- Development team (maintenance)

## Goals / Non-Goals

### Goals
- Provide browser-based access to all Milestone 1 functionality
- Improve user experience with visual interface and real-time feedback
- Enable lesson export in multiple formats (PDF, Word, text)
- Support session persistence across browser refreshes
- Maintain performance on modest hardware

### Non-Goals
- User authentication and multi-user support (defer to Milestone 3)
- Collaborative features like sharing (defer to future)
- Mobile app development (web responsive design only)
- Offline-first architecture (require internet for LLM)
- Cloud deployment (local deployment only for now)

## Decisions

### Decision: FastAPI for Backend API
**Choice**: FastAPI over Flask or Django
**Rationale**: 
- Native async/await support for WebSocket handling
- Automatic OpenAPI documentation generation
- Built-in request validation with Pydantic
- Better performance than Flask, simpler than Django
**Alternatives Considered**:
- Flask + Socket.IO: More complex WebSocket setup
- Django + Channels: Too heavyweight for our needs

### Decision: React + TypeScript for Frontend
**Choice**: React with TypeScript and Vite
**Rationale**:
- React's component model fits our multi-step workflows
- TypeScript provides type safety matching backend Pydantic
- Vite offers fast build times and excellent DX
- Large ecosystem of compatible libraries
**Alternatives Considered**:
- Vue.js: Smaller community, less component library support
- Svelte: Less mature ecosystem, harder to hire for
- Plain JavaScript: Lost type safety benefits

### Decision: Zustand for State Management
**Choice**: Zustand over Redux or Context API
**Rationale**:
- Simpler API than Redux with less boilerplate
- Better performance than Context API for frequent updates
- TypeScript support out of the box
- Small bundle size (8KB)
**Alternatives Considered**:
- Redux Toolkit: Overkill for our state complexity
- React Context: Performance issues with frequent updates
- Jotai: Less community adoption

### Decision: shadcn/ui for Components
**Choice**: shadcn/ui with Tailwind CSS
**Rationale**:
- Copy-paste components allow customization
- Built on Radix UI for accessibility
- Tailwind provides consistent design system
- No runtime dependencies
**Alternatives Considered**:
- Material-UI: Heavy bundle, opinionated design
- Ant Design: Large bundle, less customizable
- Chakra UI: Runtime CSS-in-JS performance cost

### Decision: IndexedDB for Client Storage
**Choice**: IndexedDB with Dexie.js wrapper
**Rationale**:
- Large storage quota (>50MB typically)
- Structured data storage for complex objects
- Better performance than localStorage for large data
- Dexie provides Promise-based API
**Alternatives Considered**:
- localStorage: 5-10MB limit too small for drafts
- WebSQL: Deprecated, no longer maintained
- Cache API: Designed for network resources, not app data

### Decision: WebSocket with SSE Fallback
**Choice**: Primary WebSocket, fallback to Server-Sent Events
**Rationale**:
- WebSocket provides true bidirectional communication
- SSE works through proxies and firewalls
- Progressive enhancement strategy
- Both supported by FastAPI natively
**Alternatives Considered**:
- WebSocket only: Some school networks block WebSocket
- Long polling: Poor performance, complex implementation
- gRPC-Web: Limited browser support, overkill

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│                  Browser                     │
│  ┌─────────────────────────────────────┐   │
│  │         React Application           │   │
│  │  ┌──────────┐  ┌──────────────┐   │   │
│  │  │  Zustand │  │  IndexedDB   │   │   │
│  │  │  Store   │  │   Storage    │   │   │
│  │  └──────────┘  └──────────────┘   │   │
│  └─────────────────────────────────────┘   │
└──────────────────┬──────────────────────────┘
                   │ HTTP/WS/SSE
┌──────────────────┴──────────────────────────┐
│              FastAPI Server                  │
│  ┌─────────────────────────────────────┐   │
│  │    API Routes    │   WebSocket      │   │
│  │  ┌────────────┐  │  ┌────────────┐ │   │
│  │  │  REST API  │  │  │  WS Handler│ │   │
│  │  └────────────┘  │  └────────────┘ │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │       PocketFlow Backend            │   │
│  │  ┌────────────┐  ┌────────────┐   │   │
│  │  │LessonAgent │  │  Standards  │   │   │
│  │  └────────────┘  │  Repository │   │   │
│  │                  └────────────┘    │   │
│  └─────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

## API Design

### REST Endpoints

```
GET  /health                          # Health check
GET  /api/standards                   # List standards with filters
GET  /api/standards/{id}              # Get standard details
GET  /api/standards/search            # Full-text search

POST /api/sessions                    # Create session
GET  /api/sessions/{id}               # Get session
PUT  /api/sessions/{id}               # Update session
DELETE /api/sessions/{id}             # Delete session
GET  /api/sessions/{id}/history       # Get drafts

POST /api/export/pdf                  # Export as PDF
POST /api/export/docx                 # Export as Word
POST /api/export/text                 # Export as text
```

### WebSocket Protocol

```javascript
// Client → Server
{
  "type": "generate_lesson",
  "session_id": "uuid",
  "requirements": {
    "grade": "3",
    "strand": "CR",
    "standards": ["3.CR.1"],
    "objectives": ["3.CR.1.1", "3.CR.1.2"]
  }
}

// Server → Client (Streaming)
{
  "type": "partial_content",
  "content": "## Lesson Plan\n\n### Title: Creating..."
}

// Server → Client (Complete)
{
  "type": "generation_complete",
  "lesson_id": "uuid",
  "content": "..."
}

// Server → Client (Error)
{
  "type": "error",
  "message": "Generation failed",
  "code": "GENERATION_ERROR"
}
```

## Component Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── Layout.tsx
│   │   ├── standards/
│   │   │   ├── StandardsList.tsx
│   │   │   ├── StandardDetail.tsx
│   │   │   └── StandardsFilter.tsx
│   │   ├── generation/
│   │   │   ├── GenerationFlow.tsx
│   │   │   ├── GradeSelector.tsx
│   │   │   ├── StrandSelector.tsx
│   │   │   └── ProgressIndicator.tsx
│   │   └── lesson/
│   │       ├── LessonViewer.tsx
│   │       ├── LessonEditor.tsx
│   │       └── ExportMenu.tsx
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useSession.ts
│   │   └── useStandards.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── storage.ts
│   │   └── export.ts
│   ├── store/
│   │   ├── sessionStore.ts
│   │   └── uiStore.ts
│   └── types/
│       ├── api.types.ts
│       └── models.types.ts
```

## State Management Schema

```typescript
interface SessionStore {
  currentSession: Session | null;
  drafts: Draft[];
  requirements: Requirements;
  
  // Actions
  createSession: () => Promise<void>;
  updateRequirements: (req: Partial<Requirements>) => void;
  saveDraft: (content: string) => Promise<void>;
  loadSession: (id: string) => Promise<void>;
}

interface UIStore {
  generationStep: GenerationStep;
  isGenerating: boolean;
  streamingContent: string;
  error: Error | null;
  
  // Actions
  setStep: (step: GenerationStep) => void;
  setGenerating: (generating: boolean) => void;
  appendContent: (content: string) => void;
  setError: (error: Error | null) => void;
}
```

## Data Flow

1. **Session Creation**:
   - User clicks "Generate New Lesson"
   - Frontend creates session via POST /api/sessions
   - Session ID stored in Zustand and IndexedDB
   - User proceeds to generation flow

2. **Lesson Generation**:
   - User selects requirements through UI steps
   - Frontend establishes WebSocket connection
   - Requirements sent via WebSocket message
   - Server streams partial content back
   - Frontend updates UI in real-time
   - Complete lesson stored in session

3. **Session Recovery**:
   - Page refresh triggers IndexedDB check
   - Active sessions loaded into Zustand
   - UI restored to last known state
   - WebSocket reconnection if needed

## Risks / Trade-offs

### Risk: WebSocket Connection Stability
**Impact**: Lesson generation could fail mid-stream
**Mitigation**: 
- Implement exponential backoff reconnection
- Save partial content to prevent data loss
- Provide SSE fallback for problematic networks

### Risk: Large Draft Storage
**Impact**: IndexedDB quota exceeded
**Mitigation**:
- Implement LRU cache for drafts
- Compress content before storage
- Monitor storage quota and warn users

### Risk: PDF Generation Performance
**Impact**: Browser freezes during export
**Mitigation**:
- Use Web Workers for PDF generation
- Implement progress indicators
- Start with simple formatting, iterate

### Trade-off: No Authentication
**Impact**: No user isolation, shared browser sessions
**Mitigation**:
- Use session IDs for temporary isolation
- Clear guidance on single-user expectation
- Plan authentication for Milestone 3

### Trade-off: Client-Heavy Architecture
**Impact**: Requires modern browser, more client resources
**Benefit**: Better UX with immediate feedback
**Mitigation**:
- Progressive enhancement for older browsers
- Lazy load components to reduce initial bundle
- Server-side rendering consideration for future

## Migration Plan

1. **Phase 1**: Deploy API server alongside CLI (no breaking changes)
2. **Phase 2**: Beta test web UI with select teachers
3. **Phase 3**: Document migration from CLI to web
4. **Phase 4**: Full release with both interfaces supported
5. **Future**: Deprecate CLI after web adoption (Milestone 4+)

### Rollback Strategy
- API and web are additive, no changes to CLI
- Can disable web interface without affecting CLI users
- Version API endpoints for future breaking changes

## Performance Targets

- Initial page load: < 2 seconds on 3G
- Time to interactive: < 3 seconds
- API response time: < 200ms (p95)
- WebSocket latency: < 100ms
- Bundle size: < 500KB gzipped
- Memory usage: < 100MB active

## Security Considerations

- Input sanitization on all API endpoints
- XSS protection in React (default)
- CORS configured for local development only
- Rate limiting on generation endpoints
- Session timeout after 2 hours
- No sensitive data in IndexedDB

## Open Questions

1. **Should we implement PWA features (service worker, offline manifest)?**
   - Benefit: Better offline experience, installable
   - Cost: Additional complexity, testing burden
   - Decision: Defer to user feedback after initial release

2. **What level of browser support should we target?**
   - Current: Modern browsers (Chrome 90+, Firefox 88+, Safari 14+)
   - Alternative: Include IE 11 / older browser support
   - Decision: Modern browsers only, with graceful degradation

3. **Should we implement request caching at the API level?**
   - Benefit: Faster repeated requests
   - Cost: Cache invalidation complexity
   - Decision: Start with browser caching, add if needed

4. **How should we handle concurrent edits in multiple tabs?**
   - Current: Last write wins with BroadcastChannel updates
   - Alternative: Operational transformation for real-time sync
   - Decision: Simple approach now, revisit if users complain