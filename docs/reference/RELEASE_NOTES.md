# Windows AI v0.2.0 Release Notes

**Release Date**: November 2025

## Overview

Windows AI v0.2.0 is a comprehensive AI-powered desktop assistant for Windows that brings modern AI capabilities directly to your desktop. This release includes a complete rewrite of the build system, improved stability, and a production-ready Windows executable installer.

---

## 🎉 What's New

### Windows Executable Release
- **Professional NSIS Installer**: One-click installation with desktop shortcuts and start menu integration
- **Portable Version**: Run Windows AI without installation
- **Multi-Architecture Support**: Both x64 and x86 (32-bit) builds available
- **Custom Icon**: Beautiful gradient icon with "W" branding

### Core Features

#### 💬 Chat Interface
- Real-time streaming AI responses via Server-Sent Events (SSE)
- Support for multiple AI models:
  - OpenAI GPT-3.5 & GPT-4
  - Anthropic Claude
  - Local Ollama models (Llama, Mistral, etc.)
- Persistent conversation history
- Beautiful dark/light theme with system integration
- Modern, responsive Electron-based UI

#### 🔧 Automation System
- **Folder Watchers**: Monitor directories and trigger AI actions on file changes
  - Pattern-based filtering (*.pdf, *.txt, etc.)
  - Actions: organize, summarize, analyze, custom
  - Debounced event handling
- **Task Scheduler**: Execute AI tasks on schedule
  - Cron expressions (e.g., "0 9 * * *")
  - Interval-based scheduling
  - Execution history tracking

#### 🎨 Plugin System
Six built-in plugins with extensible architecture:
1. **Web Search** - DuckDuckGo integration for real-time information
2. **File Organizer** - Intelligent file categorization
3. **System Info** - Real-time system metrics
4. **GitHub Integration** - Repository, issue, and PR management
5. **Code Executor** - Sandboxed Python/JS/Bash execution
6. **Calendar** - Event and reminder management

#### 🔔 System Tray Integration
- Global hotkey (`Ctrl+Shift+Space`) for quick access
- Quick command popup window
- Desktop notifications
- Status monitoring
- Double-click to open main GUI

### Backend Improvements
- FastAPI-based REST backend with 15+ endpoints
- WebSocket support for real-time bidirectional communication
- LiteLLM integration for multi-model AI support
- Improved error handling and logging
- Configuration management with persistent settings

---

## 🐛 Bug Fixes

### Critical Fixes
- **Fixed AgentHub import errors**: Added missing `Iterable` import and `CollaborationProtocol` class
- **Fixed duplicate method definitions**: Removed duplicate `deregister()` and `list_agents()` methods
- **Fixed missing attributes**: Added `_last_train` and `_last_run` dictionaries to AgentHub
- **Fixed MARKETPLACE_URL**: Added missing environment variable definition

### Python Fixes
- **Deprecated locale.getdefaultlocale()**: Replaced with `locale.getlocale()` to fix Python 3.15 deprecation warning
- **Cryptography module issues**: Fixed import errors in test suite
- **Test suite improvements**: Excluded GUI-dependent tests that require tkinter

### TypeScript/JavaScript Fixes
- **TypeScript compilation**: Successfully compiling actions-api without errors
- **Build system**: Improved build scripts and added proper npm scripts

---

## 📦 Installation & Usage

### Windows Installation

#### Option 1: NSIS Installer (Recommended)
1. Download `WindowsAI-0.2.0-x64.exe` (or `ia32` for 32-bit)
2. Run the installer
3. Follow the installation wizard
4. Launch from Start Menu or Desktop shortcut

#### Option 2: Portable Version
1. Download `WindowsAI-Portable-0.2.0-x64.exe`
2. Extract to any folder
3. Run `WindowsAI.exe`

### Running from Source

```bash
# Install dependencies
npm install
pip install -r requirements.txt

# Start all services
./start-all.sh        # Linux/Mac
start-all.bat         # Windows

# Or start individually
./start-backend.sh    # Backend only
./start-gui.sh        # GUI only
./start-tray.sh       # System tray only
```

### Quick Start
1. **Open the GUI**: Launch Windows AI from Start Menu
2. **Configure API Keys**: Settings → API Keys → Add your OpenAI/Anthropic key
3. **Start Chatting**: Type a message and press Enter
4. **Use Quick Commands**: Press `Ctrl+Shift+Space` anywhere for quick access
5. **Automate Tasks**: Settings → Automation → Add folder watchers or scheduled tasks

---

## 🔧 Technical Details

### System Requirements
- **OS**: Windows 10 or later (x64 or x86)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB for application + space for AI models if using Ollama
- **Node.js**: 18+ (only for development)
- **Python**: 3.11+ (included in installer)

### Architecture
- **Frontend**: Electron 38.4.0 with vanilla JavaScript
- **Backend**: FastAPI 0.119+ with Python 3.11
- **AI Gateway**: LiteLLM 1.78+ for multi-model support
- **Database**: JSON file-based storage for conversations and settings

### API Endpoints
- `POST /chat` - Send chat messages
- `GET /chat/stream` - Stream responses via SSE
- `GET /conversations` - List all conversations
- `GET /config` - Get configuration
- `POST /config` - Update configuration
- `GET /models` - List available AI models
- `POST /automation/watchers` - Create folder watcher
- `POST /automation/tasks` - Create scheduled task
- `GET /plugins` - List available plugins
- `POST /plugins/{name}/execute` - Execute plugin

---

## 📊 Build Information

### Build System
- **Icon Generation**: Automated Python script creates multi-size icons
- **Electron Builder**: Professional Windows installers with NSIS
- **TypeScript Compilation**: Actions-api built with TypeScript 5.9
- **Test Suite**: 172 tests covering core functionality

### Build Scripts
```bash
npm run build:icons      # Generate application icons
npm run build:gui        # Build Electron GUI
npm run build:release    # Complete release build
npm run test:python      # Run Python test suite
```

---

## 🚀 Future Roadmap

### Planned Features
- Windows Service integration for background operation
- Voice input/output support
- Context menu integration (right-click to send to AI)
- Screen capture and analysis
- Mobile companion app (iOS/Android)
- IoT device control via mesh networking
- Auto-update system
- Plugin marketplace

### Under Development
- Mobile apps (scaffolding exists)
- IoT integration (code present, needs integration)
- Mesh networking (code present, needs integration)
- Control center enhancements

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
# Clone repository
git clone https://github.com/Anthony5265/Windows-AI.git
cd Windows-AI

# Install dependencies
npm install
pip install -r requirements.txt

# Run tests
npm run test:python
npm test

# Start development
./start-all.sh
```

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

- Built with [Electron](https://www.electronjs.org/)
- Powered by [FastAPI](https://fastapi.tiangolo.com/)
- AI integration via [LiteLLM](https://github.com/BerriAI/litellm)
- Icons generated with [Pillow](https://python-pillow.org/)

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Anthony5265/Windows-AI/issues)
- **Documentation**: [docs/](docs/)
- **Getting Started**: [GETTING_STARTED.md](GETTING_STARTED.md)

---

**Thank you for using Windows AI!** 🎉
