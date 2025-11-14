# Windows AI

## Imagine a Windows PC That Thinks With You, For You.

Forget complicated software and endless clicks. **Windows AI** is designed to be the ultimate upgrade for your computer, turning it into a **beyond super-agentic, assistant, and chat AI machine.**

> **🎉 NEW: Windows AI is now functional!** Complete chat interface, system tray with quick commands, and easy launcher scripts. [See what's new](#whats-new) | [Quick Start](#-quick-start)

### 🚀 Simple Download, Limitless Power.

When completed, Windows AI will be a single, easy-to-install `.exe` file. Just download, click, and watch your Windows computer transform. No complex setups, no technical jargon – just pure, intelligent assistance at your fingertips.

### 🧠 Your PC, Reimagined. Your Home, Connected.

Windows AI isn't just another program; it's a fundamental shift in how you interact with your computer and your entire home environment. It will deeply and seamlessly integrate with every aspect of your Windows experience, learning your habits, anticipating your needs, and proactively assisting you in ways you never thought possible.

**But that's just the beginning.** From there, your computer will not only be a super-agentic AI machine, but it will also become the **host to transform your local home network into a deeply AI-integrated mesh home.** Imagine a home where every device works in harmony, intelligently managed and optimized by your central AI.

**Get ready for a computer that:**

*   **Understands You**: Chat naturally and get intelligent responses.
*   **Automates Your World**: Handles tasks, organizes your files, and streamlines your workflow effortlessly.
*   **Anticipates Your Needs**: Proactively offers solutions and insights before you even ask.
*   **Learns and Evolves**: Gets smarter and more personalized with every interaction.
*   **Connects Your Home**: Becomes the intelligent hub for your entire home network, creating a seamless, AI-powered living space.

**Windows AI is building the future of personal computing and smart homes, making your digital life simpler, smarter, and truly extraordinary.**

---

## 🎉 What's New

Windows AI now has a **complete, functional system**! Here's what's ready:

### ✅ Completed Features

#### 💬 Modern Chat Interface
- **Beautiful Electron GUI** with light/dark themes
- **Real-time streaming** AI responses
- **Conversation history** with sidebar
- **Multi-model support** (GPT-3.5, GPT-4, Claude, Ollama local models)
- **Quick action buttons** for common tasks
- **Settings panel** for customization

#### 🔔 System Tray Application
- **Quick Command window** (`Ctrl+Shift+Space`)
- **Desktop notifications** for AI responses
- **Status monitoring** (online/offline/busy)
- **Quick actions menu** (time, system info, daily summary)
- **Double-click** to open main chat
- **Right-click menu** with useful options

#### 🚀 Easy Launchers
- **One-click startup** scripts for Linux/Mac and Windows
- **start-all.sh/.bat** - Start everything at once
- **start-backend.sh/.bat** - Just the backend
- **start-gui.sh/.bat** - Just the chat GUI
- **start-tray.sh/.bat** - Just the system tray

#### 🔧 FastAPI Backend
- **Complete REST API** with streaming support
- **Chat endpoints** with conversation management
- **WebSocket support** for real-time communication
- **LiteLLM integration** for 100+ AI models
- **Health monitoring** and status endpoints
- **Configuration system** with persistence

#### 🎨 Professional Design
- **Smooth animations** and transitions
- **Responsive layout** for any screen size
- **Custom scrollbars** and hover effects
- **Message bubbles** with avatars and timestamps
- **Typing indicators** and loading states
- **Character counter** and input validation

#### 🤖 Automation System
- **Folder Watchers** - Monitor directories for file changes and trigger AI actions
- **Scheduled Tasks** - Run AI tasks on a schedule (cron or interval-based)
- **Web UI** - Easy-to-use interface for managing automations
- **Real-time execution** - Automations run in the background
- **Action types** - Organize files, summarize documents, analyze content, run system checks
- **Flexible scheduling** - Cron expressions, intervals (1h, 30m), or one-time tasks

#### 🔧 Watchdog Service (NEW)
- **Auto-Restart** - Automatically restarts backend if it crashes
- **Health Monitoring** - Continuous HTTP health checks
- **Resource Tracking** - Monitors CPU, memory, and thread usage
- **Smart Recovery** - Graceful restart with cooldown protection
- **Production-Ready** - Comprehensive logging and error handling
- **Easy Setup** - Simple startup scripts for all platforms

#### 🔌 Plugin System
- **Extensible Architecture** - Add custom AI actions, tools, and integrations
- **6 Built-in Plugins:**
  - 🔍 **Web Search** - DuckDuckGo integration for current information
  - 📁 **File Organizer** - Intelligent file categorization and organization
  - 💻 **System Info** - Real-time system monitoring and metrics
  - 🐙 **GitHub Integration** - Manage repos, issues, and PRs
  - ⚡ **Code Executor** - Safe sandboxed code execution (Python, JS, Bash)
  - 📅 **Calendar** - Event and reminder management
- **Plugin Types** - Actions, Tools, Integrations, Automation triggers
- **Dynamic Loading** - Plugins load at runtime without restart
- **REST API** - 8 endpoints for plugin management and execution
- **Plugin Marketplace UI** - Browse, enable/disable, and manage plugins
- **Easy Development** - Simple base classes to extend

### 🚀 Quick Start

**Start everything with one command:**

```bash
# Linux/Mac
./start-all.sh

# Windows
start-all.bat
```

That's it! The backend, GUI, and tray will all start automatically.

**Or start components individually:**

```bash
# Start just the backend
./start-backend.sh    # or start-backend.bat

# Start just the GUI
./start-gui.sh        # or start-gui.bat

# Start just the tray
./start-tray.sh       # or start-tray.bat

# Start the watchdog (monitors & auto-restarts backend)
./start-watchdog.sh   # or start-watchdog.bat
```

**Recommended for Production**: Use `start-watchdog.sh` instead of `start-backend.sh` to enable automatic monitoring and restart capabilities. See [docs/WATCHDOG.md](docs/WATCHDOG.md) for details.

**Using the Quick Command (Tray):**
1. Press `Ctrl+Shift+Space` anywhere
2. Type your question
3. Press `Enter`
4. Get a notification with the AI response!

📖 **Full documentation:** See [GETTING_STARTED.md](GETTING_STARTED.md) for detailed setup instructions, configuration, and troubleshooting.

## 🗂 Repository Structure

The entire monorepo is catalogued so you can instantly find any service, UI, or tool:

- Browse the human-friendly [Repository Map](docs/structure/overview.md) to see how every top-level folder and file is grouped.
- Pull the machine-readable [manifest](docs/structure/manifest.json) into scripts or dashboards for automated navigation.
- Regenerate the manifest after reorganizing code with `python scripts/generate_repo_manifest.py --pretty`.
- Explore the comprehensive [Repository Organization Guide](docs/REPO_STRUCTURE.md)
  for a directory-by-directory explanation of responsibilities, tooling, and
  cross-service relationships.

---

## 📸 Screenshots & Demos

### Chat Interface
- Modern, clean design with conversation history
- Real-time streaming responses
- Multi-model support with easy switching
- Light and dark themes

### System Tray
- Quick command window for instant AI access
- Desktop notifications
- Status monitoring
- Quick actions menu

*(Screenshots coming soon!)*

---

## 🛠️ For Developers & Contributors: Dive into the Future!

For those who want to understand the magic under the hood or contribute to this groundbreaking project, here's a more technical overview.

### Project Overview

The **Windows AI** project is developing a comprehensive and intelligent AI assistant deeply integrated with the Windows operating system. It aims to enhance user productivity, automate tasks, and provide intelligent insights through a multi-component architecture. The project is currently in active development, following a structured phased approach to build out its core functionalities, user interfaces, and integration capabilities. Beyond individual machine enhancement, the project envisions transforming local home networks into deeply AI-integrated mesh environments.

### Features

The project is being developed in phases, with the following key features planned:

*   **Epic Chat GUI (Main Control Center)**: A beautiful, feature-rich chat interface, similar to leading AI assistants (ChatGPT, Minus, Deepseek), serving as the primary control center for all Windows AI interactions. This will be the central hub for users to communicate with and manage their AI.
*   **Core Agent (Phase 1)**: A Node.js service acting as the central intelligence, with a plugin architecture supporting interactions with the shell, file system, OpenAI, and GitHub. Includes a Command Line Interface (CLI) and a PowerShell installer for Windows service integration.
*   **Tray GUI (Complementary)**: A lightweight Electron-based application accessible from the system tray, offering quick access to status updates and potentially a simplified command box for rapid interactions, complementing the main chat GUI.
*   **Integrations (Phase 3)**: Advanced integrations including a GitHub trigger UI, folder watcher automation, and scheduled jobs for proactive assistance.
*   **Robust Packaging (Phase 4)**: Comprehensive Windows installer build and a streamlined release pipeline for easy deployment.
*   **Mesh Network Integration (Future)**: Transforming the local home network into an AI-integrated mesh, with the Windows AI PC acting as the central host.

### Technologies Used

This project leverages a hybrid technology stack to deliver its functionalities:

#### Backend (Python)

*   **Framework**: FastAPI
*   **Web/HTTP**: Uvicorn, httpx, requests, respx
*   **AI/ML**: huggingface_hub, litellm, Pillow (for image processing)
*   **System Utilities**: psutil, PyYAML, markdown

#### Frontend/Services (Node.js/JavaScript)

*   **Framework**: Express
*   **HTTP Client**: node-fetch
*   **Monorepo Management**: npm workspaces
*   **Desktop GUI**: Electron (for the main chat GUI and complementary tray app)

#### Other

*   **Dependency Management**: `uv` (for Python), `npm` (for Node.js)
*   **Containerization**: Docker
*   **Testing**: Pytest (Python), JavaScript test runners (for Node.js components)
*   **Version Control**: Git, GitHub CLI (`gh`)

### Project Structure

The repository is organized into several key directories reflecting its multi-component nature. For a comprehensive guide to the repository structure, see **[docs/DIRECTORY_STRUCTURE.md](docs/DIRECTORY_STRUCTURE.md)**.

#### Core Application
*   `windows_ai/`: Main Python backend (FastAPI with 72+ endpoints, 2,600+ lines of code)
*   `windows-ai-agent/`: Node.js agent service
*   `windows-ai-tray/`: System tray application (Electron)
*   `apps/`: Node.js applications (actions, proxy, agenthub, etc.)

#### Key Features
*   `plugins/`: Plugin system with 6 built-in plugins and 2,600+ AI provider templates
*   `automation/`: Automation engine (folder watchers, scheduled tasks)
*   `gui/`: Main chat interface (Electron-based)
*   `control_center/`: Central management and coordination
*   `iot/`: Internet of Things integration
*   `mesh/`: Mesh networking capabilities
*   `mobile/`: Mobile companion app

#### Development & Documentation
*   `docs/`: All project documentation (60+ files)
*   `tests/`: Comprehensive test suite
*   `scripts/`: Build and utility scripts
*   `installer/`: Multi-platform installation system

#### Advanced Features
*   `domains/`: Domain-specific logic (audio, computer vision)
*   `sdk/`: Extension development kit
*   `marketplace/`: Plugin marketplace
*   `xr/`: Extended Reality support
*   `cloud_sync/`: Cloud synchronization
*   `search/`: Universal search

📚 **See [docs/DIRECTORY_STRUCTURE.md](docs/DIRECTORY_STRUCTURE.md) for detailed information about all 47 directories, organization principles, and maintenance guidelines.**

### Installation

To set up the development environment:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Anthony5265/Windows-AI.git
    cd Windows-AI
    ```
2.  **Python Dependencies**:
    Ensure you have `uv` installed. If not, you can install it via `pip install uv` or your preferred method.
    ```bash
    uv pip sync requirements.lock
    ```
3.  **Node.js Dependencies**:
    Navigate to the project root and install Node.js dependencies for all workspaces:
    ```bash
    npm install
    ```

### Usage

#### Running the Python Backend (FastAPI)

To start the main Python FastAPI application:
```bash
uvicorn windows_ai.main:app --host 0.0.0.0 --port 8010
```
