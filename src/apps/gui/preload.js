import { contextBridge, ipcRenderer } from 'electron';
contextBridge.exposeInMainWorld('winAI', {
  envInfo: () => ipcRenderer.invoke('env-info'),
  readConfig: () => ipcRenderer.invoke('config:read'),
  writeConfig: (obj) => ipcRenderer.invoke('config:write', obj)
});
