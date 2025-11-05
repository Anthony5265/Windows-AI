const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// IPC safely without exposing the entire IPC module
contextBridge.exposeInMainWorld('quickCommandAPI', {
  sendCommand: (command) => ipcRenderer.invoke('send-quick-command', command),
  hideWindow: () => ipcRenderer.send('hide-quick-command'),
  getStatus: () => ipcRenderer.invoke('get-status')
});

console.log('Quick Command preload script loaded');
