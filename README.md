# 🪟 Windows-AI

### Your AI control layer for Windows.

**Windows-AI** is an open-source, Windows-first AI platform designed to bring cloud models, local models, agents, automation, plugins, search/RAG, and Windows control together in one extensible application.

> **Build first. Validate at the end.**  
> Active development is focused on building the product. Comprehensive testing is reserved for the final development phase.

<p align="center">
  <a href="https://github.com/Anthony5265/Windows-AI/releases">⬇️ Releases</a> •
  <a href="https://github.com/Anthony5265/Windows-AI/blob/main/AI_BLUEPRINT.md">🧠 AI Blueprint</a> •
  <a href="https://github.com/Anthony5265/Windows-AI/issues">🐛 Issues</a> •
  <a href="https://github.com/Anthony5265/Windows-AI/discussions">💬 Discussions</a>
</p>

---

## 🚀 The Vision

Windows-AI is being built as more than a chatbot.

The long-term goal is an **AI operating layer for Windows** that can understand your environment, work with AI models, coordinate agents, use plugins, search your knowledge, automate workflows, and safely interact with Windows and connected services.

```text
                         ┌─────────────────────┐
                         │     Windows-AI      │
                         │   AI Control Layer  │
                         └──────────┬──────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          ▼                         ▼                         ▼
   🧠 AI & Models             🤖 Agents                 🪟 Windows
   Local + Cloud              Multi-Agent               OS Control
          │                         │                         │
          └─────────────────────────┼─────────────────────────┘
                                    ▼
                         ⚙️ Automation & Workflows
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
                  🔌 Plugins     🔎 RAG/Search    🏠 IoT
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
                         🖥️ Desktop Experience
```

---

## ✨ What Windows-AI Brings Together

| Area | Capabilities |
|---|---|
| 🧠 **AI** | Cloud providers, local models, multimodal AI, model discovery |
| 🤖 **Agents** | Task agents, orchestration, multi-agent workflows |
| 🔌 **Plugins** | Extensible plugin architecture and a large existing plugin ecosystem |
| 🔎 **Knowledge** | Search, document processing, embeddings, vector storage, RAG and memory |
| 🪟 **Windows** | Applications, files, processes, clipboard, notifications and controlled OS actions |
| ⚙️ **Automation** | Workflows, schedules, watchers, events, webhooks and AI-driven actions |
| 🖥️ **Desktop** | Electron interface, chat, agents, workflows, plugins, settings and system integration |
| 🏠 **IoT** | MQTT, Matter, Zigbee, Home Assistant and device integrations |
| 🔐 **Security** | Credentials, permissions, RBAC, sandboxing, encryption and auditing |
| 📦 **Distribution** | Windows packaging, installer, portable builds, MSIX and release automation |

---

## 🧠 AI Without Lock-In

Use the model that makes sense for the job.

### ☁️ Cloud

- OpenAI
- Anthropic
- Google
- Mistral
- Cohere
- Groq
- Additional providers through the extensible provider layer

### 🏠 Local

- Ollama
- Local model runtimes supported by the platform
- Privacy-focused local inference

The platform is designed around a **provider-agnostic AI layer**, so applications and plugins don't need to be rewritten every time you change models.

---

## 🤖 Agents + Automation

Turn AI from something you talk to into something that can **perform tasks**.

```text
You
 │
 ▼
AI Request
 │
 ▼
Agent Manager
 │
 ├──► Search / RAG
 ├──► Plugins
 ├──► Windows Actions
 ├──► Other Agents
 └──► Automation
 │
 ▼
Result
```

The architecture is designed for controlled capabilities rather than giving an AI unrestricted access to the computer.

---

## 🔌 Extensible by Design

Plugins are a core part of Windows-AI.

The existing project contains a large plugin ecosystem spanning Windows, operating-system capabilities, AI, audio, vision, code, cloud services, creative tools, automation, IoT, and other integrations.

Developers can extend the platform without unnecessarily modifying the core application.

**Plugin goals:**

- 🧩 Modular capabilities
- 🛠️ Developer SDK
- 🔗 Service integrations
- ⚡ Event-driven extensions
- 🏪 Marketplace architecture
- 🔐 Controlled permissions

---

## 🔎 Search, RAG & Memory

Windows-AI is designed to turn information into usable AI context.

```text
Files / Documents / Search / Knowledge
                    │
                    ▼
              Processing
                    │
                    ▼
              Embeddings
                    │
                    ▼
             Vector Storage
                    │
                    ▼
          Retrieval + Re-ranking
                    │
                    ▼
                  Agent
                    │
                    ▼
                   AI
```

This foundation enables document analysis, knowledge retrieval, local search, RAG, and persistent AI context.

---

## 🪟 Windows-First

