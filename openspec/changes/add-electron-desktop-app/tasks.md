# Implementation Tasks: Add Electron Desktop App

## 1. Project Setup
- [ ] 1.1 Create `electron/` directory structure
- [ ] 1.2 Initialize `electron/package.json` with dependencies
- [ ] 1.3 Set up TypeScript configuration for Electron
- [ ] 1.4 Configure electron-builder in `electron-builder.yml`
- [ ] 1.5 Add desktop-specific scripts to root package.json
- [ ] 1.6 Add PyInstaller to Python optional dependencies

## 2. Electron Main Process
- [ ] 2.1 Create `electron/main.ts` with basic window management
- [ ] 2.2 Implement window state persistence (size, position)
- [ ] 2.3 Configure security settings (context isolation, CSP)
- [ ] 2.4 Add system tray integration with menu
- [ ] 2.5 Implement native application menu (File, Edit, Help)
- [ ] 2.6 Add keyboard shortcut handlers
- [ ] 2.7 Handle deep links and file associations

## 3. Backend Integration
- [ ] 3.1 Create `electron/backend-manager.ts` for process management
- [ ] 3.2 Implement dynamic port finding (8000-9000 range)
- [ ] 3.3 Bundle Python backend with PyInstaller spec file
- [ ] 3.4 Configure backend to detect Electron mode via env vars
- [ ] 3.5 Add graceful shutdown endpoint to FastAPI app
- [ ] 3.6 Implement backend health check and retry logic
- [ ] 3.7 Handle backend crashes with auto-restart
- [ ] 3.8 Add backend process logging to Electron logs

## 4. IPC Bridge
- [ ] 4.1 Create `electron/preload.ts` with secure IPC API
- [ ] 4.2 Expose file dialog APIs to renderer
- [ ] 4.3 Expose system notifications to renderer
- [ ] 4.4 Add IPC for backend status queries
- [ ] 4.5 Implement secure file system access
- [ ] 4.6 Add shell integration (open external links)

## 5. Frontend Integration
- [ ] 5.1 Detect Electron context in `frontend/src/main.tsx`
- [ ] 5.2 Use dynamic API URL from Electron preload
- [ ] 5.3 Add Electron-specific UI elements (window controls on Linux)
- [ ] 5.4 Implement native file save/open dialogs
- [ ] 5.5 Update Vite config for Electron build target
- [ ] 5.6 Test all existing features in Electron renderer

## 6. Auto-Update Mechanism
- [ ] 6.1 Integrate electron-updater library
- [ ] 6.2 Configure update channel (GitHub Releases)
- [ ] 6.3 Implement update check on startup
- [ ] 6.4 Add update notification UI in renderer
- [ ] 6.5 Handle update download and installation
- [ ] 6.6 Display release notes before update
- [ ] 6.7 Implement rollback mechanism for failed updates
- [ ] 6.8 Add settings toggle for auto-update frequency

## 7. macOS-Specific Features

- [ ] 7.1 Configure app icon and bundle identifier (e.g., `com.pocketmusec.app`)
- [ ] 7.2 Implement Dock menu with quick actions (New Lesson, Open Data, Quit)
- [ ] 7.3 Configure menu bar (hide/show on launch, minimize to menu bar option)
- [ ] 7.4 Handle macOS dark mode (respects system settings)
- [ ] 7.5 Implement native macOS window styling (rounded corners, traffic lights)
- [ ] 7.6 Add native menu bar menu (File, Edit, View, Help)
- [ ] 7.7 Configure code signing with Apple Developer ID certificate
- [ ] 7.8 Configure app notarization for Gatekeeper compliance
- [ ] 7.9 Create DMG installer with drag-and-drop UI
- [ ] 7.10 Test on Apple Silicon (M1/M2/M3) and Intel Macs

## 8. Build & Distribution (macOS Only)
- [ ] 8.1 Create GitHub Actions workflow for macOS builds
- [ ] 8.2 Configure code signing secrets in GitHub Actions (Apple Developer ID)
- [ ] 8.3 Configure notarization secrets in GitHub Actions (Apple ID, app-specific password)
- [ ] 8.4 Implement automated app signing and notarization in CI/CD
- [ ] 8.5 Configure artifact upload to GitHub Releases
- [ ] 8.6 Test build artifacts on clean macOS machines (Apple Silicon and Intel)
- [ ] 8.7 Verify notarization status (gatekeeper acceptance)
- [ ] 8.8 Create release checklist document
- [ ] 8.9 Document manual build process for local development
- [ ] 8.10 Document certificate renewal process (yearly Apple Developer ID)

## 9. Data & Settings Management
- [ ] 9.1 Define user data directory per platform
- [ ] 9.2 Implement data migration from web version
- [ ] 9.3 Use electron-store for app settings
- [ ] 9.4 Share database location with backend
- [ ] 9.5 Handle concurrent web/desktop access (file locking)
- [ ] 9.6 Add "Open Data Directory" menu option
- [ ] 9.7 Implement data export/import for backup

