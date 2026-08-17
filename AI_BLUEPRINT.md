# Windows-AI — Canonical Product & Development Blueprint

> **This is the single source of truth for active Windows-AI development.**
>
> Every AI coding agent must read `AGENTS.md`, then this file, before modifying the repository.

## 1. Authority

This document replaces competing active roadmaps, blueprints, master plans, and AI development plans. Historical documents may remain for reference, but they do not override this blueprint.

If any older document conflicts with this file, **this file wins**.

The project owner has explicitly directed: **develop first; test at the end.**

---

# 2. Product Vision

Windows-AI is being built as a **Windows-first, locally runnable AI control layer** that combines AI models, agents, tools, plugins, memory, search, automation, computer use, Windows control, external services, devices, and a polished desktop experience into one extensible platform.

The finished product should feel less like a chatbot and more like an **AI operating layer for Windows**.

A user should be able to install Windows-AI, have it detect and configure the computer, select local or cloud intelligence, interact naturally, and safely delegate real work to agents and tools.

Core goals:

- Local-first and privacy-aware operation
- Cloud AI when useful
- Offline capability where practical
- Natural-language computer control
- Multi-agent work delegation
- Extensible tools, plugins, and MCP
- Persistent search, RAG, and memory
- Windows automation
- Developer/coding workflows
- IoT/device integration
- Reliable packaging, updating, and distribution
- Secure, permission-controlled execution

---

# 3. Finished Product Capabilities

Windows-AI should ultimately provide:

- Natural-language chat and commands
- Text, image, audio, voice, document, and video understanding where supported
- Local and cloud model selection
- Model routing and fallback
- Short-term and long-term memory
- Project/workspace memory
- RAG and semantic search
- File and document understanding
- Windows application launching and control
- File/folder operations
- Process and service operations
- System settings and supported OS actions
- Clipboard operations
- Screenshots and screen understanding
- Keyboard/mouse/computer-use automation where supported
- Voice input and text-to-speech
- Notifications
- Web interaction through approved tools
- Code generation and repository assistance
- Git/GitHub workflows
- Long-running/background agents
- Scheduled automation
- Event-driven workflows
- Plugin and marketplace ecosystem
- MCP client/server integration
- IoT/device control
- Mobile companion capabilities
- XR/AR/VR expansion
- Secure permissions and approvals
- Self-contained Windows distribution and updates

Capabilities must be implemented through controlled architecture rather than unrestricted arbitrary access.

---

# 4. System Architecture

The target architecture is:

```text
                         WINDOWS-AI
                              │
                 ┌────────────┴────────────┐
                 │                         │
              Desktop                  Backend
              Electron                 FastAPI
                 │                         │
                 └────────────┬────────────┘
                              │
                       AI Orchestrator
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
       Model Router       Agent Manager       Memory
          │                   │                   │
    ┌─────┼─────┐       ┌─────┼─────┐       ┌────┼────┐
    │     │     │       │     │     │       │    │    │
  Local Cloud Hybrid  Agents Tasks Teams  Short Long RAG
          │                   │                   │
          └───────────────────┼───────────────────┘
                              │
                        Unified Tool Layer
                              │
             ┌────────────────┼────────────────┐
             │                │                │
          Built-ins         Plugins            MCP
             │                │                │
             └────────────────┼────────────────┘
                              │
                       Permission Layer
                              │
              ┌───────────────┼────────────────┐
              │               │                │
           Windows          Web             Devices
              │               │                │
              └───────────────┼────────────────┘
                              │
                         Event / Result
                              │
                              ▼
                              AI
```

The major architectural principle is that **AI intelligence, agents, plugins, MCP, and Windows/device capabilities converge through a unified tool/action layer**.

---

# 5. Unified Tool & Action Architecture

This is a central subsystem and must be treated as such.

Every executable capability should be representable as a tool/action with:

- Name and description
- Input schema
- Output schema
- Capability category
- Permission requirements
- Risk level
- Availability conditions
- Provider/plugin/MCP ownership
- Timeout/resource policy
- Audit metadata

Execution flow:

```text
AI Request
   ↓
Orchestrator
   ↓
Tool Router
   ↓
Capability Discovery
   ↓
Permission / Policy Check
   ↓
Approval if required
   ↓
Tool Execution
   ↓
Result / Error
   ↓
Audit Event
   ↓
AI / Agent
```

The tool layer must support built-in tools, plugins, MCP tools, Windows tools, web tools, developer tools, automation tools, and device tools without requiring separate execution architectures.

---

# 6. AI Provider & Model Layer

Use a provider-agnostic interface.

Support existing and future cloud providers and local runtimes, including where practical:

- OpenAI
- Anthropic
- Google
- Mistral
- Cohere
- Groq
- Ollama
- Other compatible local model runtimes

