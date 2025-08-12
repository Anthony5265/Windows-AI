import { app, BrowserWindow, Tray, Menu, nativeImage, ipcMain } from 'electron';
import path from 'path';
import fs from 'fs';
import os from 'os';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let mainWindow = null;
let tray = null;

function programData(){ return path.join(process.env.PROGRAMDATA || 'C:\\ProgramData', 'Windows AI'); }
function cfgPath(){ return path.join(programData(), 'config', 'defaults.json'); }
function readConfig(){
  try { return JSON.parse(fs.readFileSync(cfgPath(),'utf8')); } catch { return {}; }
}
function writeConfig(obj){
  const dir = path.dirname(cfgPath()); fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(cfgPath(), JSON.stringify(obj, null, 2), 'utf8');
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

app.whenReady().then(() => { createWindow(); createTray(); app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); }); });
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });

ipcMain.handle('env-info', () => ({ platform: process.platform, arch: process.arch, versions: process.versions }));
ipcMain.handle('config:read', () => readConfig());
ipcMain.handle('config:write', (e, obj) => { writeConfig(obj || {}); return { ok:true }; });
