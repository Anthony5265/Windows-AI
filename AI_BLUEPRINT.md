# Windows-AI — Canonical AI Development Blueprint

## 1. Authority

This document is the **single canonical source of truth for active Windows-AI development**.

Every AI coding agent working in this repository MUST read `AGENTS.md` and then this file before making development decisions.

Do not create or follow competing active blueprints, roadmaps, master plans, or AI development plans. Historical planning documents may remain for reference, but they do not override this document.

If an older document conflicts with this blueprint, this blueprint wins.

## 2. Development Mission

Build Windows-AI into a production-quality, Windows-first AI platform that combines:

- Multiple cloud and local AI providers
- Local model support
- Multi-agent orchestration
- RAG, search, memory, and knowledge systems
- Windows and Windows-OS control
- Plugin architecture and marketplace
- Automation and workflows
- IoT/device integrations
- Desktop GUI
- Mobile and XR expansion
- Strong security and permission boundaries
- Reliable Windows packaging, installation, updating, and distribution

The goal is not merely to maintain a chatbot. Windows-AI should become an extensible AI control layer for Windows.

## 3. Core Development Rules

1. **Build first.** Prioritize production implementation over planning, reports, and administrative work.
2. **Use the existing architecture.** Inspect the repository before adding anything. Reuse existing components and APIs instead of creating duplicates.
3. **Preserve working functionality.** Changes must fit the existing architecture and avoid unnecessary breaking changes.
4. **One plan.** New active development direction belongs in this file.
5. **No competing instructions.** AI-specific instruction files should point agents here rather than define another project plan.
6. **No unnecessary tests during active development.** Testing is intentionally deferred until the final development phase described below.
7. **Do not spend development time writing test suites, expanding test coverage, running test campaigns, or building test infrastructure during the implementation phases unless a test/build step is absolutely required to make the production implementation work.
8. **Security remains mandatory.** Deferring testing does not authorize adding credentials, secrets, unsafe defaults, or deliberately insecure architecture.
9. **Keep documentation proportional.** Update this blueprint when the product direction or major implementation status changes; do not create duplicate planning documents.
10. **Finish implementation before validation.** The final testing/validation phase happens after the planned product functionality is implemented.

## 4. Product Architecture

### Core

- Unified application orchestration
- Configuration management
- Credential management
- Plugin manager and registry
- Agent manager
- Task/workflow system
- Event system

### AI Layer

Support a provider-agnostic interface for cloud and local AI, including the existing provider integrations and local runtimes such as Ollama where supported.

### Backend

FastAPI-based services provide the stable backend interface for the desktop application, agents, plugins, search, automation, and integrations.

### Desktop

Electron is the primary desktop interface. It should expose chat, models, agents, workflows, plugins, marketplace functionality, settings, notifications, and Windows-AI controls.

### Plugins

The plugin system is the primary extensibility mechanism. Plugins should integrate capabilities without unnecessarily modifying core services.

### Search / RAG / Memory

Build toward unified local/remote search, document processing, embeddings, vector storage, retrieval, RAG, and persistent AI knowledge.

### Agents

Support task-oriented agents and multi-agent orchestration with controlled capabilities and clear permission boundaries.

### Windows Integration

Provide controlled access to Windows applications, files, processes, system functions, clipboard, notifications, automation, and other supported OS capabilities.

### Automation

Support triggers, workflows, scheduled actions, watchers, webhooks, device events, and AI-driven conditions.

### IoT

Continue the planned MQTT, Matter, Zigbee, Home Assistant, Bluetooth/BLE, and other device integrations where practical.

### XR / Mobile

Continue these as expansion areas after the core Windows product is mature.

### Security

Maintain credential protection, permissions/RBAC, sandboxing, auditing, encryption, safe configuration, and controlled system capabilities throughout development.

## 5. Development Priorities

### Phase A — Core Product Completion

Finish and integrate remaining core functionality across:

- Core orchestration
- Backend/API
- AI providers
- Agents
- Plugins
- Search/RAG/memory
- Configuration
- Security

