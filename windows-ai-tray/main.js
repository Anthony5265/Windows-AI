const { app, Tray, Menu, BrowserWindow } = require('electron');

let tray, win;
function createWindow(){
  win = new BrowserWindow({ width: 480, height: 360, show: false });
  win.loadFile('index.html');
}
app.whenReady().then(() => {
  createWindow();
  tray = new Tray(null);
  tray.setToolTip('Windows AI');
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Open', click: () => { win.show(); } },
    { label: 'Quit', role: 'quit' }
  ]));
});