The model layer should provide:

- Model discovery
- Provider discovery
- Model capability metadata
- Context limits
- Vision/audio/tool capability metadata
- Model routing
- Fallback
- Privacy preference
- Offline preference
- Cost/performance preference
- Local-first preference
- Provider health/status
- Streaming

Model routing should support:

```text
Request
  ↓
Policy / Preferences
  ↓
Model Router
  ├── Local
  ├── Cloud
  └── Hybrid
```

---

# 7. Memory Architecture

Memory is a first-class subsystem.

Support distinct layers where appropriate:

- Conversation/short-term memory
- Long-term user memory
- Agent memory
- Project/workspace memory
- Semantic/vector memory
- Structured memory
- Retrieved knowledge
- Ephemeral task state

Memory must support:

- Storage
- Retrieval
- Ranking
- Summarization
- Deduplication
- User inspection
- Editing/deletion
- Privacy controls
- Workspace isolation
- Agent isolation where required

The user must retain control over persistent memory.

---

# 8. Agent Architecture

Agents are specialized AI workers operating through the unified tool layer.

Target hierarchy:

```text
Master Orchestrator
        ↓
Agent Manager
        ↓
Specialized Agents
        ↓
Tools / Plugins / MCP
        ↓
Windows / Web / APIs / Devices
```

Agent capabilities should include:

- Agent profiles
- System instructions
- Tool permissions
- Model selection
- Memory assignment
- Workspace assignment
- Task state
- Background execution
- Scheduling
- Parallel execution
- Agent-to-agent communication
- Delegation
- Human approval gates
- Cancellation
- Recovery
- Result aggregation

Agents must not bypass the permission architecture.

---

# 9. MCP Architecture

MCP is a first-class extensibility layer.

Windows-AI should support an MCP client architecture and, where useful, MCP server capabilities.

Target support includes:

- MCP server discovery/configuration
- Local MCP servers
- Remote MCP servers
- Tool registration
- Resource registration
- Prompt registration
- Authentication
- Permission mapping
- Server lifecycle
- Health/status
- Version compatibility
- Secure credential handling

MCP capabilities must enter the same unified tool/action and permission architecture as native tools and plugins.

---

# 10. Plugin Platform

Plugins are a primary extension mechanism.

The plugin architecture should define:

- Manifest
- Metadata
- Versioning
- Dependencies
- Capabilities
- Permissions
- Configuration
- Lifecycle hooks
- Tool registration
- Event registration
- UI integration
- Storage boundaries
- Compatibility rules
- Updates
- Disable/uninstall behavior
- Trust/signing model where practical

Plugins must use stable APIs and should not duplicate core services.

---

# 11. Marketplace

The marketplace should eventually distribute:

- Plugins
- Agents
- Tools
- MCP servers/configurations
- Models or model configurations
- Workflows
- Extensions
- Themes

Marketplace requirements include:

- Discovery
- Categories
- Search
- Versioning
- Compatibility metadata
- Installation/update/uninstall
- Trust/signing information
- Permissions disclosure
- Ratings/reviews where appropriate
- Local/offline package installation where practical

---

# 12. Windows Integration

Windows-AI should provide controlled capabilities for:

- Applications
- Files/folders
- Processes
- Services
- Clipboard
- Notifications
- Windows settings
- Power/session operations
- Networking where authorized
- Shell/terminal
- System information
- Hardware information
- Supported Windows APIs

Capabilities must be exposed through the tool/action layer and governed by permissions.

---

# 13. Computer-Use System

Computer use is distinct from ordinary Windows APIs and should be treated as its own subsystem.

Target flow:

```text
Observe screen
     ↓
Understand UI
     ↓
Plan action
     ↓
Permission / approval
     ↓
Click / type / scroll / interact
     ↓
Observe result
     ↓
Continue or finish
```

Support, where technically practical:

- Screenshots
- Vision models
- UI element detection
- Mouse control
- Keyboard control
- Window management
- Application awareness
- Action verification
- Safe stopping
- Human takeover

High-risk actions should require explicit approval according to policy.

---

# 14. Multimodal System

The AI layer should support a unified multimodal interface for:

- Text
- Images
- Screenshots
- Audio
- Speech
- Video
- Documents
- OCR
- Vision
- Speech-to-text
- Text-to-speech

Provider capabilities should determine which modalities are available for each model.

---

# 15. Search, RAG & Knowledge

Build toward unified:

- Local search
- Remote/web search
- File indexing
- Document processing
- OCR
- Chunking
- Embeddings
- Vector databases
- Hybrid retrieval
- Re-ranking
- RAG
- Knowledge collections
- Workspace knowledge

The system should make relevant information available to agents through the same controlled tool architecture.

