# Task 29: Tray & Global Hotkey Service

**Goal**: Autostart tray app and register a global shortcut that opens the Overlay.

**Scope**
- Electron app with background/tray process
- Register/unregister globalShortcut; configurable key (default Ctrl+Space)
- Tray menu: Open Overlay, Pause AI, Recent Actions, Repair, Quit
- Writes state to `%PROGRAMDATA%\Windows AI\config.json`

**Acceptance**
- Starts on login; tray visible
- Shortcut opens overlay in ≤200ms (warm) & ≤600ms (cold)
- Pause switch halts scheduled/background AI tasks

**Tech hints**: Electron `globalShortcut`, `Tray`; persist in JSON; use Windows startup registry or Startup folder.
