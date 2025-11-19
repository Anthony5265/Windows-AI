# Windows AI — Master Spec v0.0 (Vision & Scope)

**Purpose:** Establish the vision, non-goals, target users, success criteria, and high-level architecture for **Windows AI** — a Windows 11 desktop suite that delivers a GUI Command Center, local-first AI, automations, agents, and an actions engine, with zero required coding.

## Vision
- One click to install; minutes to productive.
- Local-first, privacy-first; cloud keys optional.
- Everything in one place: chat, workflows, agents, and system actions.
- Designed for non-coders while staying powerful for power users.

## Non-Goals (v0.0–v1.x)
- No Linux/Kali deliverables or partitioning topics.
- No mandatory cloud dependency.
- No forced registry hacking or manual service setup.

## Target Users
- Non-coders who want local AI and automations.
- Power users who want a GUI over scripts + optional agent frameworks.

## Success Criteria
- Fresh install → functional chat with a local model.
- Run a file operation from the GUI without touching the CLI.
- Build a 2–3 step automation on a canvas and execute it.

## Top-Level Architecture (preview)
- Electron GUI (Chat, Pipelines, Agents, Models, Settings, Logs).
- Actions API (Node/TS) — system/file/process/package actions.
- AgentHub (FastAPI) — tools + pipelines + agent adapters.
- LiteLLM Proxy — model router to local/cloud backends.
- Local LLM runtime (Ollama), optional LM Studio / text-generation-webui discovery.

## Milestones (high level)
- M1: Services + GUI chat + local model.
- M2: Pipelines + Actions API end-to-end.
- M3: Agents/templates + model router polish.
- M4: Installer + TLS + CI/CD + backups.
