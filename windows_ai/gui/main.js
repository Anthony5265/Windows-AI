/**
 * Windows AI - Electron Main Process
 *
 * Handles window management, IPC, and system integration
 */

const { app, BrowserWindow, ipcMain, Tray, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

// Keep a global reference to prevent garbage collection
let mainWindow = null;
let tray = null;
let apiProcess = null;

// API server configuration
const API_PORT = 8000;
const API_HOST = 'localhost';
const API_URL = `http://${API_HOST}:${API_PORT}`;

/**
 * Start the Python API server
 */
function startApiServer() {
    console.log('Starting Windows AI API server...');

    apiProcess = spawn('python', ['-m', 'windows_ai.api.server'], {
        env: { ...process.env, PYTHONUNBUFFERED: '1' }
    });

    apiProcess.stdout.on('data', (data) => {
        console.log(`API: ${data.toString()}`);
    });

    apiProcess.stderr.on('data', (data) => {
        console.error(`API Error: ${data.toString()}`);
    });

    apiProcess.on('close', (code) => {
        console.log(`API server exited with code ${code}`);
    });

    // Wait for API to be ready
    return new Promise((resolve) => {
        setTimeout(resolve, 3000); // Give API 3 seconds to start
    });
}

/**
 * Create the main application window
 */
async function createWindow() {
    // Start API server first
    await startApiServer();

    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 800,
        minHeight: 600,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        icon: path.join(__dirname, 'public', 'icon.png'),
        title: 'Windows AI',
        backgroundColor: '#1e1e1e'
    });

    // Load the app
    mainWindow.loadFile(path.join(__dirname, 'public', 'index.html'));

    // Open DevTools in development
    if (process.argv.includes('--dev')) {
        mainWindow.webContents.openDevTools();
    }

    // Handle window close
    mainWindow.on('close', (event) => {
        if (!app.isQuitting) {
            event.preventDefault();
            mainWindow.hide();
        }
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

/**
 * Create system tray
 */
function createTray() {
    const iconPath = path.join(__dirname, 'public', 'icon.png');

    tray = new Tray(iconPath);

    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'Show Windows AI',
            click: () => {
                if (mainWindow) {
                    mainWindow.show();
                }
            }
        },
        {
            label: 'API Status',
            submenu: [
                { label: `Server: ${API_URL}`, enabled: false },
                { label: 'Open API Docs', click: () => {
                    require('electron').shell.openExternal(`${API_URL}/docs`);
                }}
            ]
        },
        { type: 'separator' },
        {
            label: 'Quit',
            click: () => {
                app.isQuitting = true;
                app.quit();
            }
        }
    ]);

    tray.setContextMenu(contextMenu);
    tray.setToolTip('Windows AI');

    tray.on('click', () => {
        if (mainWindow) {
            mainWindow.show();
        }
    });
}

// IPC Handlers
ipcMain.handle('get-api-url', () => {
    return API_URL;
});

ipcMain.handle('get-plugins', async () => {
    try {
        const axios = require('axios');
        const response = await axios.get(`${API_URL}/api/v1/plugins/`);
        return response.data;
    } catch (error) {
        console.error('Error fetching plugins:', error);
        throw error;
    }
});

ipcMain.handle('execute-plugin', async (event, pluginId, action, params) => {
    try {
        const axios = require('axios');
        const response = await axios.post(
            `${API_URL}/api/v1/plugins/${pluginId}/execute`,
            { action, params }
        );
        return response.data;
    } catch (error) {
        console.error('Error executing plugin:', error);
        throw error;
    }
});

ipcMain.handle('get-system-info', async () => {
    try {
        const axios = require('axios');
        const response = await axios.get(`${API_URL}/api/v1/system/info`);
        return response.data;
    } catch (error) {
        console.error('Error fetching system info:', error);
        throw error;
    }
});

// App lifecycle
app.whenReady().then(() => {
    createWindow();
    createTray();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    // On macOS, keep app running
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    app.isQuitting = true;

    // Stop API server
    if (apiProcess) {
        console.log('Stopping API server...');
        apiProcess.kill();
    }
});

// Handle crashes
process.on('uncaughtException', (error) => {
    console.error('Uncaught exception:', error);
});

console.log('Windows AI Electron app starting...');
