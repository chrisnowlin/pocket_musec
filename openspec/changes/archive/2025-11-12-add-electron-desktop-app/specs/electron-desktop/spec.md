# Spec Delta: Electron Desktop

## ADDED Requirements

### Requirement: Desktop Application Shell
The system SHALL provide a native desktop application built with Electron that packages the entire PocketMusec stack (frontend, backend, Python runtime) into a single executable for macOS, Windows, and Linux.

#### Scenario: Application launches successfully
- **WHEN** user double-clicks the PocketMusec app icon
- **THEN** the application window opens within 5 seconds
- **AND** the backend process starts automatically
- **AND** the frontend loads and connects to the backend
- **AND** no technical setup or manual process management is required

#### Scenario: Application window management
- **WHEN** user interacts with the application window
- **THEN** native window controls (minimize, maximize, close) work correctly
- **AND** window size and position persist across app restarts
- **AND** the window can be moved between displays
- **AND** the application respects OS-specific window behavior (snap, full-screen)

#### Scenario: Application quits gracefully
- **WHEN** user closes the application window or quits via menu
- **THEN** the backend process receives shutdown signal
- **AND** the backend stops gracefully within 5 seconds
- **AND** all resources are cleaned up (no zombie processes)
- **AND** user data is saved before exit

### Requirement: Menu Bar Integration
The system SHALL provide macOS menu bar integration for quick access to common actions and status information.

#### Scenario: Menu bar icon appears
- **WHEN** the application is running
- **THEN** a PocketMusec icon appears in the macOS menu bar (top-right area)
- **AND** clicking the icon shows a context menu
- **AND** the menu includes "Show Window", "Generate Lesson", "Settings", and "Quit" options

#### Scenario: Menu bar quick actions
- **WHEN** user selects "Generate Lesson" from menu bar menu
- **THEN** the application window opens (if hidden)
- **AND** the lesson generation flow starts immediately
- **AND** the action completes without requiring additional clicks

#### Scenario: Dock integration
- **WHEN** the application is running
- **THEN** the app appears in the macOS Dock with the PocketMusec icon
- **AND** right-clicking the Dock icon shows menu: "New Lesson", "Open Data Directory", "Quit"
- **AND** the Dock icon shows a badge when updates are available

### Requirement: Native Menus and Keyboard Shortcuts
The system SHALL provide native application menus (File, Edit, View, Help) with keyboard shortcuts appropriate to each platform.

#### Scenario: File menu actions
- **WHEN** user opens the File menu
- **THEN** options include "New Lesson" (Cmd+N / Ctrl+N), "Open Data Directory", "Export Lesson" (Cmd+E / Ctrl+E), "Import Data", and "Quit" (Cmd+Q / Ctrl+Q)
- **AND** all shortcuts work correctly
- **AND** shortcuts follow platform conventions (Cmd on macOS, Ctrl on Windows/Linux)

#### Scenario: Help menu actions
- **WHEN** user opens the Help menu
- **THEN** options include "View Documentation", "Check for Updates", "View Logs", "Report Issue", and "About PocketMusec"
- **AND** selecting "About" shows app version, Electron version, and license info

#### Scenario: Keyboard shortcuts work globally
- **WHEN** user presses Cmd+N (macOS) or Ctrl+N (Windows/Linux)
- **THEN** the new lesson flow starts regardless of which UI element has focus
- **AND** shortcuts work even when window is in background (if OS permits)

### Requirement: macOS-Native Behaviors
The system SHALL implement macOS-native features and behaviors that match user expectations for professional macOS applications.

#### Scenario: macOS keyboard conventions
- **WHEN** the user presses standard macOS key combinations
- **THEN** Cmd+W closes the window
- **AND** Cmd+Q quits the application
- **AND** Cmd+N creates a new lesson
- **AND** Cmd+S saves the current lesson
- **AND** Cmd+, opens Settings
- **AND** Cmd+H hides the window
- **AND** Cmd+M minimizes the window

#### Scenario: Dark mode support
- **WHEN** the macOS system is in dark mode
- **THEN** the app respects the system setting automatically
- **AND** all UI elements render correctly in dark theme
- **AND** text contrast meets accessibility standards
- **AND** the app works seamlessly in light/dark/auto modes

