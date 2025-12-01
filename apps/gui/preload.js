import { contextBridge, ipcRenderer } from 'electron';
contextBridge.exposeInMainWorld('winAI', {
  envInfo: () => ipcRenderer.invoke('env-info'),
  readConfig: () => ipcRenderer.invoke('config:read'),
  writeConfig: (obj) => ipcRenderer.invoke('config:write', obj),
  // Backend process controls
  startBackend: () => ipcRenderer.invoke('backend:start'),
  stopBackend: () => ipcRenderer.invoke('backend:stop'),
  getBackendStatus: () => ipcRenderer.invoke('backend:status')
});
