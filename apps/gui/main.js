import { spawn } from 'child_process';
import { app, BrowserWindow, ipcMain, Menu, nativeImage, Tray } from 'electron';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let mainWindow = null;
let tray = null;
let backendProcess = null;
let backendReady = false;

function programData(){ return path.join(process.env.PROGRAMDATA || 'C:\\ProgramData', 'Windows AI'); }
function cfgPath(){ return path.join(programData(), 'config', 'defaults.json'); }
function readConfig(){
  try { return JSON.parse(fs.readFileSync(cfgPath(),'utf8')); } catch { return {}; }
}
function writeConfig(obj){
  const dir = path.dirname(cfgPath()); fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(cfgPath(), JSON.stringify(obj, null, 2), 'utf8');
}

// Backend process management
function getBackendPath() {
  if (app.isPackaged) {
    // Production: backend bundled in resources/backend/
    return path.join(process.resourcesPath, 'backend', 'WindowsAI.exe');
  } else {
    // Development: backend in dist/WindowsAI/
    return path.join(__dirname, '..', '..', 'dist', 'WindowsAI', 'WindowsAI.exe');
  }
}

// Check if backend is already running (dev mode - Python server)
async function checkExistingBackend() {
  try {
    const response = await fetch('http://127.0.0.1:8010/health', {
      signal: AbortSignal.timeout(2000)
    });
    if (response.ok) {
      console.log('[Backend] Existing backend detected on port 8010!');
      return true;
    }
  } catch (err) {
    // No existing backend
  }
  return false;
}

function startBackend() {
  return new Promise(async (resolve) => {
    // First, check if a backend is already running (dev mode)
    const existingBackend = await checkExistingBackend();
    if (existingBackend) {
      console.log('[Backend] Using existing backend server');
      backendReady = true;
      resolve(true);
      return;
    }

    const backendPath = getBackendPath();

    console.log(`[Backend] Attempting to start backend at: ${backendPath}`);

    if (!fs.existsSync(backendPath)) {
      console.error(`[Backend] ERROR: Backend executable not found at ${backendPath}`);
      console.error('[Backend] For development, start backend manually: python -m windows_ai.api.server');
      console.error('[Backend] For production, run: python build_exe.py');
      resolve(false);
      return;
    }

    try {
      backendProcess = spawn(backendPath, ['--api', '--verbose'], {
        detached: false,
        stdio: ['ignore', 'pipe', 'pipe']
      });

      backendProcess.stdout.on('data', (data) => {
        const msg = data.toString().trim();
        console.log(`[Backend] ${msg}`);
        if (msg.includes('Application startup complete') || msg.includes('Uvicorn running')) {
          backendReady = true;
        }
      });

      backendProcess.stderr.on('data', (data) => {
        console.error(`[Backend] ${data.toString().trim()}`);
      });

      backendProcess.on('error', (err) => {
        console.error('[Backend] Failed to start:', err);
        backendProcess = null;
        resolve(false);
      });

      backendProcess.on('exit', (code) => {
        console.log(`[Backend] Process exited with code ${code}`);
        backendProcess = null;
        backendReady = false;
      });

      console.log(`[Backend] Process started with PID: ${backendProcess.pid}`);

      // Wait for backend to be ready
      let attempts = 0;
      const maxAttempts = 30;
      const checkInterval = setInterval(async () => {
        attempts++;
        try {
          const response = await fetch('http://127.0.0.1:8010/health', {
            signal: AbortSignal.timeout(1000)
          });
          if (response.ok) {
            console.log('[Backend] Backend is ready!');
            backendReady = true;
            clearInterval(checkInterval);
            resolve(true);
          }
        } catch (err) {
          if (attempts >= maxAttempts) {
            console.error('[Backend] Timeout waiting for backend to be ready');
            clearInterval(checkInterval);
            resolve(false);
          }
        }
      }, 1000);

    } catch (err) {
      console.error('[Backend] Exception starting backend:', err);
      resolve(false);
    }
  });
}

function stopBackend() {
  if (backendProcess) {
    console.log('[Backend] Stopping backend process...');
    backendProcess.kill();
    backendProcess = null;
    backendReady = false;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100, height: 720,
    webPreferences: { preload: path.join(__dirname, 'preload.js') },
    title: 'Windows AI — Command Center'
  });
  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
}

