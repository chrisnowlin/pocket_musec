import { app, BrowserWindow, Menu, shell, ipcMain, dialog, Tray, nativeImage } from 'electron';
import * as path from 'path';
import Store from 'electron-store';
import { BackendManager } from './backend-manager';
import { logger } from './logger';

// Initialize store for app settings
const store = new Store();

class PocketMusecApp {
  private mainWindow: BrowserWindow | null = null;
  private isQuitting = false;
  private backendManager: BackendManager;
  private tray: Tray | null = null;

  constructor() {
    this.backendManager = new BackendManager();
    this.initializeApp();
  }

  private initializeApp(): void {
    logger.info('Initializing PocketMusec application', {
      version: app.getVersion(),
      platform: process.platform,
      arch: process.arch,
      electronVersion: process.versions.electron,
      nodeVersion: process.versions.node
    });

    // Set app user model ID for Windows
    if (process.platform === 'win32') {
      app.setAppUserModelId('com.pocketmusec.app');
    }

    // Clean old logs
    logger.cleanOldLogs(7);

    // Handle uncaught exceptions
    process.on('uncaughtException', (error) => {
      logger.error('Uncaught exception', error);
      dialog.showErrorBox('Application Error', `An unexpected error occurred: ${error.message}`);
    });

    process.on('unhandledRejection', (reason) => {
      logger.error('Unhandled promise rejection', reason);
    });

    // App event handlers
    app.whenReady().then(() => this.onReady());
    app.on('window-all-closed', this.onWindowAllClosed.bind(this));
    app.on('activate', this.onActivate.bind(this));
    app.on('before-quit', this.onBeforeQuit.bind(this));

    // Auto-updater disabled for development
    // autoUpdater.on('update-available', this.onUpdateAvailable.bind(this));
    // autoUpdater.on('update-downloaded', this.onUpdateDownloaded.bind(this));
    // autoUpdater.on('error', this.onUpdateError.bind(this));

    // IPC handlers
    this.setupIpcHandlers();
  }

  private async onReady(): Promise<void> {
    try {
      logger.info('Application ready, starting initialization');
      
      // Start backend first
      logger.info('Starting backend server');
      const backendPort = await this.backendManager.start();
      logger.info(`Backend started successfully on port ${backendPort}`);
      
      // Then create main window
      logger.info('Creating main window');
      await this.createMainWindow(backendPort);
      this.setupMenu();
      this.setupTray();
      this.setupDock();
      
      logger.info('Application startup complete');
      
      // Check for updates disabled in development
      // setTimeout(() => {
      //   autoUpdater.checkForUpdatesAndNotify();
      // }, 5000);
    } catch (error) {
      logger.error('Failed to start application', error);
      dialog.showErrorBox('Startup Error', `Failed to start PocketMusec: ${(error as Error).message}`);
      app.quit();
    }
  }

  private async createMainWindow(backendPort: number): Promise<void> {
    // Get stored window state or use defaults
    const windowState = store.get('windowState', {
      width: 1200,
      height: 800,
      x: undefined,
      y: undefined
    }) as { width: number; height: number; x?: number; y?: number };

    // Create the browser window
    this.mainWindow = new BrowserWindow({
      width: windowState.width,
      height: windowState.height,
      x: windowState.x,
      y: windowState.y,
      minWidth: 800,
      minHeight: 600,
      show: false, // Don't show until ready-to-show
      titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js'),
        webSecurity: true,
        additionalArguments: [
          `--electron-version=${app.getVersion()}`,
          `--backend-port=${backendPort}`
        ]
      }
    });

    // Save window state on resize/move
    this.mainWindow.on('resize', this.saveWindowState.bind(this));
    this.mainWindow.on('move', this.saveWindowState.bind(this));

    // Handle window close
    this.mainWindow.on('close', (event) => {
      if (process.platform === 'darwin' && !this.isQuitting) {
        event.preventDefault();
        this.mainWindow?.hide();
      }
    });

    // Load the app
    const isDev = !app.isPackaged;
    if (isDev) {
      // In development, load from Vite dev server
      await this.mainWindow.loadURL('http://localhost:5173');
      this.mainWindow.webContents.openDevTools();
    } else {
      // In production, load from built files
      const indexPath = path.join(__dirname, '../../frontend/dist/index.html');
      await this.mainWindow.loadFile(indexPath);
    }

