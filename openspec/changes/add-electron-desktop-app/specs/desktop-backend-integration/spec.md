# Spec Delta: Desktop Backend Integration

## ADDED Requirements

### Requirement: Backend Process Lifecycle Management
The system SHALL automatically manage the Python backend process lifecycle (start, monitor, stop) as part of the Electron application.

#### Scenario: Backend starts automatically on app launch
- **WHEN** the Electron app launches
- **THEN** the system finds an available port between 8000-9000
- **AND** spawns the Python backend executable with `--port` flag
- **AND** sets ELECTRON_MODE environment variable to "true"
- **AND** waits for backend health check endpoint to respond (200 OK)
- **AND** times out after 30 seconds if backend fails to start

#### Scenario: Backend uses dynamic port allocation (macOS)
- **WHEN** the system starts the backend process on macOS
- **THEN** it scans ports 8000-9000 for availability
- **AND** selects the first available port
- **AND** passes the port to the backend via command-line argument
- **AND** stores the port for renderer process to use
- **AND** handles port conflicts with other macOS applications gracefully

#### Scenario: Backend environment is isolated
- **WHEN** the backend process runs
- **THEN** it uses the bundled Python runtime (not system Python)
- **AND** DATABASE_PATH points to userData directory
- **AND** IMAGE_STORAGE_PATH points to userData/images
- **AND** ELECTRON_MODE flag is set to "true"
- **AND** backend logs to userData/logs/backend.log

#### Scenario: Backend stops gracefully on app quit
- **WHEN** the user quits the Electron app
- **THEN** the app sends POST request to `/api/shutdown` endpoint
- **AND** waits up to 5 seconds for backend to stop gracefully
- **AND** if backend doesn't stop, sends SIGTERM signal
- **AND** if still running after 2 more seconds, sends SIGKILL
- **AND** cleans up any temporary files or resources

### Requirement: Backend Health Monitoring
The system SHALL continuously monitor backend health and restart if necessary.

#### Scenario: Health check during startup
- **WHEN** the backend process is starting
- **THEN** the system polls GET `/health` endpoint every 500ms
- **AND** considers backend healthy when endpoint returns 200 OK
- **AND** retries up to 60 times (30 second timeout)
- **AND** shows "Starting backend..." message to user
- **AND** fails with error dialog if timeout reached

#### Scenario: Continuous health monitoring
- **WHEN** the backend is running
- **THEN** the system polls GET `/health` endpoint every 30 seconds
- **AND** if health check fails, marks backend as unhealthy
- **AND** attempts to reconnect 3 times before restarting backend
- **AND** shows "Reconnecting..." notification to user

#### Scenario: Automatic restart on crash
- **WHEN** the backend process exits unexpectedly (non-zero exit code)
- **THEN** the system logs the crash with exit code and stderr
- **AND** waits 2 seconds before restarting
- **AND** restarts the backend automatically
- **AND** notifies user: "Backend restarted after crash"
- **AND** if crash happens 3 times within 5 minutes, shows error dialog and stops auto-restart

#### Scenario: Backend logs are captured
- **WHEN** the backend process writes to stdout or stderr
- **THEN** the output is captured by the Electron main process
- **AND** written to userData/logs/backend.log
- **AND** log entries include timestamps
- **AND** log rotation keeps last 7 days of logs

### Requirement: IPC Bridge for Backend Communication
The system SHALL provide a secure IPC (Inter-Process Communication) bridge between the Electron renderer and Python backend.

#### Scenario: Renderer gets backend URL
- **WHEN** the renderer process needs to make API requests
- **THEN** it calls `window.electronAPI.getApiUrl()` (from preload script)
- **AND** receives the dynamic backend URL (e.g., `http://localhost:8437`)
- **AND** uses this URL for all HTTP and WebSocket connections
- **AND** the URL is not hardcoded in the frontend

#### Scenario: Backend status events
- **WHEN** the backend status changes (starting, healthy, unhealthy, stopped)
- **THEN** the main process emits `backend-status` IPC event
- **AND** the renderer receives the event via `window.electronAPI.onBackendStatus(callback)`
- **AND** the UI updates to show status (e.g., "Connecting...", "Ready", "Reconnecting...")

#### Scenario: Secure IPC validation
- **WHEN** the renderer sends IPC messages to main process
- **THEN** all arguments are validated for type and structure
- **AND** file paths are restricted to userData directory
- **AND** external URLs are validated against whitelist
- **AND** malformed requests are rejected with error

### Requirement: Python Backend Bundling
The system SHALL bundle the Python backend and all dependencies into a standalone executable using PyInstaller.

