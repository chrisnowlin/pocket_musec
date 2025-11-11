# Change Proposal: Add Electron Desktop App

**Change ID**: `add-electron-desktop-app`  
**Status**: DRAFT  
**Created**: 2025-11-10  
**Author**: AI Assistant  

## Why

While the web interface (Milestone 2) provides browser-based access to PocketMusec, macOS teachers need a native desktop application for:

1. **Simplified deployment**: Single-click install without managing separate backend/frontend processes
2. **Offline reliability**: Embedded backend ensures the app works without internet connectivity (especially in local mode)
3. **System integration**: Native file associations, OS notifications, Dock integration, menu bar presence
4. **Better UX**: Native window controls, keyboard shortcuts, and macOS-specific behaviors (cmd key, menu bar, Dock)
5. **Professional presentation**: Teachers perceive native apps as more trustworthy and stable than browser-based tools

Currently, macOS teachers must:
- Install Python dependencies separately
- Run `python run_api.py` in a terminal
- Run `npm run dev` in another terminal
- Navigate to `localhost:5173` in a browser
- Keep both terminal windows running

This multi-step process creates friction for non-technical users and increases support burden. A native macOS app eliminates this barrier.

## What Changes

Implement a macOS-native Electron-based desktop application that:

- **Bundles the complete stack**: Packages Python backend (FastAPI + PocketFlow), React frontend, and Python runtime into a single executable
- **Manages backend lifecycle**: Automatically starts/stops the FastAPI server when the app launches/quits
- **Provides native macOS experience**: Window management, Dock integration, menu bar, native menus, keyboard shortcuts
- **Handles updates**: Auto-update mechanism using electron-builder with GitHub releases (macOS only)
- **Maintains feature parity**: All Milestone 2 and Milestone 3 features work identically in desktop app
- **Supports macOS**: Apple Silicon (M1/M2/M3) and Intel Macs, macOS 10.15 (Catalina) and later

**BREAKING**: None - this is an additive feature that complements the existing web interface

## Impact

### Affected Specs
- **New**: `electron-desktop` - Desktop app shell and Electron integration
- **New**: `desktop-backend-integration` - Backend process management and IPC
- **New**: `desktop-auto-update` - Update mechanism and versioning

### Affected Code
- **New files**:
  - `electron/main.ts` - Electron main process
  - `electron/preload.ts` - Preload scripts for security
  - `electron/backend-manager.ts` - Python backend lifecycle management
  - `electron/package.json` - Electron dependencies
  - `electron/tsconfig.json` - TypeScript config for Electron
  - `electron-builder.yml` - Build configuration for macOS packaging
  
- **Modified files**:
  - `frontend/src/main.tsx` - Detect Electron context and adjust API URLs
  - `frontend/vite.config.ts` - Add Electron-specific build target
  - `backend/api/main.py` - Add shutdown endpoint for graceful Electron integration
  - `pyproject.toml` - Add PyInstaller for bundling Python runtime
  - Root `package.json` - Add Electron build scripts and dependencies

- **New build artifacts**:
  - `dist-electron/` - Electron build output
  - `release/` - Packaged installers (.dmg for macOS only)

### Deployment Changes
- New release pipeline for building macOS-specific installer
- Auto-update server configuration (GitHub Releases)
- Code signing and notarization certificate configuration (Apple Developer ID)

## Technical Decisions

### Architecture

```
┌─────────────────────────────────────┐
│     Electron Main Process           │
│  (Node.js - main.ts)                │
│  - Window management                │
│  - Backend process spawning         │
│  - Auto-updates                     │
│  - System tray                      │
└─────────┬───────────────────────────┘
          │
          ├─────► Backend Manager
          │       - Spawns Python process
          │       - Health checks
          │       - Port management
          │       - Graceful shutdown
          │
          ├─────► IPC Bridge
          │       - Secure communication
          │       - File system access
          │       - Native dialogs
          │
          └─────► Auto-update Module
                  - Check for updates
                  - Download & install
                  - Release notes
┌─────────────────────────────────────┐
│   Electron Renderer Process         │
│  (Chromium - React App)             │
│  - Existing frontend code           │
│  - Detects Electron context         │
│  - Uses IPC for native features     │
└─────────────────────────────────────┘
          │
          └─────► FastAPI Backend
                  - Bundled via PyInstaller
                  - Runs on dynamic port
                  - Isolated Python env
```