function createTray() {
  const iconPath = path.join(__dirname, 'renderer', 'icon.png');
  let image; try { image = nativeImage.createFromPath(iconPath); } catch { image = undefined; }
  tray = new Tray(image || nativeImage.createEmpty());
  
  const menu = Menu.buildFromTemplate([
    { 
      label: 'Open Command Center', 
      click: () => { 
        if (!mainWindow) createWindow(); 
        else { mainWindow.show(); mainWindow.focus(); } 
      } 
    },
    { type: 'separator' },
    { 
      label: 'New Conversation', 
      accelerator: 'CmdOrCtrl+N',
      click: () => { 
        if (mainWindow) mainWindow.webContents.send('new-conversation');
      } 
    },
    { 
      label: 'Quick Chat...', 
      accelerator: 'CmdOrCtrl+Shift+C',
      click: () => { 
        if (!mainWindow) createWindow();
        mainWindow.show();
        mainWindow.focus();
        mainWindow.webContents.send('focus-chat-input');
      } 
    },
    { type: 'separator' },
    {
      label: 'Backend Status',
      submenu: [
        { 
          label: 'Start Backend', 
          click: async () => { await startBackend(); } 
        },
        { 
          label: 'Stop Backend', 
          click: () => { stopBackend(); } 
        },
        { 
          label: 'Check Status', 
          click: () => { 
            if (mainWindow) mainWindow.webContents.send('show-backend-status', {
              running: backendProcess !== null,
              ready: backendReady
            });
          } 
        }
      ]
    },
    { type: 'separator' },
    { 
      label: 'Settings', 
      click: () => { 
        if (!mainWindow) createWindow();
        mainWindow.show();
        mainWindow.webContents.send('navigate-to', 'settings');
      } 
    },
    { 
      label: 'Plugins', 
      click: () => { 
        if (!mainWindow) createWindow();
        mainWindow.show();
        mainWindow.webContents.send('navigate-to', 'plugins');
      } 
    },
    { type: 'separator' },
    { 
      label: 'Check for Updates', 
      click: () => { 
        if (mainWindow) mainWindow.webContents.send('check-for-updates');
      } 
    },
    { type: 'separator' },
    { label: 'Quit', role: 'quit' }
  ]);
  
  tray.setToolTip('Windows AI'); 
  tray.setContextMenu(menu);
  
  // Double-click to open
  tray.on('double-click', () => {
    if (!mainWindow) createWindow();
    else { mainWindow.show(); mainWindow.focus(); }
  });
}

