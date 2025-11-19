const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { exec } = require('child_process');
const fetch = require('node-fetch');

// Disable hardware acceleration for better compatibility
app.disableHardwareAcceleration();

// Configuration
const BACKEND_URL = 'http://127.0.0.1:8010';
const CONFIG_PATH = path.join(process.env.APPDATA || process.env.HOME, 'WindowsAI', 'config.json');

let mainWindow = null;

// =====================================================================
// Window Creation
// =====================================================================

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 700,
    resizable: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets', 'icon.png')
  });

  mainWindow.loadFile('wizard.html');

  // Remove menu bar
  mainWindow.setMenuBarVisibility(false);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// =====================================================================
// App Lifecycle
// =====================================================================

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// =====================================================================
// IPC Handlers
// =====================================================================

// Check if backend is running
ipcMain.handle('check-backend', async () => {
  try {
    const response = await fetch(`${BACKEND_URL}/health`, { timeout: 3000 });
    return response.ok;
  } catch (error) {
    return false;
  }
});

// Check if Ollama is installed
ipcMain.handle('check-ollama', async () => {
  return new Promise((resolve) => {
    exec('ollama --version', (error, stdout) => {
      if (error) {
        resolve({ installed: false, version: null });
      } else {
        const version = stdout.trim();
        resolve({ installed: true, version });
      }
    });
  });
});

// List Ollama models
ipcMain.handle('list-ollama-models', async () => {
  return new Promise((resolve) => {
    exec('ollama list', (error, stdout) => {
      if (error) {
        resolve([]);
      } else {
        const lines = stdout.trim().split('\n').slice(1); // Skip header
        const models = lines.map(line => {
          const parts = line.split(/\s+/);
          return { name: parts[0], size: parts[1] };
        }).filter(m => m.name);
        resolve(models);
      }
    });
  });
});

// Download Ollama model
ipcMain.handle('download-ollama-model', async (event, modelName) => {
  return new Promise((resolve) => {
    const process = exec(`ollama pull ${modelName}`);

    process.stdout.on('data', (data) => {
      event.sender.send('ollama-download-progress', data.toString());
    });

    process.on('close', (code) => {
      resolve({ success: code === 0 });
    });
  });
});

// Save configuration
ipcMain.handle('save-config', async (event, config) => {
  try {
    // Ensure directory exists
    const configDir = path.dirname(CONFIG_PATH);
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true });
    }

    // Save config
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2));

    // Also try to send config to backend if running
    try {
      await fetch(`${BACKEND_URL}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
        timeout: 5000
      });
    } catch (err) {
      console.log('Backend not running, config saved locally only');
    }

    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Load existing configuration
ipcMain.handle('load-config', async () => {
  try {
    if (fs.existsSync(CONFIG_PATH)) {
      const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
      return config;
    }
    return null;
  } catch (error) {
    return null;
  }
});

// Open external URL
ipcMain.handle('open-external', async (event, url) => {
  const { shell } = require('electron');
  shell.openExternal(url);
  return { success: true };
});

// Check for IoT devices
ipcMain.handle('discover-iot-devices', async () => {
  try {
    const response = await fetch(`${BACKEND_URL}/integrations/iot/discover`, {
      timeout: 10000
    });
    if (response.ok) {
      return await response.json();
    }
    return { discovered: 0, devices: [] };
  } catch (error) {
    return { discovered: 0, devices: [] };
  }
});

// Test API key
ipcMain.handle('test-api-key', async (event, provider, apiKey) => {
  // Simple validation for now
  if (!apiKey || apiKey.length < 10) {
    return { valid: false, error: 'API key too short' };
  }

  // Provider-specific prefix checks
  const prefixes = {
    openai: 'sk-',
    anthropic: 'sk-ant-',
    google: 'AIza'
  };

  if (prefixes[provider] && !apiKey.startsWith(prefixes[provider])) {
    return { valid: false, error: `Invalid ${provider} API key format` };
  }

  return { valid: true };
});
