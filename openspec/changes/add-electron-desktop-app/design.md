# Design Document: Electron Desktop App

## Context

PocketMusec currently exists as a web application with separate frontend (React/Vite) and backend (FastAPI/Python) processes. While this works well for development and browser-based usage, macOS teachers need a native desktop application that:
- Requires no technical setup (single installer, no Python/Node dependencies)
- Works reliably offline (embedded backend)
- Integrates with macOS features (Dock, menu bar, Notification Center)
- Updates automatically with code signing and notarization
- Feels like a native macOS app (Cmd+key shortcuts, standard behaviors)

Electron provides a proven path to package web applications as native macOS apps, used by many professional applications (VS Code, Slack, Figma, etc.).

## Goals

### Primary Goals
- Package entire PocketMusec stack (frontend + backend + Python runtime) into single macOS app
- Maintain 100% feature parity with web version
- Provide native macOS UX (Dock integration, menu bar, Cmd+key shortcuts, Notification Center)
- Enable auto-updates with code signing and notarization
- Support both Apple Silicon (M1/M2/M3) and Intel Macs with universal binary
- Zero technical setup (single DMG installer, no Python/Node knowledge required)

### Non-Goals
- Windows or Linux support (macOS only for v1)
- Mobile app (iOS/Android) - out of scope
- Mac App Store distribution (direct download via GitHub for now)
- Rewriting backend in Swift - maintain Python/FastAPI stack
- Supporting macOS versions older than Catalina (10.15)

## Decisions

### Decision 1: Electron vs. Tauri vs. Native

**Options Considered:**

| Factor | Electron | Tauri | SwiftUI Native |
|--------|----------|-------|--------|
| Bundle size | 150-250MB | 30-50MB | ~50MB |
| Maturity | Very mature (10+ years) | Young (~3 years) | Native OS |
| macOS Integration | Good | Decent | Excellent |
| Development Speed | Fast (reuse web code) | Fast | Slow (full rewrite) |
| Community | Very large | Small but growing | macOS-specific |
| Code Reuse | 100% (existing React) | 70-80% | 0% (new app) |

**Decision**: Use Electron for v1

**Rationale:**
- Maturity and stability are critical for teacher-facing app
- 100% code reuse from existing React frontend
- Bundle size (<250MB) acceptable for professional macOS app
- Extensive documentation and community support reduces risk
- Fast development path (reuse existing stack)
- Code signing and notarization well-supported
- Future: Tauri can be evaluated for lighter alternative if needed

### Decision 2: Backend Bundling Strategy

**Options:**

1. **PyInstaller** - Bundle Python + dependencies into single executable
2. **Embedded Python** - Ship Python runtime + wheel files
3. **Docker** - Run backend in containerized environment
4. **Remote Backend** - Connect to cloud-hosted backend

**Decision**: Use PyInstaller

