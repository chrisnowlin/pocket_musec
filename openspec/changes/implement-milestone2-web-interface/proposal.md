# Change Proposal: Implement Milestone 2 Web Interface

**Change ID**: `implement-milestone2-web-interface`  
**Status**: DRAFT  
**Created**: 2025-11-10  
**Author**: cnowlin  

## Summary

Build the web interface layer for PocketMusec, transitioning from CLI-only to a browser-based React application with real-time lesson generation, enhanced visualization, and improved teacher workflow. This milestone delivers the FastAPI backend server, React frontend, and WebSocket-based streaming for interactive lesson generation.

## Problem

While Milestone 1 delivered a functional CLI for lesson generation, teachers need:
1. A more intuitive visual interface for browsing standards and generating lessons
2. Real-time streaming feedback during lesson generation
3. Better visualization of standards hierarchy and relationships
4. Session persistence and lesson history management in the browser
5. Collaborative features like sharing and exporting lessons

The CLI workflow requires technical comfort that many teachers may lack, limiting adoption.

## Solution

Implement a modern web stack with:
1. **FastAPI Server**: HTTP/WebSocket API serving the existing PocketFlow backend
2. **React Frontend**: TypeScript + Vite SPA with shadcn/ui components
3. **Real-time Streaming**: WebSocket communication with SSE fallback
4. **Session Management**: Browser-based draft history and workspace
5. **Export Options**: Download lessons as PDF, Word, or plain text

## Capabilities

This change introduces three core capabilities:

### 1. Web Interface (`web-interface`)
React-based single-page application for lesson generation workflow.

### 2. API Server (`api-server`)
FastAPI backend exposing PocketFlow functionality via HTTP and WebSocket endpoints.

### 3. Session Management (`session-management`)
Browser-based session persistence, draft history, and export functionality.

## User Journey

1. Teacher opens PocketMusec web app in their browser
2. Landing page shows quick-start options and recent sessions
3. Teacher clicks "Generate New Lesson" to start interactive flow
4. Visual interface guides through grade/strand/standard selection
5. Real-time streaming shows lesson generation progress
6. Generated lesson displays with rich formatting and editing tools
7. Teacher can save, export, or regenerate with modifications
8. Session history persists across browser sessions

## Technical Approach

- FastAPI server wrapping existing PocketFlow backend
- React 18 with TypeScript for type-safe frontend
- Zustand for client-side state management  
- shadcn/ui + Tailwind CSS for consistent UI components
- WebSocket for real-time communication, SSE as fallback
- IndexedDB for client-side session persistence
- PDF generation via browser-based libraries (jsPDF/react-pdf)

## Dependencies

- Existing Milestone 1 backend (PocketFlow, standards DB, lesson generation)
- New frontend toolchain: Node.js, Vite, React, TypeScript
- FastAPI and WebSocket libraries for Python backend
- No breaking changes to existing CLI functionality

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| WebSocket compatibility | Medium | Implement SSE fallback for older browsers |
| Client-side storage limits | Low | Limit draft history to 20 items, compress data |
| PDF generation complexity | Medium | Start with simple text export, iterate on formatting |
| Cross-browser compatibility | Medium | Target modern browsers, progressive enhancement |

## Open Questions

1. Should we implement user authentication in this milestone or defer?
2. What level of collaborative features (sharing, templates) to include?
3. Should the web interface completely replace CLI or complement it?
4. Do we need offline support via service workers in this milestone?

## Success Criteria

- [ ] Web app accessible at http://localhost:3000
- [ ] Complete lesson generation flow works in browser
- [ ] Real-time streaming updates during generation
- [ ] Session history persists across page refreshes
- [ ] Export lessons as PDF, Word, or text files
- [ ] Responsive design works on tablet and desktop
- [ ] All Milestone 1 functionality accessible via web UI
- [ ] Performance: < 2s initial load, < 100ms interactions

## Related Changes

- `implement-milestone1-foundation` - Builds on the backend foundation

## Why

Teachers need an accessible, visual interface for lesson generation that doesn't require command-line knowledge. A web interface will dramatically increase adoption and usability of the PocketMusec system.

## What Changes

- **NEW**: FastAPI server with REST and WebSocket endpoints
- **NEW**: React TypeScript frontend with modern UI components
- **NEW**: Real-time streaming for lesson generation progress
- **NEW**: Browser-based session management and persistence
- **NEW**: Export functionality for multiple formats (PDF, Word, text)
- **NEW**: Visual standards browser and selector
- **ENHANCED**: Lesson editor with rich text formatting
- **MAINTAINED**: All existing CLI functionality remains unchanged

## Impact

- Affected specs: None (all new capabilities)
- Affected code: 
  - New `/frontend` directory for React app
  - New `/backend/api` module for FastAPI server
  - Enhanced `/backend/utils` for export formats
- User impact: Significantly improved user experience for non-technical teachers