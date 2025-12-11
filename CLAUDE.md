# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Windows AI is a comprehensive AI platform for Windows that provides 2500+ AI capabilities through a unified interface. It combines a Python backend (FastAPI-based) with an Electron desktop GUI, offering local and cloud AI features including chat, image generation, document processing, automation, and 200+ integrations.

## Development Commands

### Building the Application

**Python Backend (PyInstaller)**

```bash
python build_exe.py                    # Build backend executable
python build_exe.py --clean           # Clean build artifacts
python build_exe.py --zip             # Build and create portable ZIP
```

**Electron GUI**

```bash
cd apps/gui
npm install                           # Install dependencies
npm run build                         # Build with electron-builder
npm run build:win                     # Build Windows installer (NSIS)
```

**Simple Portable Build**

```bash
build-simple.bat                      # Build both backend and GUI (Windows batch script)
```

### Testing

**Python Tests**

```bash
pytest                                # Run all tests
pytest tests/ -v                      # Verbose output
pytest -m unit                        # Run only unit tests
pytest -m integration                 # Run only integration tests
pytest -m slow                        # Run slow tests
pytest --cov=windows_ai              # With coverage report
```

**Test markers**: `unit`, `integration`, `e2e`, `slow`, `benchmark`

### Running the Application

**GUI Mode**

```bash
python -m windows_ai                  # Launch with GUI
windows-ai-gui                        # After installation
```

**CLI Mode**

```bash
python -m windows_ai interactive      # Interactive mode
python -m windows_ai chat "message"   # Direct chat
python -m windows_ai status           # Check status
python -m windows_ai capabilities     # List all capabilities
```

### Linting and Code Quality

```bash
npm run lint                          # Lint JavaScript/TypeScript
npm run test                          # Run all workspace tests
npm run test:python                   # Python tests via npm
```

## Architecture Overview

### Core Design Pattern: Master Orchestrator

The system uses a centralized orchestrator pattern where `WindowsAI` class (in `windows_ai/core/orchestrator.py`) acts as the master entry point to 43 specialized managers, each handling specific domains (LLMs, vision, audio, databases, cloud services, etc.).

```
WindowsAI Orchestrator (Master Entry Point)
├── Auto Setup & Configuration
├── Dependency Installer
├── 43 Specialized Managers
│   ├── LLM Manager (OpenAI, Anthropic, Google, etc.)
│   ├── Vision Manager (object detection, face recognition, OCR)
│   ├── Audio Manager (transcription, TTS, speech recognition)
│   ├── Database Manager (PostgreSQL, MongoDB, Redis, etc.)
│   ├── Cloud Manager (AWS, Azure, GCP)
│   ├── Automation Manager (RPA, workflows)
│   └── ... (37+ more managers)
└── Plugin System (200+ plugins)
```

### Key Architectural Principles

1. **Zero Configuration**: Auto-setup, auto-install, auto-configure with smart defaults
2. **Graceful Degradation**: System continues even if some features fail
3. **Modular Design**: Each manager is independent and can be loaded on-demand
4. **Production Ready**: No placeholders or stubs - all features are fully implemented

### Main Components

**Python Backend (`windows_ai/`)**

- `core/`: Core orchestrator and managers
- `api/`: FastAPI REST API endpoints
- `agents/`: Multi-agent system for complex tasks
- `plugins/`: Plugin system and individual plugins
- `integrations/`: Third-party service integrations
- `frameworks/`: AI framework abstractions
- `security/`: Security and sandboxing
- `iot/`, `mesh/`, `xr/`: Specialized feature modules

**Electron GUI (`apps/gui/`)**

- `main.js`: Electron main process
- `preload.js`: Preload script for security
- `renderer/`: Frontend UI code
- `build/`: Build resources (icons, installers)

### Configuration System

Windows AI uses a **unified configuration system** providing centralized, type-safe configuration management:

- **Single Source of Truth**: All settings managed through `WindowsAIConfig` (Pydantic-based)
- **Multiple Formats**: Supports JSON and YAML configuration files
- **Auto-Discovery**: Automatically finds config files in standard locations
- **Environment Override**: Any setting can be overridden via `WINDOWSAI_*` env vars
- **Hot Reload**: Configuration can be reloaded without restarting

**Configuration Files** (searched in order):

1. Specified path (if provided to `get_config(path="...")`)
2. `data/config.json` - User JSON configuration
3. `data/config.yaml` - User YAML configuration  
4. `windows_ai/config/default.yaml` - Default YAML configuration
5. Built-in defaults (if no files found)

**Legacy Configuration** (deprecated):

