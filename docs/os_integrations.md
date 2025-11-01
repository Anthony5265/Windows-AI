# OS Integrations

Prototypes in `ui.os_integrations` demonstrate how Windows AI features
could surface inside familiar shell experiences.

## Installing helpers

Run the setup script to register hotkeys and context menu entries:

```powershell
scripts/setup-os-integrations.ps1
```

The script adds:

* **Ctrl+Alt+E** – launch the AI File Explorer
* **Ctrl+Alt+T** – launch the AI Terminal
* Right‑click background menu entries to open either prototype in the
  current folder

## Launching manually

You can also start the prototypes directly with Python:

```bash
python -m ui.os_integrations.file_explorer
python -m ui.os_integrations.terminal
```

Both windows are built with PySide6 and include placeholder areas where
AI‑powered suggestions could be added later.
