# Windows AI — Master Spec v0.7 (Mesh + Deep Windows Integration)
Date: 2025-08-03

Purpose: Windows-only, no-code AI workstation with mesh expansion across devices, deep OS integration, and a one‑click smart installer.

Outcomes
- Smart installer probes hardware + chooses CUDA/DirectML/CPU
- Unified OpenAI-compatible router (LiteLLM) to Ollama (11434), llama.cpp server, vLLM (WSL2)
- Optional mesh via Tailscale/ZeroTier; distributed inference via Petals or Ray+vLLM (advanced)
- Electron UI (Chat, Agents, Files, Automations, Models, Mesh), global hotkey + tray
- Explorer context menu, Windows Toast notifications, winget bootstrap
- OpenTelemetry + Windows Event Log channel; diagnostics bundle

Architecture
- Electron shell + Node backend + Python worker
- Backends pluggable; all normalized through router
- Agents: JSON manifests + TS skills, background queue
- Mesh helpers; device tags; TLS via VPN
- Observability: OTEL SDKs, file logs, ETW/EventLog

Security
- Local-first, strict egress toggle, DPAPI secrets
- Clear model source + license banners

Success
- Install → first chat ≤ 10 min
- No typing during install; offline after downloads
- Single endpoint swap models live