**Rationale:**
- PyInstaller is mature and well-tested
- Simple build process (single spec file)
- Cross-platform support (macOS, Windows, Linux)
- Isolated Python environment (no conflicts with user's Python)
- Offline operation (no cloud dependency)

**Trade-offs:**
- Large bundle size (~100-150MB for Python + deps) - acceptable for native app
- Slower startup time (2-3s) vs. embedded Python - mitigated by splash screen
- Black-box executable (harder to debug) - compensated by robust logging

**Mitigation:**
- Accept larger bundle for v1 (simplicity and reliability > size)
- Add branded splash screen to mask startup time
- Implement comprehensive logging for debugging
- Optimize later only if bundle size becomes user complaint

### Decision 3: Backend Process Management

**Architecture:**

```typescript
// electron/backend-manager.ts
class BackendManager {
  private process: ChildProcess | null = null;
  private port: number = 0;
  private healthCheckInterval: NodeJS.Timeout | null = null;
  
  async start(): Promise<void> {
    // 1. Find free port
    this.port = await findFreePort(8000, 9000);
    
    // 2. Spawn backend process
    const backendExec = this.getBackendExecutable();
    this.process = spawn(backendExec, [
      '--port', this.port.toString(),
      '--electron-mode'
    ], {
      env: {
        ...process.env,
        ELECTRON_MODE: 'true',
        DATABASE_PATH: path.join(app.getPath('userData'), 'pocket_musec.db')
      }
    });
    
    // 3. Wait for healthy
    await this.waitForHealthy();
    
    // 4. Monitor health
    this.startHealthCheck();
  }
  
  async stop(): Promise<void> {
    // Graceful shutdown via API
    try {
      await axios.post(`http://localhost:${this.port}/api/shutdown`, {
        timeout: 3000
      });
    } catch (e) {
      // Force kill if graceful fails
      this.process?.kill('SIGTERM');
    }
    
    // Cleanup
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
    }
  }
}
```

**Key Decisions:**
- Use child process (not worker threads) for full isolation
- Dynamic port allocation to avoid conflicts
- Health check endpoint to detect backend readiness
- Graceful shutdown via API endpoint
- Force kill as fallback (timeout after 5s)
- Store logs in userData directory

**Alternatives Considered:**
- **WebWorker**: Not viable - can't spawn Python process from renderer
- **Service Worker**: Wrong abstraction - not for long-running processes
- **Separate app**: Defeats purpose of single-click install

### Decision 4: IPC Security Model

**Architecture:**

```typescript
// electron/preload.ts
import { contextBridge, ipcRenderer } from 'electron';

// Expose limited, secure API to renderer
contextBridge.exposeInMainWorld('electronAPI', {
  // Safe API surface
  getApiUrl: () => ipcRenderer.invoke('get-api-url'),
  openFileDialog: (options) => ipcRenderer.invoke('open-file-dialog', options),
  saveFileDialog: (options) => ipcRenderer.invoke('save-file-dialog', options),
  showNotification: (title, body) => ipcRenderer.invoke('show-notification', title, body),
  
  // Events (one-way)
  onBackendStatus: (callback) => {
    ipcRenderer.on('backend-status', (_event, status) => callback(status));
  }
});
```

**Security Principles:**
1. **Context isolation**: Renderer has no direct access to Node.js APIs
2. **Preload whitelist**: Only expose specific, validated APIs
3. **Input validation**: All IPC arguments validated in main process
4. **No eval**: Never execute renderer-provided code in main process
5. **CSP headers**: Strict Content Security Policy in renderer

**Trade-offs:**
- More boilerplate (preload + IPC handlers)
- But: Much more secure than `nodeIntegration: true`
- Industry best practice (Electron Security Guide)

### Decision 5: Update Strategy

**Architecture:**

```
┌──────────────────────┐
│   GitHub Releases    │  ← Upload artifacts from CI/CD
└──────────┬───────────┘
           │
           │ Check for updates
           ↓
┌──────────────────────┐
│  electron-updater    │  ← Built into app
│  (Auto-updater)      │
└──────────┬───────────┘
           │
           ├─ Download update in background
           ├─ Verify signature (code signed)
           ├─ Notify user
           └─ Install on quit (macOS/Linux)
              or Install immediately (Windows)
```

**Configuration:**

```yaml
# electron-builder.yml
publish:
  provider: github
  owner: your-org
  repo: pocket-musec
  releaseType: release