    // Show window when ready
    this.mainWindow.once('ready-to-show', () => {
      this.mainWindow?.show();
      
      if (isDev) {
        this.mainWindow?.webContents.openDevTools();
      }
    });

    // Handle external links
    this.mainWindow.webContents.setWindowOpenHandler(({ url }) => {
      shell.openExternal(url);
      return { action: 'deny' };
    });
  }

  private saveWindowState(): void {
    if (!this.mainWindow) return;

    const bounds = this.mainWindow.getBounds();
    store.set('windowState', {
      width: bounds.width,
      height: bounds.height,
      x: bounds.x,
      y: bounds.y
    });
  }

  private setupMenu(): void {
    const template: Electron.MenuItemConstructorOptions[] = [
      {
        label: 'PocketMusec',
        submenu: [
          { role: 'about', label: 'About PocketMusec' },
          { type: 'separator' },
          { role: 'services', label: 'Services' },
          { type: 'separator' },
          { role: 'hide', label: 'Hide PocketMusec' },
          { role: 'hideOthers', label: 'Hide Others' },
          { role: 'unhide', label: 'Show All' },
          { type: 'separator' },
          { role: 'quit', label: 'Quit PocketMusec' }
        ]
      },
      {
        label: 'File',
        submenu: [
          {
            label: 'New Lesson',
            accelerator: 'CmdOrCtrl+N',
            click: () => {
              this.mainWindow?.webContents.send('menu-new-lesson');
            }
          },
          {
            label: 'Open Data Directory',
            click: async () => {
              const dataDir = app.getPath('userData');
              await shell.openPath(dataDir);
            }
          },
          { type: 'separator' },
          { role: 'quit', label: 'Quit' }
        ]
      },
      {
        label: 'Edit',
        submenu: [
          { role: 'undo', label: 'Undo' },
          { role: 'redo', label: 'Redo' },
          { type: 'separator' },
          { role: 'cut', label: 'Cut' },
          { role: 'copy', label: 'Copy' },
          { role: 'paste', label: 'Paste' },
          { role: 'selectAll', label: 'Select All' }
        ]
      },
      {
        label: 'View',
        submenu: [
          { role: 'reload', label: 'Reload' },
          { role: 'forceReload', label: 'Force Reload' },
          { role: 'toggleDevTools', label: 'Toggle Developer Tools' },
          { type: 'separator' },
          { role: 'resetZoom', label: 'Actual Size' },
          { role: 'zoomIn', label: 'Zoom In' },
          { role: 'zoomOut', label: 'Zoom Out' },
          { type: 'separator' },
          { role: 'togglefullscreen', label: 'Toggle Full Screen' }
        ]
      },
      {
        label: 'Window',
        submenu: [
          { role: 'minimize', label: 'Minimize' },
          { role: 'close', label: 'Close' }
        ]
      },
      {
        label: 'Help',
        submenu: [
          {
            label: 'About PocketMusec',
            click: async () => {
              await dialog.showMessageBox(this.mainWindow!, {
                type: 'info',
                title: 'About PocketMusec',
                message: 'PocketMusec',
                detail: `AI-powered lesson planning assistant for music teachers\n\nVersion: ${app.getVersion()}\nElectron: ${process.versions.electron}\nNode.js: ${process.versions.node}\nPlatform: ${process.platform}`
              });
            }
          },
          {
            label: 'Check for Updates',
            click: () => {
              console.log('Update checking disabled in development');
            }
          },
          {
            label: 'Learn More',
            click: async () => {
              await shell.openExternal('https://pocketmusec.com');
            }
          }
        ]
      }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
  }

  private setupTray(): void {
    // Only show tray on macOS and Windows
    if (process.platform === 'linux') {
      return;
    }

    // Create a simple icon for the tray (using a text icon for now)
    // In production, this would use a proper icon file
    const icon = nativeImage.createFromDataURL(
      'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAGvSURBVFhH7ZbBSsNAEIb/pIq9ePLgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD148ePHgxYMXD14AAAAASUVORK5CYII='
    );
    
    this.tray = new Tray(icon);
    
    const contextMenu = Menu.buildFromTemplate([
      {
        label: 'Show PocketMusec',
        click: () => {
          this.mainWindow?.show();
          this.mainWindow?.focus();
        }
      },
      { type: 'separator' },
      {
        label: 'New Lesson',
        click: () => {
          this.mainWindow?.show();
          this.mainWindow?.webContents.send('menu-new-lesson');
        }
      },
      { type: 'separator' },
      {
        label: 'Backend Status',
        click: () => {
          const status = this.backendManager.getStatus();
          const message = status.isRunning 
            ? `Backend running on port ${status.port} (PID: ${status.pid})`
            : 'Backend is not running';
          dialog.showMessageBox(this.mainWindow!, {
            type: 'info',
            title: 'Backend Status',
            message,
            buttons: ['OK']
          });
        }
      },
      { type: 'separator' },
      {
        label: 'Quit PocketMusec',
        click: () => {
          this.isQuitting = true;
          app.quit();
        }
      }
    ]);
    
    this.tray.setToolTip('PocketMusec - Music Education Assistant');
    this.tray.setContextMenu(contextMenu);
    
    // On macOS, clicking the tray icon should show/hide the window
    if (process.platform === 'darwin') {
      this.tray.on('click', () => {
        if (this.mainWindow?.isVisible()) {
          this.mainWindow.hide();
        } else {
          this.mainWindow?.show();
          this.mainWindow?.focus();
        }
      });
    }
  }

  private setupDock(): void {
    // Dock menu is macOS only
    if (process.platform !== 'darwin') {
      return;
    }

    const dockMenu = Menu.buildFromTemplate([
      {
        label: 'New Lesson',
        click: () => {
          this.mainWindow?.show();
          this.mainWindow?.webContents.send('menu-new-lesson');
        }
      },
      {
        label: 'Open Data Directory',
        click: async () => {
          const dataDir = app.getPath('userData');
          await shell.openPath(dataDir);
        }
      },
      { type: 'separator' },
      {
        label: 'Backend Status',
        click: () => {
          const status = this.backendManager.getStatus();
          const message = status.isRunning 
            ? `Backend running on port ${status.port}`
            : 'Backend is not running';
          dialog.showMessageBox(this.mainWindow!, {
            type: 'info',
            title: 'Backend Status',
            message,
            buttons: ['OK']
          });
        }
      }
    ]);

    app.dock?.setMenu(dockMenu);
  }

  private setupIpcHandlers(): void {
    // Handle app version request
    ipcMain.handle('app:getVersion', () => {
      return app.getVersion();
    });

    // Handle platform info
    ipcMain.handle('app:getPlatform', () => {
      return process.platform;
    });

    // Handle backend status
    ipcMain.handle('backend:getStatus', () => {
      return this.backendManager.getStatus();
    });

    // Handle backend restart
    ipcMain.handle('backend:restart', async () => {
      return await this.backendManager.restart();
    });

    // Handle show save dialog
    ipcMain.handle('dialog:showSaveDialog', async (event, options) => {
      const result = await dialog.showSaveDialog(this.mainWindow!, options);
      return result;
    });

    // Handle show open dialog
    ipcMain.handle('dialog:showOpenDialog', async (event, options) => {
      const result = await dialog.showOpenDialog(this.mainWindow!, options);
      return result;
    });

    // Handle app quit
    ipcMain.handle('app:quit', () => {
      this.isQuitting = true;
      app.quit();
    });
  }

  private onWindowAllClosed(): void {
    // On macOS, keep app running even when all windows are closed
    if (process.platform !== 'darwin') {
      app.quit();
    }
  }

  private onActivate(): void {
    // On macOS, re-create window when dock icon is clicked
    if (BrowserWindow.getAllWindows().length === 0) {
      this.createMainWindow(8000);
    } else if (this.mainWindow) {
      this.mainWindow.show();
    }
  }

  private async onBeforeQuit(): Promise<void> {
    this.isQuitting = true;
    await this.backendManager.stop();
  }

// Update methods disabled for development

  private onUpdateDownloaded(info: any): void {
    this.mainWindow?.webContents.send('update-downloaded', info);
  }

  private onUpdateError(error: Error): void {
    console.error('Update error:', error);
    this.mainWindow?.webContents.send('update-error', error.message);
  }
}

// Create and run the app
new PocketMusecApp();