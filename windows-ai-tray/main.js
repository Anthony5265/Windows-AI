const { app, Tray, Menu, shell, nativeImage } = require("electron");
const path = require("path");

const HOST = "127.0.0.1";
const PORT = 15777;
const BASE = `http://${HOST}:${PORT}`;

app.setPath("userData", path.join(__dirname, "userdata")); // reduce cache permission issues

function iconPath() {
  return path.join(__dirname, "assets", "icon.png");
}

async function callAgent(pathname, payload) {
  const url = `${BASE}${pathname}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload||{})
  });
  if (!res.ok) throw new Error(`${pathname} ${res.status}`);
  return await res.json();
}

function buildMenu(tray) {
  const template = [
    {
      label: "Ask: 'hello from tray'",
      click: async () => {
        try { await callAgent("/ask", { prompt: "hello from tray" }); tray.setToolTip("Asked AI"); }
        catch (e) { tray.setToolTip("Ask failed"); }
      }
    },
    {
      label: "Run: 'Get-Process | Select -First 1'",
      click: async () => {
        try { await callAgent("/sh", { command: "Get-Process | Select-Object -First 1 Name,CPU" }); tray.setToolTip("Command sent"); }
        catch (e) { tray.setToolTip("Command failed"); }
      }
    },
    { type: "separator" },
    {
      label: "Open Agent Logs",
      click: () => shell.openPath(path.join(__dirname, "..", "windows-ai-agent", "logs"))
    },
    {
      label: "Restart Agent Task",
      click: async () => {
        const { exec } = require("child_process");
        exec('schtasks /End /TN "WindowsAIAgent" & schtasks /Run /TN "WindowsAIAgent"');
      }
    },
    { type: "separator" },
    { label: "Quit", role: "quit" }
  ];
  return Menu.buildFromTemplate(template);
}

let tray;
app.whenReady().then(() => {
  const img = nativeImage.createFromPath(iconPath());
  tray = new Tray(img);
  tray.setContextMenu(buildMenu(tray));
  tray.setToolTip("Windows AI");

  // Health ping
  const ping = async () => {
    try {
      const res = await fetch(`${BASE}/health`);
      if (res.ok) tray.setToolTip("Windows AI: online");
      else tray.setToolTip("Windows AI: degraded");
    } catch {
      tray.setToolTip("Windows AI: offline");
    }
  };
  ping();
  setInterval(ping, 5000);
});
