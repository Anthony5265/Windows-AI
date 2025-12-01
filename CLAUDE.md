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

**Configuration**
- `.env`: API keys and secrets (not committed)
- `~/.windows_ai/config.json`: User configuration
- Environment variables for cloud provider credentials

### Entry Points

- `windows_ai/__main__.py`: CLI entry point
- `windows_ai/app.py`: FastAPI application
- `apps/gui/main.js`: Electron entry point
- `build_exe.py`: Build script for PyInstaller

## Common Development Patterns

### Adding a New AI Capability

1. Create a new manager in `windows_ai/core/` or extend existing manager
2. Register the manager in the orchestrator's `_init_all_managers()` method
3. Add corresponding API endpoint in `windows_ai/api/` if needed
4. Update capability count in documentation

### Adding a New Plugin

1. Create plugin file in `windows_ai/plugins/`
2. Inherit from base `Plugin` class
3. Implement required methods: `name`, `version`, `execute()`
4. Register in plugin manager
5. Add to marketplace metadata

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