### Python Backend Bundling

**Option 1: PyInstaller** (RECOMMENDED)
- Bundles Python runtime + dependencies into single executable
- Pros: Simple, well-tested, cross-platform
- Cons: Large bundle size (~150-200MB), slow startup

**Option 2: Python Embedded Distribution**
- Ship minimal Python runtime + wheels
- Pros: Smaller size, faster startup
- Cons: Complex dependency management, platform-specific

**Decision**: Use PyInstaller for v1 due to simplicity and reliability. Optimize later if bundle size becomes an issue.

### Backend Process Management

```typescript
// electron/backend-manager.ts
class BackendManager {
  private process: ChildProcess | null = null;
  private port: number = 0;
  
  async start(): Promise<number> {
    // 1. Find available port
    this.port = await findFreePort(8000, 9000);
    
    // 2. Spawn Python backend
    const backendPath = path.join(
      app.getAppPath(),
      'resources',
      'backend',
      process.platform === 'win32' ? 'main.exe' : 'main'
    );
    
    this.process = spawn(backendPath, [`--port=${this.port}`], {
      env: { ...process.env, ELECTRON_MODE: 'true' }
    });
    
    // 3. Wait for health check
    await this.waitForHealthy();
    
    return this.port;
  }
  
  async stop(): Promise<void> {
    // Graceful shutdown via API endpoint
    await axios.post(`http://localhost:${this.port}/api/shutdown`);
    
    // Force kill after timeout
    setTimeout(() => {
      if (this.process && !this.process.killed) {
        this.process.kill('SIGTERM');
      }
    }, 5000);
  }
}
```

### Security Considerations

- **Context isolation**: Enable `contextIsolation: true` in BrowserWindow
- **Preload scripts**: Use preload script for controlled IPC access
- **No Node integration in renderer**: Keep `nodeIntegration: false`
- **CSP headers**: Content Security Policy to prevent XSS
- **Code signing**: Sign apps for macOS and Windows to avoid security warnings

### Update Strategy

- **Electron-updater**: Use `electron-updater` library (built on Squirrel)
- **Update channel**: GitHub Releases for public distribution
- **Update flow**:
  1. Check for updates on startup (configurable interval)
  2. Download in background if available
  3. Notify user with release notes
  4. Install on quit (macOS/Linux) or immediately (Windows)
- **Delta updates**: Use delta updates to minimize download size
- **Rollback**: Keep previous version for emergency rollback

## Implementation Phases

### Phase 1: Electron Shell (Week 1)
- Set up Electron project structure for macOS
- Create main process with window management
- Integrate existing React frontend
- Test frontend loads in Electron window

### Phase 2: Backend Integration (Week 2)
- Bundle Python backend with PyInstaller for macOS (universal binary for Apple Silicon + Intel)
- Implement backend manager with process spawning
- Handle port management and health checks
- Test full stack communication in Electron

### Phase 3: macOS Native Features (Week 3)
- Add Dock integration with menu and recent items
- Implement menu bar integration
- Add native menus and keyboard shortcuts (Cmd-key conventions)
- Implement IPC bridge for native file dialogs and notifications

### Phase 4: Build & Distribution (Week 4)
- Configure electron-builder for macOS (DMG and ZIP)
- Set up code signing with Apple Developer ID
- Configure notarization with Apple's notary service
- Create GitHub Actions for automated macOS builds

### Phase 5: Testing & Polish (Week 5)
- Test on macOS with Apple Silicon and Intel hardware
- Verify code signature and notarization
- Optimize bundle size and startup time
- Write macOS-specific documentation

## Dependencies

### Required
- Existing Milestone 2 web interface (frontend + backend)
- Node.js 18+ (for Electron toolchain)
- Python 3.11+ (for PyInstaller bundling)

### New NPM Packages
```json
{
  "electron": "^28.0.0",
  "electron-builder": "^24.9.0",
  "electron-updater": "^6.1.7",
  "electron-store": "^8.1.0",
  "find-free-port": "^2.0.0",
  "wait-on": "^7.2.0"
}
```

### New Python Packages
```toml
[project.optional-dependencies]
desktop = [
    "pyinstaller>=6.3.0",
]
```

### Build Tools
- **macOS**: Xcode command line tools (for code signing)
- **Windows**: Windows SDK (for code signing)
- **Linux**: AppImage tools (for distribution)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large bundle size (>200MB) | Medium | Use ASAR compression; exclude unnecessary dependencies; provide delta updates |
| Slow startup time (>5s) | Medium | Cache backend health check; pre-warm Python runtime; optimize import paths; show splash screen |
| Apple Silicon vs Intel compatibility | High | Build universal binary (arm64 + x86_64) with PyInstaller; test on both architectures |
| Code signing & notarization complexity | High | Document signing process; use GitHub Actions secrets; integrate notarization into CI/CD |
| Update mechanism failures | Medium | Implement robust error handling; provide manual update option; rollback capability |
| Backend process zombie issues | Medium | Implement proper process cleanup; use watchdog timers; handle crashes gracefully |
| Gatekeeper warnings | Medium | Code sign and notarize all releases; maintain reputation over time |

## Open Questions

1. **Mac App Store**: Should we also distribute via Mac App Store, or direct downloads only?
2. **Licensing**: Do we need separate licenses for bundled Python runtime and dependencies?
3. **Telemetry**: Should we add anonymous crash reporting to the desktop app (Sentry)?
4. **Multi-instance**: Allow multiple app instances or enforce single instance?
5. **Data location**: Store user data in `~/Library/Application Support/PocketMusec` or `~/Documents/PocketMusec`?
6. **Offline mode**: Should desktop app support completely offline operation (bundle local models)?
7. **macOS version support**: Drop support for macOS < 10.15 (Catalina) for simpler Electron support?

## Success Criteria

- [ ] Single-click installer available for macOS (universal binary: Apple Silicon + Intel)
- [ ] Code signed and notarized (no Gatekeeper warnings)
- [ ] Backend automatically starts/stops with app lifecycle
- [ ] All Milestone 2 & 3 features work identically in desktop app
- [ ] App appears in Dock and menu bar with appropriate icons
- [ ] Native macOS keyboard shortcuts (Cmd+N, Cmd+S, etc.) work
- [ ] Auto-update downloads and installs updates seamlessly
- [ ] Bundle size < 300MB
- [ ] Startup time < 5 seconds on typical macOS hardware
- [ ] Memory usage < 500MB idle, < 1GB during lesson generation
- [ ] Graceful handling of backend crashes (auto-restart)
- [ ] Works on both Apple Silicon (M1/M2/M3) and Intel Macs

## Related Changes

- Complements: `implement-milestone2-web-interface` (uses same frontend)
- Complements: `implement-milestone3-advanced-features` (all features available in desktop)
- Future: `add-tauri-desktop-app` (lighter-weight alternative to Electron)

## Alternatives Considered

### Tauri
- **Pros**: Smaller bundle (~30-50MB), faster startup, Rust-based
- **Cons**: Less mature, fewer native macOS features, smaller ecosystem
- **Decision**: Defer Tauri to future milestone; Electron proven and widely used for macOS apps

### SwiftUI Native App
- **Pros**: Native macOS app, best performance, native feel
- **Cons**: Requires complete rewrite of backend and frontend, massive effort
- **Decision**: Not viable given existing web/Python stack

### PyWebView
- **Pros**: Simpler, Python-native, no Node.js required
- **Cons**: Limited features, poor update mechanism, not macOS-optimized
- **Decision**: Not suitable for production-grade macOS app

## Migration Path

For users currently running web interface:
1. Install desktop app
2. App detects existing data in `~/.pocketmusec/` or `data/`
3. Prompt to import sessions and settings
4. Provide option to continue using web interface alongside desktop app

No data migration required - desktop app uses same database and file structure.