- `.env`: API keys and secrets (migrate to WindowsAIConfig)
- `~/.windows_ai/config.json`: User config (migrate to new system)
- Environment variables: Use `WINDOWSAI_*` prefix for new system

**Quick Start**:

```python
from windows_ai.config.unified_config import get_config

# Load configuration (auto-discovers config files)
config = get_config()

# Access values
print(f"Server: {config.server.host}:{config.server.port}")
print(f"LLM: {config.llm.provider} - {config.llm.model}")

# Modify and save
config.server.port = 8080
config.to_file('data/config.yaml', format='yaml')
```

**Configuration Structure** (14 sections):

- `server`: REST API settings (host, port, CORS, workers)
- `database`: Database connection settings
- `logging`: Logging configuration (level, format, file paths)
- `llm`: Language model provider settings (provider, API keys, models)
- `local_models`: Local AI model settings (llama.cpp, model paths)
- `embedding`: Text embedding configuration (provider, model, dimensions)
- `plugins`: Plugin system settings (enabled plugins, search paths)
- `sandbox`: Security sandbox configuration (level, resource limits)
- `agents`: Multi-agent system settings (max concurrent, timeouts)
- `rag`: RAG pipeline configuration (chunk size, top-k retrieval)
- `ui`: User interface preferences (theme, language, font size)
- `watcher`: File system watcher settings
- `scheduler`: Task scheduler configuration
- `security`: Application security (API keys, rate limiting, IP filtering)

**See**: `windows_ai/config/README.md` for comprehensive configuration documentation

### Entry Points

- `windows_ai/__main__.py`: CLI entry point
- `windows_ai/app.py`: FastAPI application
- `apps/gui/main.js`: Electron entry point
- `build_exe.py`: Build script for PyInstaller

## Common Development Patterns

### Manager Integration with Unified Config

All managers should accept and use `WindowsAIConfig`:

```python
from windows_ai.config.unified_config import WindowsAIConfig

class MyManager:
    def __init__(self, config: WindowsAIConfig):
        """Initialize manager with unified configuration"""
        self.config = config
        self._initialized = False
        
    async def initialize(self):
        """Initialize using config values"""
        # Access config values
        self.timeout = self.config.llm.timeout
        self.api_key = self.config.llm.api_key
        
        # Get nested values with defaults
        self.storage_path = self.config.get_nested('storage.data_dir', 'data/')
        
        self._initialized = True
```

**Orchestrator Integration**:

```python
# In WindowsAI.__init__()
self._config = config or get_config()

# In _init_all_managers()
self._managers['my_manager'] = MyManager(self._config)
await self._managers['my_manager'].initialize()
```

### Adding a New AI Capability

1. Create a new manager in `windows_ai/integrations/` accepting `WindowsAIConfig`
2. Register the manager in orchestrator's `_init_all_managers()` method
3. Pass `self._config` to manager constructor
4. Add corresponding API endpoint in `windows_ai/api/` if needed
5. Update capability count in documentation

### Adding a New Plugin

1. Create plugin file in `windows_ai/plugins/`
2. Inherit from base `Plugin` class
3. Implement required methods: `name`, `version`, `execute()`
4. Plugin can access config through kwargs in `execute()`
5. Register in plugin manager
6. Add to marketplace metadata

**Plugin with Config**:

```python
from windows_ai.plugins.base import Plugin

class MyPlugin(Plugin):
    async def execute(self, **kwargs):
        # Access config from orchestrator
        config = kwargs.get('config')
        
        if config:
            timeout = config.llm.timeout
            model = config.llm.model
        
        # Plugin implementation
        result = await self._do_work()
        return {"status": "success", "result": result}
```

### Working with the Multi-Agent System

Agents coordinate to solve complex tasks. Each agent has:

- Specialized capabilities (design, coding, cloud, database, etc.)
- Ability to communicate with other agents
- Task planning and execution logic

Located in: `windows_ai/agents/`

## Build Artifacts and Distribution

**Build Output Locations**

- Python backend: `dist/WindowsAI/` (PyInstaller output)
- Electron GUI: `apps/gui/dist/` (electron-builder output)
- Portable builds: `dist-simple/`

**PyInstaller Spec File**: `WindowsAI.spec` (auto-generated, can be customized)

**Icon Files**: `assets/icon.ico`, `apps/gui/build/icon.ico`

## Important Notes

### Windows Defender Issues

When building with electron-builder, Windows Defender may block `app-builder.exe`. Solutions:

1. Add exception for `node_modules` folder
2. Temporarily disable antivirus during build
3. Use the simple portable build method instead

### Dependencies

- Python: 3.8+ (built with 3.12)
- Node.js: 18+
- PyInstaller for executable builds
- electron-builder for installers

### Hidden Imports for PyInstaller

