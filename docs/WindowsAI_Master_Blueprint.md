# Windows AI — Master Blueprint (Target)

**What this is:** The ideal end-state plan: GUI Command Center, local-first services (Actions API, AgentHub), model proxy, CI/CD, and self-healing.

## Components (short)
- **GUI (Electron/React)**: Chat, Models, Terminal, Workflows, Logs/Jobs, Settings
- **Actions API (Node/Express)**: OS actions (shell, files, processes) w/ allowlist
- **AgentHub (FastAPI)**: YAML workflow runner, tool registry, artifacts/logs
- **Model Proxy (LiteLLM-compatible)**: logical → local (Ollama/LM Studio) or cloud

## Folders (target)
apps/gui · apps/actions · apps/agenthub · apps/proxy  
assets/workflows · config · scripts · docs

## CI/CD (baseline)
Lint → Test → Build → Upload artifacts; tag → draft release
