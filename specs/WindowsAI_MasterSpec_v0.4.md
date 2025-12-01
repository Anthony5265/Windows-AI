# Windows AI — Master Spec v0.4 (Windows 11)

**Scope of this update:** Add the **Terminal & Workflows** module to the Windows AI blueprint (Electron GUI + services from v0.3 unchanged).

---

## 0) Context (what already exists from v0.3)

- **Actions API (Node/Express, TS)** — `POST /api/actions/execute` (file/OS/process/package actions, normalizer, structured logs).
- **AgentHub (FastAPI, Py)** — tools, pipelines, adapters to Actions API + LiteLLM Proxy.
- **LiteLLM Proxy (Py)** — OpenAI-compatible gateway mapping logical names to local/cloud backends.
- **Ollama** — local model runtime.
- **GUI (Electron + React)** — Chat, Pipelines, Agents, Models, Settings, Logs/Jobs.
- **Installer** — MSI/EXE + services via node-windows/NSSM, mkcert TLS (optional), firewall rules.

Ports (defaults): Actions 3000, AgentHub 8000, Proxy 4000, Ollama 11434.

---

## 1) Terminal & Workflows Module (new)

### 1.1 Goals
- Provide an **embedded terminal** inside the GUI with themes, keybindings, tabs/splits, and history search.
- Ship a **Workflow Catalog** (YAML) that users can run from a launcher or bind to keys.
- All system-touching workflows pass through the **Actions API** for logging, elevation policy, and safety.

### 1.2 Engine & Libraries
- **Terminal renderer:** `xterm.js` with addons: **fit**, **search**, **web-links**, optional **unicode11**. 
- **PTY integration:** `node-pty` to spawn **PowerShell**, **cmd**, or **bash (WSL)** inside Electron on Windows.
- **Fuzzy search:** `Fuse.js` for searching workflows by title/tags.
- **YAML parsing:** `yaml` (or `js-yaml`) for themes, keysets, and workflow specs.

> Notes for Devs: xterm.js addons list (fit, search, web-links, unicode11) are first-class; node-pty is the Windows-friendly PTY layer; Fuse.js enables fast fuzzy search; YAML libs parse user-supplied theme/keyset/workflow files.

### 1.3 File Layout
```
C:\Windows AI\assets\terminal\
  themes\*.yaml
  keysets\*.yaml
  workflows\**\*.yml
```

### 1.4 Theme Schema (YAML → internal)
```yaml
id: "solarized-dark"
name: "Solarized Dark"
cursorStyle: "block"        # block | underline | bar
fontFamily: "Consolas, 'Fira Code', monospace"
fontSize: 14
opacity: 0.95
palette:
  background: "#002b36"
  foreground: "#93a1a1"
  black: "#073642"
  red: "#dc322f"
  green: "#859900"
  yellow: "#b58900"
  blue: "#268bd2"
  magenta: "#d33682"
  cyan: "#2aa198"
  white: "#eee8d5"
  brightBlack: "#002b36"
  brightRed: "#cb4b16"
  brightGreen: "#586e75"
  brightYellow: "#657b83"
  brightBlue: "#839496"
  brightMagenta: "#6c71c4"
  brightCyan: "#93a1a1"
  brightWhite: "#fdf6e3"
```

### 1.5 Keyset Schema (YAML → internal)
```yaml
id: "default-windowsai"
name: "Windows AI Default"
bindings:
  - when: "terminalFocus"
    key: "Ctrl+Shift+T"
    action: "tab.new"
  - when: "terminalFocus"
    key: "Ctrl+Shift+W"
    action: "tab.close"
  - when: "terminalFocus"
    key: "Ctrl+Shift+D"
    action: "pane.splitRight"
  - when: "terminalFocus"
    key: "Ctrl+Shift+F"
    action: "find.open"        # uses xterm search addon
  - when: "terminalFocus"
    key: "Ctrl+Shift+P"
    action: "workflow.launcher" # open the Workflow Launcher
  - when: "terminalFocus"
    key: "Ctrl+Shift+R"
    action: "workflow.run"
    args: { id: "cleanup-downloads" }
```

**Action mapping (examples):**
- `tab.new`, `tab.next`, `tab.prev`, `tab.close`
- `pane.splitRight`, `pane.splitDown`, `pane.focusNext`, `pane.focusPrev`, `pane.close`
- `find.open`, `find.next`, `find.prev`
- `copy`, `paste`, `selectAll`
- `workflow.launcher`, `workflow.run`

