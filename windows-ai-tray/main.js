const { app, Tray, Menu, shell, nativeImage, BrowserWindow, ipcMain, globalShortcut, Notification } = require("electron");
const path = require("path");
const fetch = require("node-fetch");

// Disable hardware acceleration for better compatibility
app.disableHardwareAcceleration();

// Configuration
const BACKEND_URL = "http://127.0.0.1:8010";
const AGENT_URL = "http://127.0.0.1:3001";
const UPDATE_INTERVAL = 10000; // 10 seconds

// Set user data directory
app.setPath("userData", path.join(__dirname, "userdata"));

// Global variables
let tray = null;
let quickCommandWindow = null;
let backendStatus = 'offline';
let lastNotification = null;

// =====================================================================
// Icon Management
// =====================================================================

function getIconPath(status = 'offline') {
  const iconFile = status === 'online' ? 'icon-online.png' :
                   status === 'busy' ? 'icon-busy.png' :
                   'icon-offline.png';

  // Fallback to default icon if specific one doesn't exist
  const iconPath = path.join(__dirname, "assets", iconFile);
  const defaultIconPath = path.join(__dirname, "assets", "icon.png");

  const fs = require('fs');
  return fs.existsSync(iconPath) ? iconPath : defaultIconPath;
}

// =====================================================================
// Quick Command Window
// =====================================================================