# Versioning
# Format: MAJOR.MINOR.PATCH (semver)
# Example: 0.4.0 → 0.4.1 (patch), 0.4.1 → 0.5.0 (minor)
```

**Update Flow:**
1. App checks for updates on startup (configurable frequency)
2. If update available, download in background
3. Show notification with release notes
4. User can:
   - "Install Now" (restarts app)
   - "Install on Quit" (default)
   - "Skip This Version"
5. Auto-install on quit (macOS/Linux) or immediately (Windows)

**Rollback Strategy:**
- Keep previous version in `app.asar.bak`
- If new version crashes on startup (3x), auto-rollback
- User can manually "Revert to Previous Version" in Help menu

**Alternatives Considered:**
- **S3 + custom CDN**: More control but more infrastructure
- **Built-in Squirrel**: Lower-level, more complex
- **No auto-update**: Manual downloads - bad UX

**Decision**: Use electron-updater with GitHub Releases

**Rationale:**
- Free hosting via GitHub Releases
- electron-updater is standard, well-tested
- Handles delta updates (smaller downloads)
- Built-in signature verification

### Decision 6: Data Storage Location

**macOS standard location:**

| Component | Location | Example Path |
|-----------|----------|--------------|
| User Data | `~/Library/Application Support/PocketMusec` | `/Users/alice/Library/Application Support/PocketMusec` |
| Logs | `~/Library/Logs/PocketMusec` | `/Users/alice/Library/Logs/PocketMusec` |
| Cache | `~/Library/Caches/PocketMusec` | `/Users/alice/Library/Caches/PocketMusec` |

**Structure:**
```
~/Library/Application Support/PocketMusec/
├── pocket_musec.db           # SQLite database
├── images/                    # Uploaded images
├── config.json                # User settings (via electron-store)
└── backup/                    # Auto-backups (last 7 days)