#### Scenario: Backend bundles successfully
- **WHEN** the build process runs
- **THEN** PyInstaller creates a single executable from backend code
- **AND** all Python dependencies are included (FastAPI, pdfplumber, etc.)
- **AND** the executable runs on systems without Python installed
- **AND** bundle size is less than 200MB

#### Scenario: Hidden imports are included
- **WHEN** the backend uses dynamic imports (e.g., plugins, optional features)
- **THEN** the PyInstaller spec file includes `hiddenimports` directive
- **AND** all necessary modules are bundled
- **AND** runtime imports work correctly (no ImportError)

#### Scenario: Data files are bundled
- **WHEN** the backend requires data files (e.g., templates, schemas)
- **THEN** the PyInstaller spec includes `datas` directive
- **AND** files are accessible via `sys._MEIPASS` in bundled mode
- **AND** file paths work correctly in both dev and production

#### Scenario: macOS universal binary executable
- **WHEN** building the backend for macOS
- **THEN** PyInstaller produces a universal binary executable (`main`)
- **AND** the executable includes both Apple Silicon (arm64) and Intel (x86_64) code
- **AND** macOS automatically selects the correct architecture at runtime
- **AND** the executable is not cross-compatible with other platforms

### Requirement: Backend Configuration for Desktop Mode
The system SHALL configure the backend differently when running in Electron compared to standalone web mode.

#### Scenario: Backend detects Electron mode
- **WHEN** the backend starts with ELECTRON_MODE environment variable set
- **THEN** it disables auto-reload (no uvicorn --reload)
- **AND** uses the port provided via --port argument
- **AND** logs to file instead of stdout
- **AND** disables CORS (not needed for Electron)
- **AND** exposes graceful shutdown endpoint

#### Scenario: Graceful shutdown endpoint
- **WHEN** the backend receives POST request to `/api/shutdown`
- **THEN** it stops accepting new requests
- **AND** completes in-flight requests (timeout 3 seconds)
- **AND** closes database connections
- **AND** exits with code 0
- **AND** responds with 200 OK before exiting

#### Scenario: Database path in userData
- **WHEN** the backend runs in Electron mode
- **THEN** DATABASE_PATH defaults to `{userData}/pocket_musec.db`
- **AND** the directory is created if it doesn't exist
- **AND** database migrations run automatically on first start
- **AND** database is shared with web version if both are used

### Requirement: Error Handling and Diagnostics
The system SHALL provide detailed error information and recovery options for backend failures.

#### Scenario: Port conflict error
- **WHEN** all ports 8000-9000 are in use
- **THEN** the system shows error dialog: "Unable to start backend. No available ports."
- **AND** provides option to "Quit other applications" or "Retry"
- **AND** logs the port scan results for debugging

#### Scenario: Backend executable missing
- **WHEN** the backend executable is not found in expected location
- **THEN** the system shows error dialog: "Backend executable missing. Please reinstall PocketMusec."
- **AND** provides button to "Download Installer"
- **AND** logs the expected path and actual directory contents

#### Scenario: Python runtime error
- **WHEN** the backend fails to start due to missing Python dependencies
- **THEN** the system captures stderr output
- **AND** shows error dialog with stack trace (if debug mode enabled)
- **AND** provides option to "View Full Logs"
- **AND** logs the error to userData/logs/backend_errors.log

#### Scenario: Backend startup timeout
- **WHEN** the backend doesn't respond to health check within 30 seconds
- **THEN** the system shows error dialog: "Backend is taking longer than expected to start."
- **AND** provides options: "Keep Waiting", "View Logs", "Restart"
- **AND** if user selects "Keep Waiting", extends timeout by 30 seconds

### Requirement: Multi-instance Prevention
The system SHALL prevent multiple instances of the app from running simultaneously to avoid database and port conflicts.

#### Scenario: Second instance attempted
- **WHEN** user tries to launch the app while it's already running
- **THEN** the second instance detects the lock
- **AND** focuses the existing window instead of starting new instance
- **AND** shows notification: "PocketMusec is already running"
- **AND** exits the second instance gracefully

#### Scenario: Instance lock is released on quit
- **WHEN** the app quits normally
- **THEN** the instance lock is released
- **AND** a new instance can be started immediately
- **AND** no orphaned lock files remain

#### Scenario: Stale lock cleanup
- **WHEN** the app crashes without releasing the lock
- **THEN** the next launch detects the stale lock (process ID no longer running)
- **AND** removes the stale lock automatically
- **AND** starts normally without user intervention