function createQuickCommandWindow() {
  if (quickCommandWindow && !quickCommandWindow.isDestroyed()) {
    quickCommandWindow.focus();
    return;
  }

  quickCommandWindow = new BrowserWindow({
    width: 600,
    height: 120,
    frame: false,
    transparent: false,
    resizable: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  quickCommandWindow.loadFile('quick-command.html');

  // Center on screen
  const { screen } = require('electron');
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;
  const winWidth = 600;
  const winHeight = 120;
  quickCommandWindow.setPosition(
    Math.floor((width - winWidth) / 2),
    Math.floor((height - winHeight) / 3) // Upper third of screen
  );

  // Hide when losing focus
  quickCommandWindow.on('blur', () => {
    if (quickCommandWindow && !quickCommandWindow.isDestroyed()) {
      quickCommandWindow.hide();
    }
  });

  quickCommandWindow.on('closed', () => {
    quickCommandWindow = null;
  });
}

function showQuickCommand() {
  if (!quickCommandWindow || quickCommandWindow.isDestroyed()) {
    createQuickCommandWindow();
  } else {
    quickCommandWindow.show();
    quickCommandWindow.focus();
  }
}

// =====================================================================
// Notification System
// =====================================================================

function showNotification(title, body, urgent = false) {
  // Don't spam notifications
  const now = Date.now();
  if (lastNotification && (now - lastNotification) < 3000) {
    return;
  }
  lastNotification = now;

  const notification = new Notification({
    title: title,
    body: body,
    icon: getIconPath(backendStatus),
    urgency: urgent ? 'critical' : 'normal'
  });

  notification.show();

  notification.on('click', () => {
    // Open main GUI when notification is clicked
    openMainGUI();
  });
}

// =====================================================================
// Backend Communication
// =====================================================================

async function callBackend(endpoint, method = 'GET', body = null) {
  try {
    const options = {
      method: method,
      headers: { 'Content-Type': 'application/json' }
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(`${BACKEND_URL}${endpoint}`, options);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Backend call failed: ${endpoint}`, error.message);
    throw error;
  }
}

async function sendQuickMessage(message) {
  try {
    const response = await callBackend('/chat', 'POST', {
      message: message,
      model: 'gpt-3.5-turbo',
      stream: false
    });

    showNotification('AI Response', response.message.content.slice(0, 100) + '...');
    return response;
  } catch (error) {
    showNotification('Error', 'Failed to send message to AI', true);
    throw error;
  }
}

async function getSystemInfo() {
  try {
    const info = await callBackend('/system/info');
    return info;
  } catch (error) {
    return null;
  }
}

// =====================================================================
// Status Monitoring
// =====================================================================

async function checkBackendStatus() {
  try {
    const response = await fetch(`${BACKEND_URL}/health`, { timeout: 5000 });

    if (response.ok) {
      if (backendStatus !== 'online') {
        backendStatus = 'online';
        updateTrayIcon();
        showNotification('Windows AI', 'Backend is now online');
      }
      return true;
    }
  } catch (error) {
    // Backend is offline
  }

  if (backendStatus !== 'offline') {
    backendStatus = 'offline';
    updateTrayIcon();
    showNotification('Windows AI', 'Backend is offline', true);
  }
  return false;
}

function updateTrayIcon() {
  if (tray && !tray.isDestroyed()) {
    const icon = nativeImage.createFromPath(getIconPath(backendStatus));
    tray.setImage(icon);

    const tooltip = backendStatus === 'online'
      ? 'Windows AI - Online'
      : 'Windows AI - Offline (Start backend to connect)';
    tray.setToolTip(tooltip);
  }
}

// =====================================================================
// Main GUI Integration
// =====================================================================

function openMainGUI() {
  // Try to open the main GUI application
  const guiPath = path.join(__dirname, '..', 'gui');

  // Check if GUI is already running by trying to focus it
  // For now, just launch a new instance
  const { spawn } = require('child_process');

  try {
    spawn('npm', ['start'], {
      cwd: guiPath,
      detached: true,
      stdio: 'ignore'
    }).unref();

    showNotification('Windows AI', 'Opening main interface...');
  } catch (error) {
    showNotification('Error', 'Failed to open main interface', true);
  }
}

// =====================================================================
// Menu Builder
// =====================================================================

function buildContextMenu() {
  const isOnline = backendStatus === 'online';

  const template = [
    {
      label: '🚀 Quick Command',
      accelerator: 'Ctrl+Shift+Space',
      click: showQuickCommand,
      enabled: isOnline
    },
    {
      label: '💬 Open Chat',
      click: openMainGUI
    },
    { type: 'separator' },

    // Quick Actions Submenu
    {
      label: '⚡ Quick Actions',
      enabled: isOnline,
      submenu: [
        {
          label: 'What time is it?',
          click: async () => {
            backendStatus = 'busy';
            updateTrayIcon();
            try {
              await sendQuickMessage('What time is it right now?');
            } finally {
              backendStatus = 'online';
              updateTrayIcon();
            }
          }
        },
        {
          label: 'System Information',
          click: async () => {
            try {
              const info = await getSystemInfo();
              if (info) {
                showNotification('System Info', `Platform: ${info.platform || 'Unknown'}`);
              }
            } catch (error) {
              showNotification('Error', 'Failed to get system info', true);
            }
          }
        },
        {
          label: 'List Recent Files',
          click: async () => {
            backendStatus = 'busy';
            updateTrayIcon();
            try {
              await sendQuickMessage('List my most recent files');
            } finally {
              backendStatus = 'online';
              updateTrayIcon();
            }
          }
        },
        {
          label: 'Daily Summary',
          click: async () => {
            backendStatus = 'busy';
            updateTrayIcon();
            try {
              await sendQuickMessage('Give me a brief daily summary');
            } finally {
              backendStatus = 'online';
              updateTrayIcon();
            }
          }
        }
      ]
    },

    { type: 'separator' },

    // Status
    {
      label: `Status: ${backendStatus.toUpperCase()}`,
      enabled: false
    },
    {
      label: 'Check Connection',
      click: async () => {
        await checkBackendStatus();
        tray.setContextMenu(buildContextMenu());
      }
    },

    { type: 'separator' },

    // Settings & Info
    {
      label: 'Open Data Folder',
      click: () => {
        const dataPath = path.join(require('os').homedir(), '.windows-ai');
        shell.openPath(dataPath);
      }
    },
    {
      label: 'Open Logs',
      click: () => {
        const logsPath = path.join(app.getPath('userData'), 'logs');
        shell.openPath(logsPath);
      }
    },

    { type: 'separator' },

    // Help
    {
      label: 'Help',
      submenu: [
        {
          label: 'Getting Started',
          click: () => {
            shell.openPath(path.join(__dirname, '..', 'GETTING_STARTED.md'));
          }
        },
        {
          label: 'About Windows AI',
          click: () => {
            showNotification(
              'Windows AI v0.1.0',
              'Your intelligent Windows assistant'
            );
          }
        }
      ]
    },

    { type: 'separator' },

    {
      label: 'Quit Windows AI',
      accelerator: 'Ctrl+Q',
      click: () => {
        app.quit();
      }
    }
  ];

  return Menu.buildFromTemplate(template);
}

// =====================================================================
// IPC Handlers
// =====================================================================

ipcMain.handle('send-quick-command', async (event, command) => {
  try {
    backendStatus = 'busy';
    updateTrayIcon();

    const response = await sendQuickMessage(command);

    backendStatus = 'online';
    updateTrayIcon();

    return { success: true, response: response };
  } catch (error) {
    backendStatus = backendStatus === 'busy' ? 'online' : backendStatus;
    updateTrayIcon();

    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-status', async () => {
  return { status: backendStatus };
});

// =====================================================================
// App Lifecycle
// =====================================================================

app.on('ready', () => {
  console.log('Windows AI Tray starting...');

  // Create tray icon
  const icon = nativeImage.createFromPath(getIconPath('offline'));
  tray = new Tray(icon);
  tray.setToolTip('Windows AI - Initializing...');
  tray.setContextMenu(buildContextMenu());

  // Double-click to open main GUI
  tray.on('double-click', () => {
    openMainGUI();
  });

  // Register global shortcuts
  const registered = globalShortcut.register('Ctrl+Shift+Space', () => {
    if (backendStatus === 'online') {
      showQuickCommand();
    } else {
      showNotification('Windows AI', 'Backend is offline. Please start the backend first.', true);
    }
  });

  if (!registered) {
    console.error('Global shortcut registration failed');
  }

  // Initial status check
  checkBackendStatus();

  // Set up periodic status updates
  setInterval(async () => {
    await checkBackendStatus();
    tray.setContextMenu(buildContextMenu());
  }, UPDATE_INTERVAL);

  // Show initial notification
  showNotification('Windows AI', 'Tray application started');

  console.log('Windows AI Tray ready!');
});

app.on('will-quit', () => {
  // Unregister all shortcuts
  globalShortcut.unregisterAll();
});

app.on('window-all-closed', (e) => {
  // Prevent app from quitting when all windows are closed
  // Tray app should keep running
  e.preventDefault();
});

// Don't quit when all windows are closed (tray should persist)
app.on('window-all-closed', () => {
  // On macOS it's common for applications to stay open
  // until the user explicitly quits
  if (process.platform !== 'darwin') {
    // Keep running on Windows/Linux
  }
});