---

# 16. Workspace / Project System

A workspace represents an isolated context for a user/project.

```text
Workspace
├── Files
├── Instructions
├── Memory
├── Agents
├── Tools
├── MCP servers
├── Plugins
├── Models
└── Workflows
```

Workspaces should support:

- Creation/deletion
- Isolation
- Project instructions
- Context discovery
- Memory boundaries
- Tool permissions
- Agent assignment
- Git repository association
- Workspace-specific configuration

---

# 17. Developer & Coding Platform

Windows-AI should be a serious AI development environment.

Target capabilities:

- Git integration
- GitHub integration
- Repository discovery
- Repository indexing
- Code search
- Code understanding
- Code generation
- Code editing
- Terminal integration
- Branch management
- Commit creation
- Pull requests
- Issues
- CI/CD interaction
- IDE integration
- Coding agents
- MCP development tools

The system must preserve repository safety and permission boundaries.

---

# 18. Automation & Workflows

Support:

- Scheduled triggers
- File triggers
- Application events
- System events
- Webhooks
- Device events
- AI conditions
- Manual triggers

Workflow architecture:

```text
Trigger
  ↓
Condition / Policy
  ↓
Workflow
  ↓
Agent / Tools
  ↓
Actions
  ↓
Results / Events
```

Workflows should be persistent, inspectable, editable, cancellable, and permission-aware.

---

# 19. Security & Permissions

Security is mandatory throughout development even though broad testing is deferred.

Define permissions for capabilities such as:

```text
READ
WRITE
EXECUTE
NETWORK
SYSTEM
ADMIN
CREDENTIALS
DEVICE
AUTOMATION
```

Permissions apply to:

- Users
- Agents
- Plugins
- Tools
- MCP servers
- Workflows
- Applications

Security architecture should include:

- Credential protection
- Encryption
- RBAC/policies
- Sandboxing where practical
- Audit logs
- Approval gates
- Safe defaults
- Secret isolation
- Credential rotation support
- Network controls
- Plugin/MCP trust information

No feature should require committing credentials or secrets to source control.

---

# 20. Configuration & Zero-Config

Windows-AI should automatically detect and configure as much as safely possible.

Target flow:

```text
Install
 ↓
Detect OS
 ↓
Detect CPU/GPU/RAM
 ↓
Detect models/runtimes
 ↓
Detect providers
 ↓
Load safe configuration
 ↓
Start services
 ↓
Ready
```

Configuration layers should support:

- System/global
- User
- Workspace/project
- Agent
- Plugin
- Provider/model
- Environment variables
- Secrets

Define and document configuration precedence so behavior is predictable.

---

# 21. Offline-First Capability

Windows-AI should remain useful without Internet access where technically practical.

Offline functionality should include:

- Local models
- Local embeddings
- Local RAG
- Local memory
- Local search
- Windows control
- Local tools/plugins
- Local automation

Cloud-dependent features should degrade gracefully rather than breaking the entire application.

---

# 22. Desktop Experience

Electron is the primary desktop interface.

Target areas:

- Chat
- Model selection
- Agents
- Workspaces
- Memory
- Search/RAG
- Tools
- Plugins
- Marketplace
- MCP
- Workflows
- Settings
- Notifications
- System tray
- Logs/activity
- Permission prompts
- Accessibility
- Windows-specific features

Customization should support themes, layouts, shortcuts, voice settings, notifications, and agent/persona configuration where appropriate.

---

# 23. Observability

Build an internal observability layer for:

- Application logs
- Events
- Agent activity
- Tool execution
- Plugin activity
- MCP activity
- API activity
- Errors
- Performance/resource usage
- Workflow execution

Users should be able to inspect meaningful activity while privacy-sensitive data remains protected.

---

# 24. IoT & Device Architecture

IoT should use a common device gateway rather than unrelated implementations.

```text
Device Gateway
 ↓
Device Registry
 ↓
Capability Model
 ↓
Permission Layer
 ↓
Tool Layer
 ↓
AI / Automation
```

Support where practical:

- MQTT
- Matter
- Zigbee
- Home Assistant
- Bluetooth/BLE
- Other supported device APIs

Devices should expose capabilities to agents through the same tool/action architecture.

---

# 25. Mobile Companion

The mobile companion should eventually provide:

- Remote AI access
- Remote Windows-AI control
- Notifications
- Voice commands
- Device pairing
- Authentication
- Camera/vision input
- Clipboard/context synchronization where appropriate

Mobile remains an expansion area after core Windows functionality is mature.

---

# 26. XR / AR / VR

Spatial computing is an expansion area.

Target technologies include:

- OpenXR
- WebXR
- SteamVR

XR features should reuse the same agent, tool, permission, and AI architectures instead of becoming a separate platform.

