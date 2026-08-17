# Windows-AI — Canonical AI Development Blueprint

> **THIS IS THE SINGLE SOURCE OF TRUTH FOR DEVELOPING WINDOWS-AI.**
>
> Every AI coding agent, assistant, or developer working on this repository must discover and follow this document before making changes.
>
> Canonical path: `/AI_BLUEPRINT.md`
>
> Do not create, maintain, or treat another roadmap/blueprint/master-plan/TODO as authoritative. Historical planning documents may remain for recordkeeping, but they are not instructions unless explicitly incorporated into this document.

## 1. Mission

Windows-AI is a Windows-first, locally runnable and cloud-capable AI platform intended to become an extensible AI control layer for Windows. It combines conversational AI, multiple model providers, local models, agents, RAG/search, automation, plugins, Windows integration, security, IoT, XR, and a polished desktop experience.

The goal is a real, usable product—not a collection of demos or documentation. Prefer working production implementation over speculative architecture.

## 2. Development Rules

1. **Read this file first.** Before coding, determine which section of this blueprint the task advances.
2. **User instructions win.** Direct instructions in the current task override this document where they conflict.
3. **Implement; do not merely plan.** When asked to develop, modify the repository with production-quality code/configuration instead of only creating issues or plans.
4. **Preserve existing functionality and public APIs** unless the task explicitly requires a breaking change.
5. **Reuse existing architecture.** Inspect the repository and extend existing systems instead of creating duplicate managers, services, registries, or packaging systems.
6. **Security by default.** Never hard-code credentials, tokens, API keys, private data, or signing secrets. Keep privileged Windows operations controlled and auditable.
7. **Windows first.** The primary target is supported Windows 10/11 environments. Cross-platform code is welcome when it improves maintainability without compromising Windows functionality.
8. **Tests are not the current priority.** Unless the user explicitly asks for tests, do not make test creation the focus of a development task. Run only checks that are intrinsically necessary to build or validate a change when appropriate.
9. **Documentation should describe reality.** Update concise product/developer documentation when implementation changes make it necessary, but do not create parallel planning documents.
10. **Keep the repository coherent.** Avoid dead code, duplicate implementations, placeholder features presented as complete, and unnecessary dependencies.

## 3. Product Architecture

### Core
- Python/FastAPI backend and service layer.
- Central orchestration for AI requests, agents, plugins, configuration, credentials, tasks, and automation.
- Unified abstractions so the application can switch AI providers without rewriting higher-level features.

### AI Providers
Support cloud and local providers through a common interface, including existing integrations such as OpenAI, Anthropic, Google, Mistral, Cohere, Groq, Ollama, and other providers already supported by the repository.

### Desktop
- Electron-based Windows desktop application.
- Chat and AI interaction.
- Model/provider selection.
- Agent management.
- Workflow/automation controls.
- Plugin/marketplace experience.
- System tray, notifications, settings, and Windows-native integration where appropriate.

### Agents
- Agent manager and task execution.
- Multi-agent orchestration where useful.
- Controlled tool/plugin access.
- Clear permission boundaries for privileged operations.

### Plugins
Plugins are the primary extensibility mechanism. Continue expanding the existing plugin architecture and categories rather than bypassing it with one-off integrations. Plugin discovery, lifecycle management, configuration, permissions, and marketplace capabilities should remain compatible with the core architecture.

### Search and RAG
- Local file/document indexing.
- Universal/local/remote search.
- Embeddings and vector storage.
- Retrieval and re-ranking.
- RAG integration with agents and conversations.

### Automation
Support event/time/file/application/system/webhook/device triggers, workflows, scheduling, watchers, and AI-driven actions through the existing automation architecture.

### Windows Integration
Windows-AI should be able to safely work with Windows applications, files, processes, shell/system capabilities, clipboard, notifications, settings, and other OS functionality through controlled interfaces/plugins rather than unrestricted access wherever practical.

### IoT
Continue the existing device architecture for MQTT, Matter, Zigbee, Home Assistant, Tuya, Ring, Nest, Hue, BLE, and other supported adapters as the codebase matures.

### XR and Mobile
XR integrations should use appropriate abstractions such as OpenXR/WebXR/SteamVR. The mobile companion should evolve as a companion/control surface for Windows-AI rather than becoming a separate competing product.

### Security
Maintain encrypted credential handling, environment-variable support, RBAC/permissions, sandboxing where applicable, auditability, secure defaults, and safe handling of privileged actions.

## 4. Zero-Configuration Goal

The product should move toward an install-and-use experience:

`Install → Detect system → Detect capabilities/providers → Configure sensible defaults → Start Windows-AI`

Advanced users must still be able to override automatic configuration.

## 5. Distribution and Release

The Windows distribution stack is a major current development priority:

- PyInstaller packaging for the Python/backend components.
- Electron packaging/build integration.
- NSIS installer and upgrade/uninstall/repair behavior.
- Portable ZIP distribution.
- MSIX packaging where practical.
- Automatic updater/release integration.
- GitHub Actions/tag-based release automation.
- Reproducible, clearly versioned release artifacts.

Target release flow:

`Git tag → CI build → backend/package build → Electron package → installer/portable/MSIX artifacts → GitHub Release`

Reuse existing scripts and configuration. Do not create parallel packaging systems.

## 6. Current Development Priority

When no more specific user task is given, prioritize unfinished production work in this order:

1. Finish and harden core Windows-AI functionality.
2. Finish the Electron desktop experience and important missing integrations.
3. Strengthen AI providers, agents, plugins, search/RAG, and automation.
4. Deepen safe Windows integration.
5. Finish production Windows distribution: PyInstaller, Electron packaging, NSIS, portable ZIP, MSIX, updater, and release automation.
6. Mature IoT, mobile, XR, marketplace, and other expansion areas.
7. Improve performance, reliability, UX, documentation, and maintainability as implementation demands.

## 7. Definition of Done for Development

A feature is considered implemented when the actual repository contains the required production code/configuration, it integrates with the existing architecture, it is wired into the appropriate entry points/builds, and documentation is updated only where needed. Do not mark a feature complete merely because a plan, stub, or issue exists.

## 8. Planning Policy

This file replaces the role of separate active blueprints, roadmaps, master plans, and TODO plans. New strategic direction must be incorporated here rather than creating another competing plan.

Historical documents under `docs/planning/`, `docs/master_plan/`, and similar directories are reference/history only. They must not override this document.

If an old document conflicts with this blueprint, follow this file and, when useful, update the old document to point here rather than reviving its conflicting instructions.

## 9. AI Agent Startup Protocol

At the start of every repository task:

1. Find `/AI_BLUEPRINT.md`.
2. Read it completely enough to understand the relevant architecture and current priority.
3. Inspect the repository for the existing implementation.
4. Identify the smallest coherent production change that advances the requested goal.
5. Implement the change directly.
6. Avoid creating another roadmap/blueprint/master-plan/TODO unless the user explicitly asks for historical documentation.
7. Report what was actually changed; never claim work that was only planned.

## 10. Canonical Reference

**Canonical blueprint:** `/AI_BLUEPRINT.md`

Any AI instruction file in this repository should point to this file. If an AI system supports repository instruction files, those files should tell the agent to read this document before working.
