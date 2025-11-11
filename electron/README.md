# PocketMusec Desktop App

Native macOS desktop application for PocketMusec, powered by Electron.

## Features

- **Native macOS Integration**: Full macOS window controls, Dock integration, and menu bar support
- **Automatic Backend Management**: Python backend starts and stops automatically with the app
- **Secure Architecture**: Context isolation, CSP headers, and secure IPC communication
- **System Tray**: Quick access menu in the system tray
- **Dock Menu**: macOS Dock menu with quick actions
- **Comprehensive Logging**: All application events logged to files for debugging
- **Window State Persistence**: Remembers window size and position between sessions

## Development

### Prerequisites

- Node.js 18+
- Python 3.11+
- macOS 10.15+ (for development)

### Setup

1. Install dependencies:
```bash
cd electron
npm install
```

2. Build TypeScript:
```bash
npm run build:electron
```

3. Run in development mode:
```bash
npm run dev:electron
```

### Project Structure

```
electron/
├── src/
│   ├── main.ts              # Main Electron process
│   ├── preload.ts           # Preload script for secure IPC
│   ├── backend-manager.ts   # Python backend lifecycle manager
│   ├── logger.ts            # Application logger
│   └── types/               # TypeScript type definitions
├── dist/                    # Compiled JavaScript output
├── package.json             # Node.js dependencies and scripts
└── tsconfig.json            # TypeScript configuration
```

## Building for Production

### Build Backend Executable

First, create a standalone Python executable using PyInstaller:

```bash
# From project root
pyinstaller pocketmusec-backend.spec
```

This creates a `dist/pocketmusec-backend` executable that bundles:
- Python runtime
- FastAPI server
- All backend dependencies
- PocketFlow AI engine

### Build Electron App

```bash
cd electron

# Build for macOS (creates DMG)
npm run dist:mac

# Build for current platform only (faster)
npm run pack
```

### Outputs

- **DMG installer**: `dist-electron/PocketMusec-1.0.0.dmg`
- **Unpacked app**: `dist-electron/mac/PocketMusec.app`

## Architecture

### Main Process (`main.ts`)

The main Electron process handles:
- Window creation and management
- Backend process lifecycle
- Native menu setup
- System tray integration
- Dock menu (macOS)
- IPC communication with renderer

### Backend Manager (`backend-manager.ts`)

Manages the Python backend:
- Finds available port (8000-9000 range)
- Spawns Python process
- Health check monitoring
- Graceful shutdown
- Auto-restart on failure

### Preload Script (`preload.ts`)

Secure bridge between main and renderer:
- Exposes limited IPC API via `window.electronAPI`
- Context isolation enabled
- No Node.js integration in renderer

### Renderer Process

The React frontend runs in the renderer process:
- Detects Electron environment via `window.electronAPI`
- Uses dynamic backend URL from main process
- All features work identically to web version

## Security

- ✅ Context isolation enabled
- ✅ Node integration disabled in renderer
- ✅ Preload script with limited API surface
- ✅ CSP headers configured
- ✅ Secure IPC communication
- ✅ No remote code execution

## Logging

Application logs are stored in:
- **macOS**: `~/Library/Application Support/PocketMusec/logs/`
- **Windows**: `%APPDATA%/PocketMusec/logs/`

Logs are automatically cleaned after 7 days.

To view logs:
```bash
# macOS
tail -f ~/Library/Application\ Support/PocketMusec/logs/pocketmusec-*.log
```

## Troubleshooting

### Backend Won't Start

Check logs for errors:
```bash
tail -f ~/Library/Application\ Support/PocketMusec/logs/pocketmusec-*.log
```

Common issues:
- Port 8000-9000 range blocked by firewall
- Python dependencies missing
- Database migration failed

### Window Won't Open

Try resetting window state:
```bash
# macOS
rm ~/Library/Application\ Support/PocketMusec/config.json
```

### Backend Crashes

Check backend process:
1. Open PocketMusec
2. Click tray icon → "Backend Status"
3. If not running, check logs for crash details

## Distribution

### Code Signing (macOS)

To distribute the app without security warnings:

1. Get an Apple Developer ID certificate
2. Configure in `electron-builder.yml`:
```yaml
mac:
  identity: "Developer ID Application: Your Name (TEAM_ID)"
```

3. Sign and notarize:
```bash
npm run dist:mac
```

### Auto-Updates

Auto-updates are configured for GitHub Releases:
1. Create a new release on GitHub
2. Upload the DMG file
3. App will auto-check for updates on startup

## Development Tips

### Hot Reload

For faster development, run backend and frontend separately:

```bash
# Terminal 1: Backend
python run_api.py

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Electron (points to existing backend)
cd electron && npm run dev:electron
```

### Debug Mode

Enable Electron DevTools:
- Development: Opens automatically
- Production: `View → Toggle Developer Tools`

### Backend Debugging

Backend logs are visible in Electron console during development:
```bash
npm run dev:electron
# Backend logs appear in terminal
```

## Future Enhancements

- [ ] Auto-updater integration
- [ ] App icon and branding
- [ ] Windows support
- [ ] Linux support (.AppImage)
- [ ] Native notifications
- [ ] Spotlight integration (macOS)
- [ ] Touch Bar support (macOS)

## License

See root LICENSE file.