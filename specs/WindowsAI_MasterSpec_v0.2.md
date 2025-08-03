# Windows AI — Master Spec v0.2 (Windows 11 Only)

**Goal:** A one-click Windows 11 suite called **Windows AI** with a desktop **GUI Command Center**, a **unified actions API** (`POST /plugin/router/act`), **local LLM runtimes** (Ollama/LM Studio/text-generation-webui), a **model router** (LiteLLM Proxy), and plug-in **multi‑agent frameworks** (LangChain, AutoGen, MetaGPT, CrewAI). End‑users do **not** need to code.

---

## 1) Architecture Overview

**GUI (Electron + React)**
- Screens: Chat, Pipelines (node‑based canvas), Agents, Models, Settings, Logs/Jobs.
- First‑run wizard: detect hardware, install/start services, download starter models.

**Background services (Windows Services)**
1) **Router/act (Node/Express, TS)** — `POST /plugin/router/act` with meta‑normalizer; dispatches actions (file/OS/process/package).
2) **AgentHub (FastAPI, Py)** — tools, pipelines, team agents; calls Router + Proxy.
3) **LiteLLM Proxy (Py)** — OpenAI‑compatible router mapping logical names → local/cloud backends.
4) **Ollama** — local LLM runtime; detect LM Studio or text‑gen‑webui if present.
5) **(Optional) TLS terminator** via mkcert (local HTTPS).

**Default ports**: Router 3000 · AgentHub 8000 · Proxy 4000 · Ollama 11434 · LM Studio 1234 · text‑gen‑webui 5000–5005

**Paths (configurable)**: `C:\Windows AI\apps\{gui|router|agenthub|proxy}\`, `models\`, `config\`, `logs\{service}\`, `agents\`, `pipelines\`, `plugins\`, `memory\`

---

## 2) Unified Action API — `/plugin/router/act`

**Normalized request**
```json
{
  "action": "shell",
  "params": {"command": "whoami"},
  "meta": {"timeout_ms":120000, "cwd":"C:\\Windows AI", "elevated": true, "version":"1.0", "request_id":"<uuid>"}
}
```

**Meta‑normalizer**
- Ensure `params {}` exists.
- Aliases: `cmd→command`, `path→filepath`, `dir→directory`, `text→content`, `args→arguments`.
- Clamp `timeout_ms` 1s–10m (default 120s). Invalid `cwd` → fallback to `C:\Windows AI`.
- Unknown `action` → `{ ok:false, error:{ code:"INVALID_ACTION", hint:"..." } }` with `closest_matches`.

**Actions (minimum set)**
`shell`, `read_file`, `write_file`, `delete_file`, `list_directory`, `download_file`, `upload_file`, `run_script` (python|powershell|cmd|node),
`start_process`, `kill_process`, `list_processes`, `install_package` (pip|npm|choco), `uninstall_package`,
`set_env_var` (user|machine|process), `get_env_var`, `get_system_info`, `open_path`.

**Response**
- Success: `{ "ok": true, "result": {...}, "request_id":"<uuid>" }`
- Error: `{ "ok": false, "error": { "code":"X","message":"...", "hint":"..." }, "request_id":"<uuid>" }`

---

## 3) GUI Command Center

- **Chat**: streaming; model selector (logical names); tool‑calls that hit Router/AgentHub.
- **Pipelines**: nodes — LLM, Tool, Script, Branch, Merge, Vote, Webhook; save/load JSON; run as job.
- **Agents**: templates (AutoGen/CrewAI/MetaGPT/LangChain); policies (Local‑only / Fastest / Highest‑quality / Budget‑capped).
- **Models**: discover local backends; download CPU‑friendly models; map logical names in LiteLLM.
- **Settings**: ports/paths/TLS toggle/API keys; start/stop/restart services.
- **Logs/Jobs**: live logs, artifacts, replay.

---

## 4) Installer

- **electron‑builder** → MSI/EXE + auto‑updates.
- `install.ps1` (admin): create paths; install **Ollama**; install **mkcert** (optional TLS); register services (Router via node‑windows; AgentHub & Proxy via NSSM); firewall rules; health checks; summary.
- `uninstall.ps1`: remove services; optional keep `models\`.

---

## 5) Model Router (LiteLLM)

Example `config\proxy.yaml`:
```yaml
model_list:
  - model_name: local/phi3-mini
    litellm_params: { model: "ollama/phi3:mini", api_base: "http://127.0.0.1:11434" }
  - model_name: local/mistral-7b
    litellm_params: { model: "lmstudio/mistral-7b", api_base: "http://127.0.0.1:1234/v1" }
router: { default: "local/phi3-mini" }
```

---

## 6) Security & Logs

- Local TLS (mkcert) toggle; elevation only when `meta.elevated:true`.
- JSONL logs per service under `logs\{service}\` with rotation (30 days).

---

## 7) Acceptance Tests

1) Services healthy: Router 3000, AgentHub 8000, Proxy 4000, Ollama 11434.
2) Actions: `shell`, `read_file`, `write_file`, `get_system_info` pass.
3) Chat via Proxy using a local model streams tokens.
4) Pipeline fan‑out to two models; merge and artifact saved.
5) Installer one‑shot setup; uninstaller cleans up.

---

## 8) CI/CD

- GitHub Actions builds MSI/EXE + service bundles; runs Jest/Pytest; uploads artifacts + checksums.
