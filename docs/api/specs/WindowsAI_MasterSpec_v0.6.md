# Windows AI — Master Spec v0.6
Date: 2025-08-03
Owner: Anthony (Product), Windows AI Team (Engineering)
Status: Draft (ready for Codex build)

## 0) What is this release?
v0.6 evolves Windows AI from a single desktop app into an **OS-level AI layer** with:
- **Global hotkey + overlay** (AI everywhere)
- **Explorer right‑click actions**
- **Clipboard & screenshot AI**
- **Voice (STT/TTS)** for hands‑free control
- **Local index/search ("recall")** — opt‑in
- **Notifications/toasts** for long‑running jobs
- **OOBE + Self‑heal + Privacy/Policy Center**
- **Mesh expansion** across home devices (Tailscale/ZeroTier) with optional **distributed inference** (Petals or vLLM/Ray)
- **Local‑first** by default; cloud keys optional

> NOTE: Firmware/driver updates are offered only when supported by the **Windows UEFI Firmware Update Platform** or trusted vendor utilities. We never flash unknown binaries. See “Installer Constraints.”

## 1) User experience summary
- **Ctrl+Space** (default) opens a fast **Command Palette Overlay** anywhere.
- **Explorer → “Run with Windows AI”** to summarize/extract/rename/convert/agent‑run on selected files/folders.
- **System Tray** shows status, recent actions, a **Pause AI** privacy switch, and “Repair” link.
- **Clipboard/Screenshot AI**: summarize, OCR, translate, extract tables (CSV), redact PII (rules).
- **Voice**: push‑to‑talk; local STT, local TTS; commands route to Workflows/Agents.
- **Recall (opt‑in)**: index chosen folders; semantic search; exclude lists; redaction.
- **Mesh**: add devices; model & job routing across nodes; optional distributed modes.
- **No coding required**; advanced users can edit YAML workflows or add agents.

## 2) Architecture (high level)
**Services**
- **Actions API** (Node/TS): file/process/network actions with logging and policy gates.
- **AgentHub** (Python): orchestrates tools/agents; talks to Actions API + Model Router.
- **Model Router** (LiteLLM Proxy): one OpenAI‑compatible endpoint across local/cloud.
- **Local LLM runtime** (Ollama): default offline engine; REST on localhost:11434.
- **Electron App**: Control Center (Chat, Workflows, Terminal, Settings) + **Tray** + **Overlay**.
- **OS hooks**: Global hotkey (Electron globalShortcut), Explorer menu (IExplorerCommand or registry fallback).
- **Observability**: ETW events + OpenTelemetry (Node/Python), local dashboard optional.

**Mesh & scale**
- **Default**: secure mesh via **Tailscale** or **ZeroTier**; nodes auto‑register; router schedules jobs to best node.
- **Advanced**: **Petals** (layer‑sharded distributed inference) and **vLLM with Ray** (multi‑node serving). Recommend WSL2/Linux for GPU collectives; Windows uses Gloo backend.

## 3) Installer & first‑run (must‑have behavior)
**Pre‑flight detection**
- OS/build, admin, PowerShell execution policy
- CPU (AVX, cores), RAM, free disk per path
- GPU & driver (NVIDIA CUDA present?), fall back to CPU/DirectML
- Network: offline/online; proxy; port conflicts (3000/4000/8000/11434 auto‑resolve)
- Existing installs of Node/Python/Ollama; Windows firewall status

**Decisions**
- **Models**: choose a small CPU model by default; enable GPU model if NVIDIA + VRAM OK.
- **Ports**: find open ports; write to shared config.
- **Services**: install Actions API, AgentHub, Router, Ollama as **Windows Services**.
- **TLS**: optional mkcert for local HTTPS; else HTTP on localhost.
- **Firewall**: create Private‑profile rules for chosen ports.

**First‑run wizard**
- Verify services; test a chat; run a sample workflow; set hotkey; choose privacy mode.
- Offer **Repair** which restarts services, rebinds ports, reissues certs, checks models.

**Constraints**
- Firmware steps only via Windows UEFI Firmware Update Platform / vendor packages.
- No unsigned drivers; no kernel patching.

## 4) Modules & acceptance
### 4.1 Tray & Global Hotkey
- Autostarts; tray shows status, last 5 actions, pause toggle.
- Registers global shortcut; launches overlay in ≤200ms on a mid‑tier PC.

### 4.2 Overlay / Command Palette
- Fuzzy search over **Actions, Workflows, Agents, Files**.
- Runs a workflow with parameters; preview result; “apply” (copy/insert/run).

### 4.3 Explorer Context Menu
- Adds “Run with Windows AI” for files/folders with verbs: Summarize, Extract Data (CSV/JSON), Rename via Pattern, Send to Agent.
- Passes full paths to Actions API; supports multi‑select; modern menu (IExplorerCommand) with classic registry fallback.

### 4.4 Indexer & Recall (opt‑in)
- Watches user‑selected folders. Stores embeddings + metadata locally.
- Search returns relevant files/snippets with path + timestamp + preview.
- Controls: Exclusions, redaction rules, pause switch.

### 4.5 Clipboard & Screenshot AI
- Global shortcuts for “Summarize clipboard”, “OCR area”, “Extract tables”.
- Works offline; redaction rules applied.

### 4.6 Voice (STT/TTS)
- Push‑to‑talk; local STT (whisper.cpp); local TTS (Piper).
- Commands map to actions/workflows; playback via system device.

### 4.7 Notifications / Toasts
- Long jobs show progress + completion toasts; deep‑link to logs/results.

### 4.8 OOBE Wizard
- Screens: Models, Privacy, Shortcuts, Context Menus, Mesh (optional).
- All steps succeed on offline machines (model pack can be deferred/imported).

### 4.9 Self‑Heal & Diagnostics
- One click: restart services, rebind ports, reinstall services, re‑download models, reset configs.
- Export diagnostics bundle (configs + recent logs).

### 4.10 Policy & Safety Center
- Local‑only mode, retention limits, redaction filters, allowlist of folders/tools.
- Logs viewer with “clear all”. Kill switch (pause all agents).

### 4.11 Mesh Expansion
- Join/leave mesh; discover peers; sync model catalog; route jobs to best node.
- Optional: start **Petals** node / join Petals swarm; **vLLM** cluster recipes under WSL2.

## 5) Performance targets
- Overlay open: ≤200ms warm, ≤600ms cold.
- Local chat (CPU 3B): first token ≤2s on 8‑core; ≳10 tok/s on mid NVIDIA GPU.
- Indexer: ≤10k files/hour on SSD (text & PDFs with OCR).

## 6) Non‑goals (v0.6)
- No vendor‑agnostic firmware flashing; no kernel‑mode drivers.
- No cloud dependence; all cloud keys optional.

## 7) Deliverables
- New services, overlay UI, context menus
- Config + logs + policies
- Installer update + Repair tool
- Smoke tests for overlay, context menu, voice, recall, mesh

## 8) Risk notes
- Context menu support differs across Win11 builds; provide registry fallback.
- Distributed GPU collectives (NCCL) not supported on native Windows; recommend WSL2/Linux for clusters.
- Indexer privacy: off by default; strict exclusions; easy wipe.