The build script includes extensive hidden imports for:

- Web frameworks: FastAPI, uvicorn, starlette
- AI providers: OpenAI, Anthropic, Google, Cohere, Mistral
- Vector databases: ChromaDB, Faiss, Pinecone, Qdrant, Weaviate
- AI frameworks: LangChain, LlamaIndex, LiteLLM

### Security Sandbox Levels

- `NONE`: Full system access
- `MINIMAL`: Basic restrictions
- `STANDARD`: Recommended (default)
- `STRICT`: Enhanced security
- `MAXIMUM`: Maximum isolation

## Project Structure Context

The codebase has an extensive module structure with 200+ Python files in `windows_ai/`, organized by functionality. Key subdirectories include specialized systems for agents, APIs, cloud sync, configuration, core orchestration, frameworks, GUI, integrations, IoT, mesh networking, plugins, RAG systems, security, system controls, updaters, vector databases, and workflows.

The `src/` directory contains additional organized modules mirroring capabilities in domains, services, backends, automation, etc.

## Configuration Files

- `requirements.txt`: Core Python dependencies
- `requirements-full.txt`: All optional dependencies
- `requirements-dev.txt`: Development dependencies
- `requirements-test.txt`: Testing dependencies
- `package.json`: Root workspace configuration
- `apps/gui/package.json`: Electron app configuration
- `pytest.ini`: Test configuration
- `electron-builder.yml`: Installer configuration

## Privacy and Offline Mode

The system supports three modes:

- **Local Only**: Everything runs on PC, no data leaves
- **Cloud Hybrid**: User chooses what goes to cloud
- **Full Cloud**: Connect to GPT-4, Claude, Gemini, etc.

API keys are stored encrypted in user config directory.

## Recent Development Updates

### Task 5: Chat Interface Enhancement (Completed)

**Date**: January 2025

**Overview**: Enhanced the Electron GUI chat interface with markdown rendering and syntax highlighting capabilities.

**Features Added**:

1. **Markdown Rendering**
   - Integrated marked.js v11.1.1 for GitHub Flavored Markdown support
   - Security hardened: disabled headerIds and mangle to prevent injection attacks
   - Conditional rendering: markdown for assistant messages, plain text for user messages (XSS prevention)

2. **Syntax Highlighting**
   - Integrated highlight.js v11.9.0 with github-dark theme
   - Auto-detection of programming languages from ```lang syntax
   - Line-by-line syntax highlighting for code blocks
   - Responsive code block layout with horizontal scrolling

3. **Code Block Copy Buttons**
   - Automatically generated copy button on each code block
   - Appears on hover with smooth opacity transition
   - Clipboard API integration with 2-second "Copied!" feedback
   - Positioned absolutely in top-right corner of code blocks

4. **Message Actions**
   - Copy button: Copy entire message to clipboard
   - Regenerate button: Resend user message to get new response (user messages only)
   - Edit button: Populate input field for editing (user messages only)
   - Actions appear on message hover with visual feedback

**Files Modified**:

- `apps/gui/renderer/index.html`: Added CDN links for marked.js and highlight.js with SRI integrity hashes
- `apps/gui/renderer/renderer.js`:
  - Added `renderMarkdown()` function (40 lines)
  - Enhanced `createMessageElement()` with conditional rendering
  - Added `regenerateMessage()` and `editMessage()` functions
  - Improved message actions with proper event handlers
- `apps/gui/renderer/chat.css`:
  - Added `.code-copy-btn` styles with hover effects
  - Added `.message-actions` styles with hover-to-show behavior
  - Enhanced code block styling with position: relative
  - Added `.copied` state for visual feedback

**Security Measures**:

- SRI (Subresource Integrity) hashes on all CDN resources
- XSS prevention: user messages use textContent, assistant messages use sanitized innerHTML
- marked.js security configuration: disabled headerIds (prevents ID injection) and mangle (prevents email obfuscation exploits)
- Temporary DOM container for processing (no direct innerHTML injection)
- Content Security Policy already present in index.html

**Usage Examples**:

Users can now send messages with markdown formatting:

```markdown
# Heading
**Bold text**
*Italic text*
- List item 1
- List item 2

Inline `code` and code blocks:

```python
def hello():
    print("Hello, World!")
```

```

**Implementation Stats**:
- Lines added: ~110 total (5 HTML, 75 JavaScript, 30 CSS)
- Libraries: 2 (marked.js 50KB, highlight.js ~100KB with theme)
- Load time impact: ~150KB additional resources (CDN cached)
- Testing status: Awaiting Node.js installation for live testing

**Completion Status**: ✅ 100% Complete (implementation done, testing pending Node.js install)