## 10. Error Handling & Logging
- [ ] 10.1 Set up Electron logging to files
- [ ] 10.2 Capture and log backend errors
- [ ] 10.3 Implement crash reporter (Sentry or built-in)
- [ ] 10.4 Add error boundary for renderer crashes
- [ ] 10.5 Create user-friendly error dialogs
- [ ] 10.6 Add "Report Issue" menu item with logs
- [ ] 10.7 Implement debug mode toggle

## 11. Testing (macOS Only)
- [ ] 11.1 Set up Playwright or Spectron for E2E tests
- [ ] 11.2 Test window management (open, close, minimize, maximize, fullscreen)
- [ ] 11.3 Test Dock integration (menu, badges, recent items)
- [ ] 11.4 Test menu bar integration (hide/show, minimize to menu bar)
- [ ] 11.5 Test backend lifecycle (start, stop, restart)
- [ ] 11.6 Test IPC communication security
- [ ] 11.7 Test auto-update flow (mock GitHub releases)
- [ ] 11.8 Test code signing and notarization (verify no Gatekeeper warnings)
- [ ] 11.9 Test all Milestone 2 features in desktop app
- [ ] 11.10 Test all Milestone 3 features in desktop app
- [ ] 11.11 Test on Apple Silicon (M1/M2/M3)
- [ ] 11.12 Test on Intel Macs
- [ ] 11.13 Test memory leaks and resource cleanup
- [ ] 11.14 Load testing (long-running lesson generation sessions)
- [ ] 11.15 Test macOS dark mode compatibility

## 12. Documentation
- [ ] 12.1 Write `docs/ELECTRON_SETUP_MACOS.md` for developers
- [ ] 12.2 Update main README with macOS desktop app info
- [ ] 12.3 Create user guide for macOS app features (Dock, menu bar, Cmd+key shortcuts)
- [ ] 12.4 Document macOS build process (dev and release)
- [ ] 12.5 Document Apple Developer ID certificate setup and renewal
- [ ] 12.6 Document macOS app notarization process
- [ ] 12.7 Create troubleshooting guide for macOS-specific issues
- [ ] 12.8 Add macOS app screenshots to documentation (light and dark mode)
- [ ] 12.9 Write release notes template for updates
- [ ] 12.10 Document code signing and notarization CI/CD setup

## 13. Performance Optimization
- [ ] 13.1 Optimize bundle size (remove unused dependencies, minimize app size)
- [ ] 13.2 Implement lazy loading for renderer modules
- [ ] 13.3 Use ASAR compression for app resources
- [ ] 13.4 Optimize PyInstaller bundle (exclude tests, docs, dev dependencies)
- [ ] 13.5 Cache backend health check status
- [ ] 13.6 Implement branded splash screen for perceived performance
- [ ] 13.7 Profile startup time on both Apple Silicon and Intel
- [ ] 13.8 Optimize bottlenecks (Python import time, backend startup)
- [ ] 13.9 Test on older Macs (minimum: macOS 10.15 with 8GB RAM)

## 14. Security Audit
- [ ] 14.1 Review Electron security checklist (context isolation, CSP, etc.)
- [ ] 14.2 Audit IPC API surface for vulnerabilities
- [ ] 14.3 Verify context isolation is enabled
- [ ] 14.4 Test CSP headers in renderer
- [ ] 14.5 Verify nodeIntegration is disabled
- [ ] 14.6 Scan npm and Python dependencies for vulnerabilities
- [ ] 14.7 Test against common Electron exploits
- [ ] 14.8 Verify code signing chain integrity
- [ ] 14.9 Implement secure update verification (signature checking)
- [ ] 14.10 Document security considerations for users
- [ ] 14.11 Security test on clean macOS machine

## 15. Polish & UX (macOS)
- [ ] 15.1 Design and add macOS app icons (1024x1024, PNG, darkmode support)
- [ ] 15.2 Create branded splash screen with PocketMusec logo
- [ ] 15.3 Add loading states for backend initialization ("Starting backend...")
- [ ] 15.4 Implement graceful degradation if backend unavailable
- [ ] 15.5 Add first-run welcome screen (intro to Dock menu, keyboard shortcuts)
- [ ] 15.6 Implement in-app changelog viewer (What's New in Help menu)
- [ ] 15.7 Add keyboard shortcut help (Cmd+? or Help menu)
- [ ] 15.8 Polish macOS native notifications
- [ ] 15.9 Test accessibility features (VoiceOver, keyboard navigation, zoom)
- [ ] 15.10 Verify dark mode styling (light and dark theme)
- [ ] 15.11 Test with system font sizes and accessibility settings
- [ ] 15.12 Conduct beta testing with 5-10 macOS teachers
- [ ] 15.13 Gather feedback on macOS integration and UX

## Dependencies
- Requires: `implement-milestone2-web-interface` (frontend - React/TypeScript)
- Requires: `implement-milestone3-advanced-features` (complete feature set)
- Enhances: All existing features via native macOS app experience

## Milestone Completion

**Target**: After all tasks are completed, update task status:
- Run final verification on macOS (both Apple Silicon and Intel)
- Confirm all success criteria are met
- Mark all tasks as complete: `- [x]`
- Update proposal.md status: DRAFT → APPROVED → IN_PROGRESS → COMPLETE