Windows-AI is being designed specifically around the Windows desktop rather than treating Windows as an afterthought.

The platform is intended to provide controlled AI access to:

- Applications
- Files and directories
- Processes
- Clipboard
- Notifications
- System resources
- Windows automation
- Supported OS capabilities
- Connected devices and services

Security and permission boundaries remain part of the architecture as these capabilities expand.

---

## 🖥️ Desktop Experience

The Electron desktop application is the primary user interface and is being developed toward a unified AI control center.

Planned/active areas include:

- 💬 AI chat
- 🧠 Model selection
- 🤖 Agents
- ⚙️ Workflows
- 🔌 Plugins
- 🏪 Marketplace
- 🔔 Notifications
- 📌 System tray
- ⚙️ Settings
- 🪟 Windows-specific controls

---

## 📦 Windows Distribution

Windows-AI is being developed toward a polished, installable Windows product.

The distribution architecture includes:

- **PyInstaller** — backend/runtime packaging
- **Electron Builder** — desktop application packaging
- **NSIS** — Windows installer
- **Portable ZIP** — no-install distribution
- **MSIX** — modern Windows package path
- **GitHub Releases** — automated release artifacts
- **Updater** — version/update workflow

---

## 🛠️ Development Status

Windows-AI is **actively under development**.

The project has a broad existing foundation across the backend, plugins, AI integrations, search/RAG, agents, Windows integrations, GUI, security, IoT, and packaging. Current work is focused on completing and integrating the product into a cohesive Windows application.

### Current development order

```text
Core Platform
     ↓
Desktop Experience
     ↓
Windows Intelligence & Automation
     ↓
Distribution & Updates
     ↓
IoT / Mobile / XR Expansion
     ↓
Final Validation
     ↓
Production Release
```

### ⚠️ Testing policy

**Testing is intentionally deferred until the end of development.**

During active implementation, development focuses on production code, architecture, integrations, UI, packaging, and functionality. A comprehensive validation phase will begin after the implementation roadmap is substantially complete.

---

## 📚 Project Documentation

### ⭐ Start Here

- **[AI Development Blueprint](AI_BLUEPRINT.md)** — the single source of truth for active development
- **[AI Agent Instructions](AGENTS.md)** — instructions for AI coding agents working in this repository

### 📖 Guides

- [Installation Guide](docs/getting-started/INSTALLATION.md)
- [Quick Start](docs/QUICK_START.md)
- [User Guide](docs/USER_GUIDE.md)
- [Plugin Development](docs/PLUGIN_DEVELOPMENT.md)
- [API Documentation](docs/api/README.md)
- [API Reference](docs/api/API_REFERENCE.md)
- [Provider Integrations](docs/api/PROVIDER_INTEGRATIONS.md)
- [FAQ](docs/FAQ.md)

> Older roadmaps, planning documents, reports, and TODO files are retained as historical/reference material. **`AI_BLUEPRINT.md` is the authoritative active development plan.**

---

## 💻 Installation

### Windows

Download the latest Windows release from:

**[👉 GitHub Releases](https://github.com/Anthony5265/Windows-AI/releases)**

The project is actively developing its production installer, portable distribution, and Windows packaging pipeline.

### From Source

```powershell
git clone https://github.com/Anthony5265/Windows-AI.git
cd Windows-AI
pip install -e .
```

For detailed setup instructions, see the **[Installation Guide](docs/getting-started/INSTALLATION.md)**.

---

## 👨‍💻 Development

Windows-AI is designed to be developed by both humans and AI coding agents.

Before making changes, an AI agent should:

```text
AGENTS.md
    ↓
AI_BLUEPRINT.md
    ↓
Inspect existing code
    ↓
Implement production functionality
```

### Core principle

> **One blueprint. One direction. Build first. Test at the end.**

Do not create competing active roadmaps or blueprints unless explicitly requested by the project owner.

---

## 🗺️ Roadmap Philosophy

Instead of maintaining multiple competing plans, Windows-AI now maintains **one canonical active blueprint**.

That blueprint is intentionally organized around the product's actual development lifecycle:

1. **Core Product**
2. **Desktop Experience**
3. **Windows Intelligence & Automation**
4. **Distribution**
5. **Expansion**
6. **Final Validation**
7. **Production Release**

This keeps humans and AI agents working toward the same target.

---

## 🤝 Contributing

Contributions are welcome as Windows-AI evolves.

Before contributing, read:

1. [AGENTS.md](AGENTS.md)
2. [AI_BLUEPRINT.md](AI_BLUEPRINT.md)
3. The relevant existing implementation

Please build on the existing architecture rather than creating parallel systems.

---

## 📄 License

Windows-AI is open source under the **MIT License**.

See [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>🪟 Windows-AI</strong><br>
  <em>Build the AI layer for Windows.</em>
</p>