### 1.6 Workflow Spec (YAML)
```yaml
id: "cleanup-downloads"
title: "Clean up Downloads older than 30 days"
tags: ["files", "cleanup", "maintenance"]
description: "Moves files older than 30 days from Downloads to Archive."
inputs:
  - name: "days"
    type: number
    default: 30
  - name: "target"
    type: path
    default: "C:\\Users\\%USERNAME%\\Downloads"
run:
  mode: "action"   # "shell" | "script" | "action"
  action:          # only when mode == "action"
    name: "shell"
    params:
      command: >
        powershell -NoProfile -ExecutionPolicy Bypass -Command
        "Get-ChildItem -Path \"${{target}}\" -File |
         Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-${{days}}) } |
         Move-Item -Destination \"${{target}}\\Archive\" -Force"
```

- `mode: shell` → runs in the active PTY session (visible in terminal).  
- `mode: script` → writes a temp file and executes via `run_script` helper.  
- `mode: action` → invokes **Actions API** with the given action/params (logged, eligible for elevation).

### 1.7 UX
- **Terminal tab** inside GUI with tabbed sessions and split panes.
- **Theme picker** and **Keyset picker** in Terminal settings; instant apply.
- **Workflow Launcher**: Ctrl+Shift+P opens a searchable list (Fuse.js) of workflows by `title`/`tags`; shows details + inputs; **Run** button.  
- **History & Logs**: terminal scrollback; per-run job log entry in **Logs/Jobs**.

### 1.8 Security & Policy
- **System-impacting workflows must use `mode: action`**, which routes through Actions API (logging, elevation policy, timeouts).  
- Shell-mode workflows are allowed but **not elevated** and are marked “untrusted” in logs.  
- Importing external YAML is allowed but gated by a confirmation dialog; the app validates schemas.

### 1.9 Installer Additions
- Create `assets\terminal\{themes,keysets,workflows}` and copy defaults.
- Add sample workflows: `system-info`, `cleanup-downloads`, `git-status-here`.
- Add sample themes/keysets; set **Windows AI Default** at first run.

### 1.10 Telemetry & Logging
- Log terminal events minimally (open/close/split) without keystroke content.
- Each workflow run logs `{id, mode, inputs, result, duration, exit_code}`.

### 1.11 Acceptance Tests
- Load ≥5 themes; apply without reload.
- Apply the default keyset; verify 10 core bindings (tab/pane/find/workflow).
- Run 3 sample workflows (shell/script/action); confirm artifacts/logs.
- `action` workflow honors elevation policy and timeouts.
- Fuzzy search returns expected top 3 matches for a known query.

---

## 2) Interfaces (additions)

### 2.1 Actions API (unchanged contract)
`POST /api/actions/execute` with `{ action, params, meta }`.

### 2.2 AgentHub (new endpoints)
- `POST /workflows/run` → accepts the Workflow Spec + inputs and dispatches to shell/script/action modes using the appropriate adapters.  
  Response mirrors the standard `{ ok, result|error, request_id }` shape.

---

## 3) GUI Additions (Terminal tab)

- **Renderer**: xterm.js + addons (fit/search/weblinks/unicode11 optional).
- **PTY spawns**: default PowerShell; profile select (PowerShell / CMD / WSL).  
- **Settings**: theme, keyset, font, cursor style, opacity, bell, scrollback size, copy-on-select.
- **Workflow Launcher**: searchable list; Run; pin to favorites; show last run status.

---

## 4) Developer Notes

- **xterm.js**: use addons `@xterm/addon-fit`, `@xterm/addon-search`, `@xterm/addon-web-links`; `@xterm/addon-unicode11` optional.  
- **node-pty**: spawn `"powershell.exe"` by default with environment fixups (ensure `SystemRoot` is present).  
- **Fuse.js**: index workflow `title`, `tags`, `id`.  
- **YAML**: prefer `yaml` npm package; `js-yaml` acceptable; validate against our schemas.

---

## 5) Updated Acceptance (Definition of Done summary)

- Terminal tab usable with tabs/splits, themes, keysets, find-in-terminal.
- Workflow catalog loads and runs (shell/script/action).
- Security boundaries enforced (action-mode for elevated/system tasks).
- Installer copies defaults; import/export works.
- Logs/Jobs shows workflow runs.