---

# 27. Distribution & Installation

Windows-AI must become a polished Windows application with reliable distribution.

Target artifacts:

- PyInstaller backend/application components
- Electron production package
- NSIS installer
- Portable ZIP
- MSIX where practical
- Uninstaller
- Upgrade/repair behavior
- Runtime asset handling
- Versioning
- GitHub Releases

Target release flow:

```text
Version Tag
 ↓
Build
 ↓
Package
 ↓
Installer
 ↓
Portable ZIP
 ↓
MSIX
 ↓
Release Metadata
 ↓
GitHub Release
```

---

# 28. Update & Recovery System

The updater should eventually support:

- Version discovery
- Stable/beta/nightly channels where appropriate
- Download verification
- Installation
- Configuration preservation
- Database/migration handling
- Rollback
- Repair
- Safe restart
- Failed-update recovery

Updates must not silently destroy user data or configuration.

---

# 29. Development Phases

## Phase A — Core Platform

Complete and integrate core orchestration, backend/API, providers, agents, tools, plugins, search/RAG/memory, configuration, and security.

## Phase B — Desktop Product

Complete the Electron experience, workspaces, agents, tools, plugins, marketplace, MCP, settings, notifications, accessibility, and Windows-specific UI.

## Phase C — Windows Intelligence

Expand controlled Windows operation, computer use, automation, workflows, background agents, and system integration.

## Phase D — Distribution

Complete PyInstaller, Electron packaging, NSIS, portable ZIP, MSIX, updater, versioning, and automated GitHub releases.

## Phase E — Expansion

Expand IoT, mobile, XR, provider ecosystem, plugin ecosystem, marketplace, and advanced multimodal capabilities.

## Phase F — Final Validation

Only after the implementation roadmap is substantially complete, perform comprehensive validation and testing.

---

# 30. TESTING POLICY — FINAL PHASE ONLY

**Testing is intentionally deferred until the end of development.**

During Phases A–E:

- Do not create new test suites as normal feature work.
- Do not expand test coverage.
- Do not run broad test campaigns.
- Do not spend development time fixing unrelated old test failures.
- Do not use test metrics as active feature-completion requirements.
- Do not allow historical testing plans to override this blueprint.

A build or targeted validation command may be used only when intrinsically necessary to implement or package production functionality.

### Final Validation

After implementation is substantially complete, perform as appropriate:

- Unit testing
- Integration testing
- End-to-end testing
- GUI testing
- API testing
- Plugin testing
- Agent/workflow testing
- MCP testing
- Security validation
- Packaging/install/update validation
- Windows 10/11 compatibility validation
- Performance/reliability validation
- Release-candidate validation

**Develop first. Validate at the end.**

Deferring testing does not permit intentionally insecure code, secrets in source control, or deliberate unnecessary breakage.

---

# 31. AI Agent Development Workflow

Every AI coding agent must:

1. Read `AGENTS.md`.
2. Read this `AI_BLUEPRINT.md`.
3. Inspect the existing implementation relevant to the task.
4. Identify the correct subsystem and reuse existing architecture.
5. Implement production functionality directly.
6. Avoid duplicate systems.
7. Respect security and permission boundaries.
8. Avoid creating competing planning documents.
9. Do not prioritize testing during Phases A–E.
10. Update this blueprint only when major architecture, product direction, or phase status changes.
11. Clearly report what was actually changed.

If an AI agent encounters an older roadmap or blueprint that conflicts with this document, it must follow this document.

---

# 32. Completion Definition

Windows-AI is complete when it operates as a cohesive product rather than a collection of disconnected components:

```text
Install
 ↓
Detect / Configure
 ↓
Start
 ↓
Desktop AI
 ↓
Models + Memory
 ↓
Agents + Tools
 ↓
Plugins + MCP
 ↓
Search + RAG
 ↓
Windows Control + Computer Use
 ↓
Automation + Workflows
 ↓
Developer Platform
 ↓
IoT / Integrations
 ↓
Packaging + Updates
 ↓
Final Validation
 ↓
Production Release
```

Completion means the architecture works together, capabilities are discoverable, permissions are enforced, data/configuration are protected, and the product can be installed and used as a cohesive Windows AI platform.

---

# 33. Historical Documentation Rule

Older documents under `docs/`, previous roadmaps, TODO files, completion reports, testing reports, CI/CD reports, session notes, and archived agent plans are **historical/reference material** unless their content is deliberately incorporated into this blueprint.

They do not create additional active requirements.

Do not resurrect old plans simply because they exist in the repository.

---

# 34. Owner Direction

The current owner direction is:

> **One blueprint. One development direction. Build the product first. Testing comes at the end.**

This directive governs AI-assisted development until the owner explicitly changes it.
