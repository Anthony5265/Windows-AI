# Windows AI — Master Spec v0.3 (Windows 11, Clean Slate)

**Change from v0.2:** Remove all “Assistant Builder” references; replace `/plugin/router/act` with neutral **`POST /api/actions/execute`**.

---

## 1) Services & Ports
- **Actions API (Node/Express, TS)** — 3000 — `POST /api/actions/execute`
- **AgentHub (FastAPI, Py)** — 8000
- **LiteLLM Proxy (Py)** — 4000
- **Ollama** — 11434
Paths as in v0.2 under `C:\Windows AI\...`

## 2) Actions API Contract
Request:
```json
{ "action":"<name>", "params":{}, "meta": { "timeout_ms":120000, "cwd":"C:\\Windows AI", "elevated":false, "request_id":"<uuid>" } }
```
Actions list and responses identical to v0.2.

## 3) GUI / Installer / Security
Same features as v0.2; only the endpoint name changes in code, GUI adapters, and docs.

## 4) Acceptance
- `/api/actions/execute` works for `shell/read/write/get_system_info`.
- GUI uses new endpoint and passes tests from v0.2.
