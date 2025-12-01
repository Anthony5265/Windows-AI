import { app, BrowserWindow, Tray, Menu, nativeImage, ipcMain } from 'electron';
import path from 'path';
import fs from 'fs';
import os from 'os';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';

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

function startBackend() {
  return new Promise((resolve) => {
    const backendPath = getBackendPath();

    console.log(`[Backend] Attempting to start backend at: ${backendPath}`);

    if (!fs.existsSync(backendPath)) {
      console.error(`[Backend] ERROR: Backend executable not found at ${backendPath}`);
      console.error('[Backend] Please run: python build_exe.py');
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
    { label: 'Open Command Center', click: () => { if (!mainWindow) createWindow(); else mainWindow.show(); } },
    { label: 'Quit', role: 'quit' }
  ]);
  tray.setToolTip('Windows AI'); tray.setContextMenu(menu);
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

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('quit', () => {
  console.log('[Main] Application quitting, cleaning up...');
  stopBackend();
});

// IPC Handlers
ipcMain.handle('env-info', () => ({ platform: process.platform, arch: process.arch, versions: process.versions }));
ipcMain.handle('config:read', () => readConfig());
ipcMain.handle('config:write', (e, obj) => { writeConfig(obj || {}); return { ok:true }; });

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
