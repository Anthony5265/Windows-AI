/**
 * Windows AI - Electron Preload Script
 *
 * Safely exposes IPC to renderer process
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use IPC
contextBridge.exposeInMainWorld('windowsAI', {
    // Get API URL
    getApiUrl: () => ipcRenderer.invoke('get-api-url'),

    // Plugin operations
    getPlugins: () => ipcRenderer.invoke('get-plugins'),
    executePlugin: (pluginId, action, params) =>
        ipcRenderer.invoke('execute-plugin', pluginId, action, params),

    // System operations
    getSystemInfo: () => ipcRenderer.invoke('get-system-info'),

    // Version info
    versions: {
        node: process.versions.node,
        chrome: process.versions.chrome,
        electron: process.versions.electron
    }
});

console.log('Windows AI preload script loaded');
