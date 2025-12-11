const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  checkBackend: () => ipcRenderer.invoke('check-backend'),
  checkOllama: () => ipcRenderer.invoke('check-ollama'),
  listOllamaModels: () => ipcRenderer.invoke('list-ollama-models'),
  downloadOllamaModel: (modelName) => ipcRenderer.invoke('download-ollama-model', modelName),
  saveConfig: (config) => ipcRenderer.invoke('save-config', config),
  loadConfig: () => ipcRenderer.invoke('load-config'),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  discoverIoTDevices: () => ipcRenderer.invoke('discover-iot-devices'),
  testApiKey: (provider, apiKey) => ipcRenderer.invoke('test-api-key', provider, apiKey),

  // Listen for download progress
  onOllamaDownloadProgress: (callback) => {
    ipcRenderer.on('ollama-download-progress', (event, data) => callback(data));
  },

  // Remove listener
  removeOllamaDownloadListener: () => {
    ipcRenderer.removeAllListeners('ollama-download-progress');
  }
});