#### Scenario: macOS window styling
- **WHEN** the app window is open
- **THEN** the window has rounded corners (standard macOS style)
- **AND** the traffic light buttons (red, yellow, green) appear in top-left
- **AND** the window responds to macOS Exposé and Mission Control
- **AND** the app supports macOS full-screen mode

### Requirement: Security and Sandboxing
The system SHALL implement Electron security best practices to protect users from malicious code execution.

#### Scenario: Context isolation enabled
- **WHEN** the renderer process loads
- **THEN** context isolation is enabled (contextIsolation: true)
- **AND** Node.js integration is disabled in renderer (nodeIntegration: false)
- **AND** remote module is disabled
- **AND** only whitelisted IPC APIs are exposed via preload script

#### Scenario: Content Security Policy enforced
- **WHEN** the frontend loads in the Electron renderer
- **THEN** a strict Content Security Policy is enforced
- **AND** inline scripts are not allowed (nonce or hash required)
- **AND** external resources must be from whitelisted domains
- **AND** eval() and related functions are disabled

#### Scenario: Secure IPC communication
- **WHEN** the renderer communicates with the main process via IPC
- **THEN** all IPC arguments are validated in the main process
- **AND** only whitelisted IPC channels are allowed
- **AND** user-provided data is sanitized before use in native APIs
- **AND** file system access is restricted to app data directory

### Requirement: Resource Management
The system SHALL manage system resources efficiently to avoid excessive memory, CPU, or disk usage.

#### Scenario: Memory usage within limits
- **WHEN** the application is idle (no lesson generation)
- **THEN** memory usage is less than 500MB
- **WHEN** generating a lesson
- **THEN** memory usage is less than 1GB
- **AND** memory is released after lesson generation completes

#### Scenario: CPU usage within limits
- **WHEN** the application is idle
- **THEN** CPU usage is less than 5% on typical hardware
- **WHEN** generating a lesson
- **THEN** CPU usage is less than 50% per core
- **AND** CPU usage returns to idle levels after completion

#### Scenario: Disk space management
- **WHEN** the application stores data
- **THEN** total disk usage (excluding images) is less than 100MB
- **AND** log files are rotated daily and kept for 7 days
- **AND** old backups are automatically deleted after 7 days
- **AND** users can manually clean up data via Settings

### Requirement: Error Handling and Recovery
The system SHALL handle errors gracefully and provide recovery mechanisms for common failure scenarios.

#### Scenario: Backend process crashes
- **WHEN** the backend process crashes unexpectedly
- **THEN** the app detects the crash within 5 seconds
- **AND** the backend process restarts automatically
- **AND** users see a notification: "Reconnecting to backend..."
- **AND** the UI reconnects once backend is healthy

#### Scenario: Backend fails to start
- **WHEN** the backend process fails to start (port conflict, missing dependencies)
- **THEN** the app shows a user-friendly error dialog
- **AND** the error message includes troubleshooting steps
- **AND** the dialog provides options: "Retry", "Open Logs", "Report Issue"
- **AND** selecting "Retry" attempts to start backend on a different port

#### Scenario: Unhandled renderer crash
- **WHEN** the renderer process crashes due to unexpected error
- **THEN** the app logs the crash with stack trace
- **AND** the window reloads automatically
- **AND** users see a notification: "Something went wrong. The app has been reloaded."
- **AND** after 3 consecutive crashes, the app offers to reset settings

### Requirement: Logging and Diagnostics
The system SHALL provide comprehensive logging for debugging and support purposes.

#### Scenario: Logs are written to files
- **WHEN** the application runs
- **THEN** logs are written to the userData directory
- **AND** separate log files exist for main process, renderer process, and backend
- **AND** log files are rotated daily with max size of 10MB
- **AND** logs include timestamps, log levels (debug, info, warn, error), and context

#### Scenario: Users can access logs
- **WHEN** user selects "View Logs" from Help menu
- **THEN** the app opens the log directory in the system file manager
- **AND** the most recent log file is highlighted
- **AND** users can copy logs for support tickets

#### Scenario: Debug mode available
- **WHEN** user enables debug mode in Settings
- **THEN** verbose logging is enabled for all processes
- **AND** the Electron DevTools open automatically
- **AND** network requests are logged with full details
- **AND** debug mode persists across app restarts until disabled
