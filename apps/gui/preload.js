/**
 * Windows AI - Electron Preload Script
 * Exposes secure APIs to the renderer process
 */

import { contextBridge, ipcRenderer } from 'electron';

// Expose all APIs to renderer process securely
contextBridge.exposeInMainWorld('winAI', {
  // Environment info
  envInfo: () => ipcRenderer.invoke('env-info'),
  
  // Configuration
  readConfig: () => ipcRenderer.invoke('config:read'),
  writeConfig: (obj) => ipcRenderer.invoke('config:write', obj),
  
  // Backend process controls
  startBackend: () => ipcRenderer.invoke('backend:start'),
  stopBackend: () => ipcRenderer.invoke('backend:stop'),
  getBackendStatus: () => ipcRenderer.invoke('backend:status'),
  
  // Workflow operations
  saveWorkflow: (workflow) => ipcRenderer.invoke('save-workflow', workflow),
  loadWorkflow: () => ipcRenderer.invoke('load-workflow'),
  executeWorkflow: (workflow) => ipcRenderer.invoke('execute-workflow', workflow),
  
  // File operations
  selectFile: (options) => ipcRenderer.invoke('dialog:openFile', options),
  selectDirectory: () => ipcRenderer.invoke('dialog:openDirectory'),
  saveFile: (options) => ipcRenderer.invoke('dialog:saveFile', options),
  readFile: (path) => ipcRenderer.invoke('file:read', path),
  writeFile: (path, content) => ipcRenderer.invoke('file:write', path, content),
  
  // Window controls
  minimize: () => ipcRenderer.send('window:minimize'),
  maximize: () => ipcRenderer.send('window:maximize'),
  close: () => ipcRenderer.send('window:close'),
  setAlwaysOnTop: (flag) => ipcRenderer.send('window:setAlwaysOnTop', flag),
  
  // Tray operations
  showTray: () => ipcRenderer.send('tray:show'),
  hideTray: () => ipcRenderer.send('tray:hide'),
  updateTrayTooltip: (text) => ipcRenderer.send('tray:updateTooltip', text),
  
  // Notifications
  showNotification: (title, body, options) => 
    ipcRenderer.invoke('notification:show', { title, body, ...options }),
  
  // Clipboard
  copyToClipboard: (text) => ipcRenderer.invoke('clipboard:write', text),
  readFromClipboard: () => ipcRenderer.invoke('clipboard:read'),
  
  // Shell operations
  openExternal: (url) => ipcRenderer.invoke('shell:openExternal', url),
  openPath: (path) => ipcRenderer.invoke('shell:openPath', path),
  
  // Update operations
  checkForUpdates: () => ipcRenderer.invoke('update:check'),
  downloadUpdate: () => ipcRenderer.invoke('update:download'),
  installUpdate: () => ipcRenderer.invoke('update:install'),
  
  // Event listeners - for main to renderer communication
  onBackendStatusChange: (callback) => {
    ipcRenderer.on('backend:statusChange', (event, status) => callback(status));
    return () => ipcRenderer.removeListener('backend:statusChange', callback);
  },
  onUpdateAvailable: (callback) => {
    ipcRenderer.on('update:available', (event, info) => callback(info));
    return () => ipcRenderer.removeListener('update:available', callback);
  },
  onUpdateProgress: (callback) => {
    ipcRenderer.on('update:progress', (event, progress) => callback(progress));
    return () => ipcRenderer.removeListener('update:progress', callback);
  },
  onDeepLink: (callback) => {
    ipcRenderer.on('deep-link', (event, url) => callback(url));
    return () => ipcRenderer.removeListener('deep-link', callback);
  },
  onTrayAction: (callback) => {
    ipcRenderer.on('tray:action', (event, action) => callback(action));
    return () => ipcRenderer.removeListener('tray:action', callback);
  },
  
  // App info
  getAppVersion: () => ipcRenderer.invoke('app:version'),
  getAppPath: (name) => ipcRenderer.invoke('app:getPath', name),
  isPackaged: () => ipcRenderer.invoke('app:isPackaged'),
  
  // Platform info
  platform: process.platform,
  arch: process.arch,
  
  // Debug/dev tools
  openDevTools: () => ipcRenderer.send('devtools:open'),
  reloadApp: () => ipcRenderer.send('app:reload'),
  
  // Keyboard shortcuts
  registerShortcut: (accelerator, callback) => 
    ipcRenderer.invoke('shortcut:register', accelerator),
  unregisterShortcut: (accelerator) => 
    ipcRenderer.invoke('shortcut:unregister', accelerator),
  onShortcut: (callback) => {
    ipcRenderer.on('shortcut:triggered', (event, accelerator) => callback(accelerator));
    return () => ipcRenderer.removeListener('shortcut:triggered', callback);
  },
  
  // Tray navigation events
  onNavigate: (callback) => {
    ipcRenderer.on('navigate-to', (event, tabId) => callback(tabId));
    return () => ipcRenderer.removeListener('navigate-to', callback);
  },
  onFocusChatInput: (callback) => {
    ipcRenderer.on('focus-chat-input', () => callback());
    return () => ipcRenderer.removeListener('focus-chat-input', callback);
  },
  onNewConversation: (callback) => {
    ipcRenderer.on('new-conversation', () => callback());
    return () => ipcRenderer.removeListener('new-conversation', callback);
  },
  onBackendStatus: (callback) => {
    ipcRenderer.on('show-backend-status', (event, status) => callback(status));
    return () => ipcRenderer.removeListener('show-backend-status', callback);
  },
  onCheckForUpdates: (callback) => {
    ipcRenderer.on('check-for-updates', () => callback());
    return () => ipcRenderer.removeListener('check-for-updates', callback);
  }
});

// Also expose a legacy electronAPI for compatibility
contextBridge.exposeInMainWorld('electronAPI', {
  invoke: (channel, ...args) => ipcRenderer.invoke(channel, ...args),
  send: (channel, ...args) => ipcRenderer.send(channel, ...args),
  on: (channel, callback) => {
    const subscription = (event, ...args) => callback(...args);
    ipcRenderer.on(channel, subscription);
    return () => ipcRenderer.removeListener(channel, subscription);
  }
});