~/Library/Logs/PocketMusec/
├── electron-main.log         # Main process logs
├── electron-renderer.log      # Renderer process logs
└── backend.log                # Python backend logs
```

**Key Decisions:**
- Use `app.getPath('userData')` for data (standard macOS location)
- Auto-backup database daily (keep 7 days)
- Provide "Show Data Directory" menu item for power users
- Provide "Export/Import Data" for manual backups
- Logs in standard macOS location (`~/Library/Logs/`)

**Migration Path:**
- On first launch, check for existing data in `./data/` (web version)
- Prompt user: "Import existing data?" (Yes / No / Don't ask again)
- If yes, copy database + images to `~/Library/Application Support/PocketMusec/`
- If no, start fresh

### Decision 7: Code Signing and Notarization

**Requirements:**

| Component | Certificate | Cost | Required For |
|-----------|------------|------|--------------|
| Code Signing | Apple Developer ID | $99/year | Gatekeeper acceptance |
| Notarization | Same cert | Included | Gatekeeper approval (required macOS 10.15+) |

**Process:**

1. Sign app with Developer ID certificate during build
2. Submit app to Apple's notary service for notarization
3. Staple notarization ticket to app (allows offline verification)
4. Publish notarized app on GitHub Releases

**CI/CD Integration:**
- Store Developer ID certificate in GitHub Actions secrets (encrypted)
- Sign and notarize during automated builds
- Publish only notarized versions
- Never commit certificates to repo
- Document certificate renewal process (yearly)

**Decision**: Implement full code signing and notarization

**Rationale:**
- Required for user trust and macOS Gatekeeper acceptance
- Notarization is mandatory for macOS 10.15+ (teachers likely on Big Sur or later)
- Critical for professional distribution
- Certificate cost ($99/year) is negligible for a teacher-focused app
- Industry standard for all native macOS apps

## Risks / Trade-offs

### Risk 1: Large Bundle Size (200-300MB)
**Impact:** Slow download on internet < 5Mbps, large disk footprint

**Mitigation:**
- Provide delta updates (only download changed files)
- Optimize PyInstaller bundle (exclude tests, docs, unnecessary dependencies)
- Use ASAR compression for app resources
- Use DMG sparse image to reduce distribution size
- Most teachers on broadband (minimal issue)

**Trade-off accepted:** Simplicity and reliability > small size for v1

### Risk 2: Backend Startup Latency (2-5 seconds)
**Impact:** User must wait 2-5 seconds for backend to start before app is usable

**Mitigation:**
- Show branded splash screen during initialization
- Cache backend health status
- Display progress indicator ("Starting backend...")
- Pre-warm Python runtime in PyInstaller

**Trade-off accepted:** Acceptable for native app (normal for many macOS apps)

### Risk 3: Apple Silicon / Intel Compatibility
**Impact:** App must work on both M1/M2/M3 and Intel Macs

**Mitigation:**
- Build universal binary (arm64 + x86_64 in single executable)
- PyInstaller supports universal binaries natively
- Test on both architectures (use Apple Silicon test machine)
- Robust error handling for architecture mismatches

**Mitigation status:** Well-supported by Electron and PyInstaller

### Risk 4: Code Signing / Notarization Complexity
**Impact:** Certificate management, notarization failures, deployment automation

**Mitigation:**
- Automate signing and notarization in GitHub Actions
- Document certificate renewal process (yearly)
- Implement retry logic for notarization service
- Provide fallback manual signing process
- Test notarization before public release

**Mitigation status:** Standard practice, well-documented

### Risk 5: Update Failures
**Impact:** Users stuck on old versions or failed update installs

**Mitigation:**
- Rollback mechanism for failed updates (keep previous version)
- Manual update option via GitHub Releases
- Robust error handling and user feedback
- Telemetry to detect update failures (crash reporting)
- Staged rollout to catch issues early

**Mitigation status:** electron-updater handles most scenarios

## Migration Plan

### Phase 1: Alpha (Internal Testing)
- Build unsigned versions for all platforms
- Test on team machines
- Fix critical bugs
- Validate feature parity with web version

### Phase 2: Beta (Teacher Testing)
- Build signed versions
- Recruit 5-10 teachers for beta testing
- Collect feedback on UX and stability
- Fix bugs and polish rough edges

### Phase 3: Public Release
- Publish to GitHub Releases
- Announce on website and mailing list
- Provide migration guide for web users
- Monitor crash reports and update metrics

### Phase 4: Ongoing Maintenance
- Regular updates (monthly or as-needed)
- Monitor update adoption rates
- Iterate based on user feedback
- Deprecate web version (optional, TBD)

## Open Questions

### Q1: Mac App Store distribution?

**Options:**
1. Direct download via GitHub Releases (current plan)
2. Mac App Store distribution

**Pros of App Store:**
- Higher discoverability for teachers
- Built-in update mechanism
- Apple stamp of approval

**Cons of App Store:**
- Sandboxing restrictions (may limit file access)
- Review process (slower updates)
- 30% cut of any future monetization (not relevant now)

**Question:** Should we also submit to Mac App Store alongside direct downloads?

**Recommendation:** Start with GitHub Releases (direct download). Evaluate Mac App Store after v1 stabilizes if there's demand for broader discoverability.

### Q2: Should we add telemetry?

**Proposed metrics:**
- Crash reports (anonymized stack traces only)
- App version and macOS version
- Update success/failure rates

**Question:** Is telemetry valuable for improving reliability? Privacy concerns?

**Recommendation:** Add opt-in crash reporting only (Sentry). Display privacy notice at first launch. Avoid usage tracking to respect teacher privacy.

### Q3: Multi-instance support?

**Question:** Should users be able to run multiple instances of the app?

**Options:**
1. Single instance only (simpler, no DB conflicts)
2. Multi-instance (useful for testing, but complex)

**Recommendation:** Single instance only for v1. Use `app.requestSingleInstanceLock()` to enforce. If user tries to launch second instance, focus existing window and show notification.

### Q4: Data location flexibility?

**Question:** Should users be able to choose custom data location?

**Use case:** Teachers may want data on external drive for backup/sync with Time Machine.

**Recommendation:** Default to `~/Library/Application Support/PocketMusec/`, but document that Time Machine backs it up automatically. If requested, provide advanced setting to customize. Warn about performance on network drives.

## Success Metrics

### Performance
- [ ] Bundle size < 300MB per platform
- [ ] Startup time < 5s on typical hardware
- [ ] Memory usage < 500MB idle
- [ ] CPU usage < 5% idle

### Reliability
- [ ] Crash rate < 1% of sessions
- [ ] Update success rate > 95%
- [ ] Backend uptime > 99.9% (auto-restart on crash)

### User Experience
- [ ] 100% feature parity with web version
- [ ] All tests pass on macOS, Windows, Linux
- [ ] No security warnings on signed builds
- [ ] Auto-update completes within 5 minutes

### Adoption (Post-Launch)
- [ ] 50% of active users on desktop app within 3 months
- [ ] Net Promoter Score (NPS) > 40
- [ ] < 10% support tickets related to desktop app