app.whenReady().then(async () => {
  console.log('[Main] Starting Windows AI...');

  // Start backend first
  const backendStarted = await startBackend();

  if (!backendStarted) {
    console.warn('[Main] Backend failed to start, but continuing with GUI...');
  }

  // Create GUI
  createWindow();
  createTray();
  
  // Register global shortcuts
  registerGlobalShortcuts();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// Global keyboard shortcuts
async function registerGlobalShortcuts() {
  const { globalShortcut } = await import('electron');
  
  // Toggle window visibility (global hotkey)
  globalShortcut.register('CommandOrControl+Shift+A', () => {
    if (!mainWindow) {
      createWindow();
    } else if (mainWindow.isVisible()) {
      mainWindow.hide();
    } else {
      mainWindow.show();
      mainWindow.focus();
    }
  });
  
  // Quick chat focus (global hotkey)
  globalShortcut.register('CommandOrControl+Shift+Space', () => {
    if (!mainWindow) createWindow();
    mainWindow.show();
    mainWindow.focus();
    mainWindow.webContents.send('focus-chat-input');
  });
  
  console.log('[Main] Global shortcuts registered');
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('quit', () => {
  console.log('[Main] Application quitting, cleaning up...');
  stopBackend();
});

// ===== IPC Handlers =====

// Basic system info
ipcMain.handle('env-info', () => ({ 
  platform: process.platform, 
  arch: process.arch, 
  versions: process.versions,
  appVersion: app.getVersion(),
  electronVersion: process.versions.electron
}));

// Configuration handlers
ipcMain.handle('config:read', () => readConfig());
ipcMain.handle('config:write', (e, obj) => { writeConfig(obj || {}); return { ok: true }; });
ipcMain.handle('settings:get', (e, key) => {
  const config = readConfig();
  return key ? config[key] : config;
});
ipcMain.handle('settings:set', (e, key, value) => {
  const config = readConfig();
  config[key] = value;
  writeConfig(config);
  return { ok: true };
});

// Backend control IPC handlers
ipcMain.handle('backend:start', async () => {
  if (backendProcess) {
    return { success: false, error: 'Backend already running' };
  }
  const started = await startBackend();
  return { success: started };
});

ipcMain.handle('backend:stop', () => {
  stopBackend();
  return { success: true };
});

ipcMain.handle('backend:status', () => ({
  running: backendProcess !== null,
  ready: backendReady,
  pid: backendProcess?.pid || null
}));

// Health check - proxy to backend
ipcMain.handle('health:check', async () => {
  try {
    const response = await fetch('http://127.0.0.1:8010/health', { signal: AbortSignal.timeout(3000) });
    if (response.ok) {
      return await response.json();
    }
    return { status: 'error', message: 'Backend returned non-OK response' };
  } catch (err) {
    return { status: 'error', message: err.message };
  }
});

// Window controls
ipcMain.handle('window:minimize', () => { mainWindow?.minimize(); });
ipcMain.handle('window:maximize', () => { 
  if (mainWindow?.isMaximized()) mainWindow.unmaximize(); 
  else mainWindow?.maximize(); 
});
ipcMain.handle('window:close', () => { mainWindow?.close(); });
ipcMain.handle('window:fullscreen', (e, enable) => { 
  mainWindow?.setFullScreen(enable !== undefined ? enable : !mainWindow.isFullScreen()); 
});

// File operations
ipcMain.handle('file:save', async (e, { defaultPath, filters, content }) => {
  const { dialog } = await import('electron');
  const result = await dialog.showSaveDialog(mainWindow, { defaultPath, filters });
  if (!result.canceled && result.filePath) {
    fs.writeFileSync(result.filePath, content, 'utf8');
    return { success: true, path: result.filePath };
  }
  return { success: false, canceled: true };
});

ipcMain.handle('file:open', async (e, { filters, properties }) => {
  const { dialog } = await import('electron');
  const result = await dialog.showOpenDialog(mainWindow, { filters, properties: properties || ['openFile'] });
  if (!result.canceled && result.filePaths.length > 0) {
    const content = fs.readFileSync(result.filePaths[0], 'utf8');
    return { success: true, path: result.filePaths[0], content };
  }
  return { success: false, canceled: true };
});

ipcMain.handle('file:read', (e, filePath) => {
  try {
    return { success: true, content: fs.readFileSync(filePath, 'utf8') };
  } catch (err) {
    return { success: false, error: err.message };
  }
});

// Shell integration
ipcMain.handle('shell:openExternal', async (e, url) => {
  const { shell } = await import('electron');
  await shell.openExternal(url);
  return { success: true };
});

ipcMain.handle('shell:showItemInFolder', async (e, filePath) => {
  const { shell } = await import('electron');
  shell.showItemInFolder(filePath);
  return { success: true };
});

// Clipboard operations
ipcMain.handle('clipboard:write', async (e, text) => {
  const { clipboard } = await import('electron');
  clipboard.writeText(text);
  return { success: true };
});

ipcMain.handle('clipboard:read', async () => {
  const { clipboard } = await import('electron');
  return clipboard.readText();
});

// App info
ipcMain.handle('app:getVersion', () => app.getVersion());
ipcMain.handle('app:getPath', (e, name) => app.getPath(name));
ipcMain.handle('app:getName', () => app.getName());

// Notifications
ipcMain.handle('notification:show', async (e, { title, body, icon }) => {
  const { Notification } = await import('electron');
  if (Notification.isSupported()) {
    const notification = new Notification({ title, body, icon });
    notification.show();
    return { success: true };
  }
  return { success: false, error: 'Notifications not supported' };
});

// Keyboard shortcuts registration
const registeredShortcuts = new Map();
ipcMain.handle('shortcuts:register', async (e, accelerator, id) => {
  const { globalShortcut } = await import('electron');
  if (registeredShortcuts.has(id)) {
    globalShortcut.unregister(registeredShortcuts.get(id));
  }
  const success = globalShortcut.register(accelerator, () => {
    mainWindow?.webContents.send('shortcut-triggered', id);
  });
  if (success) registeredShortcuts.set(id, accelerator);
  return { success };
});

ipcMain.handle('shortcuts:unregister', async (e, id) => {
  const { globalShortcut } = await import('electron');
  if (registeredShortcuts.has(id)) {
    globalShortcut.unregister(registeredShortcuts.get(id));
    registeredShortcuts.delete(id);
    return { success: true };
  }
  return { success: false, error: 'Shortcut not found' };
});

// Auto-updater handlers (using electron-updater if available)
let autoUpdater = null;
try {
  const { autoUpdater: au } = await import('electron-updater');
  autoUpdater = au;
} catch { /* electron-updater not installed */ }

ipcMain.handle('update:check', async () => {
  if (!autoUpdater) return { available: false, error: 'Auto-updater not available' };
  try {
    const result = await autoUpdater.checkForUpdates();
    return { available: result?.updateInfo?.version !== app.getVersion(), info: result?.updateInfo };
  } catch (err) {
    return { available: false, error: err.message };
  }
});

ipcMain.handle('update:download', async () => {
  if (!autoUpdater) return { success: false, error: 'Auto-updater not available' };
  try {
    await autoUpdater.downloadUpdate();
    return { success: true };
  } catch (err) {
    return { success: false, error: err.message };
  }
});

ipcMain.handle('update:install', () => {
  if (!autoUpdater) return { success: false, error: 'Auto-updater not available' };
  autoUpdater.quitAndInstall();
  return { success: true };
});