### Phase B — Desktop Experience

Continue production implementation of:

- Electron GUI
- AI chat experience
- Agent interface
- Workflow interface
- Plugin management
- Marketplace
- System tray and notifications
- Settings and configuration
- Accessibility and Windows-specific integrations

### Phase C — Windows Intelligence and Automation

Expand the AI's controlled ability to:

- Understand the Windows environment
- Operate supported applications
- Manage files and system resources
- Execute approved actions
- Automate workflows
- Respond to events
- Coordinate agents and plugins

### Phase D — Distribution

Make Windows-AI a polished distributable Windows application:

- PyInstaller backend packaging
- Electron production packaging
- NSIS installer
- Uninstaller and upgrade handling
- Portable ZIP distribution
- MSIX packaging where practical
- Runtime asset handling
- Versioning
- GitHub release automation
- Update mechanism

### Phase E — Expansion

After the core Windows product is implemented, continue:

- IoT ecosystem
- Mobile companion
- XR/AR/VR
- Expanded provider ecosystem
- Expanded plugin ecosystem
- Marketplace ecosystem

## 6. TESTING POLICY — DEFERRED UNTIL THE END

**Testing is intentionally removed from the active development workflow.**

During Phases A–E:

- Do not create new test suites as a development priority.
- Do not expand test coverage.
- Do not spend sessions fixing unrelated test failures.
- Do not run broad test campaigns.
- Do not make test metrics a completion criterion for implementation work.
- Do not let old testing plans dictate development priorities.

Existing tests may remain in the repository as historical/deferred material. They are not the active development focus.

### Final Validation Phase — Only After Development Is Complete

Once the implementation roadmap is substantially complete, testing becomes a dedicated final phase.

That final phase will cover, as appropriate:

- Unit tests
- Integration tests
- End-to-end tests
- GUI tests
- API tests
- Plugin tests
- Agent/workflow tests
- Security validation
- Packaging/install/update validation
- Windows 10/11 compatibility
- Performance and reliability validation
- Release-candidate validation

At that point, failures found through testing should be fixed before declaring Windows-AI production-ready.

**Important:** Deferring testing is a sequencing decision, not permission to knowingly introduce insecure behavior or intentionally break existing functionality.

## 7. AI AGENT WORKFLOW

Every AI working on this repository should follow this sequence:

1. Read `AGENTS.md`.
2. Read `AI_BLUEPRINT.md`.
3. Inspect the current repository implementation relevant to the requested task.
4. Determine whether the requested work advances an active phase.
5. Implement the production code/configuration directly.
6. Reuse existing components and avoid duplication.
7. Do not start a separate planning document unless explicitly requested by the owner.
8. Do not prioritize testing during the active implementation phases.
9. Update this blueprint only when a major product direction, architectural decision, or phase status genuinely changes.
10. Clearly report what was actually implemented.

## 8. Completion Definition

Windows-AI is not considered finished merely because the individual components exist. The product must eventually operate as a cohesive Windows application:

```text
Install
  ↓
Configure / Detect Environment
  ↓
Start Windows-AI
  ↓
Desktop AI Interface
  ↓
Models + Agents + Plugins
  ↓
Search + RAG + Memory
  ↓
Windows Control + Automation
  ↓
Integrations
  ↓
Packaging + Updates + Releases
  ↓
Final Validation
  ↓
Production Release
```

The final validation/testing phase occurs **after implementation is complete**, not throughout the active build phase.

## 9. Historical Documentation

Older documents under `docs/`, including previous roadmaps, blueprints, TODO lists, completion reports, security test reports, CI/CD reports, and session reports, are historical/reference material unless explicitly promoted into this blueprint.

They must not be treated as competing active instructions.

When historical documentation conflicts with this blueprint, follow this file.

## 10. Owner Direction

The repository owner has explicitly directed that Windows-AI should be actively **developed first and tested at the end**. AI agents must respect that sequencing unless the owner changes it.
