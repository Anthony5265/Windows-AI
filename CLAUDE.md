# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **⚠️ MANDATORY:** Before starting any development work, read `ROADMAP.md` and `BLUEPRINT.md` in full. Those are the single sources of truth for project status, architecture, and priorities. All work must follow the phased roadmap. See [Agent Compliance](#agent-compliance-rules) at the bottom of this file.

## Project Overview

Windows AI is a comprehensive AI platform for Windows that provides 2,000+ AI capabilities through a unified interface. It combines a Python backend (FastAPI-based) with an Electron desktop GUI, offering local and cloud AI features including chat, image generation, document processing, automation, and 200+ integrations.

**Current Project Status:** ~75% production-ready (see `ROADMAP.md` for detailed breakdown)

### Honest Status Assessment

**What Works (Production-Ready):**
- ✅ Core orchestrator and plugin architecture (100%)
- ✅ API server with REST endpoints (100%)
- ✅ Security system with multi-level sandbox (100%)
- ✅ Build system (PyInstaller + Electron) (100%)
- ✅ 2,203 plugins across 27 categories in `builtin/` (~90% functional)
- ✅ Windows Core Plugins (51/51 complete)
- ✅ Windows OS Plugins (31/31 complete)
- ✅ Audio Model Plugins (29 plugins, 300–650 lines each — real implementations)
- ✅ Vision Model Plugins (21 plugins, 150–320 lines each — real implementations)
- ✅ Code Model Plugins (16 plugins, 296–416 lines each — real implementations)
- ✅ 253 test files (passing)
- ✅ Unified configuration system (100%)
- ✅ Search module (29 files, 10,007 lines)
- ✅ IoT module (37 files in `iot/` + 12 files in `windows_ai/iot/`)
- ✅ Optimization module (14 files, 1,532 lines)
- ✅ XR module (runtime 230 lines, input_manager 319 lines, spatial_ui)
- ✅ Security module (14+ files, 11 subdirectories)

**Areas Needing Work (Not stubs — need expansion or testing):**
- ⚠️ RAG pipeline (3 files — needs expansion to full retrieval chain)
- ⚠️ Mobile companion app (`mobile/` — has TypeScript code but needs integration)
- ⚠️ CI/CD pipelines (~70%)
- ⚠️ Documentation (~65% consolidated)
- ⚠️ Test coverage (~35% — target is 60%+)

**When working on this codebase:** Be honest about implementation status. Verify actual file contents before making assertions. Use `ROADMAP.md` and `BLUEPRINT.md` as the sources of truth.

**⚠️ Plugin Path Correction:** Audio/Vision/Code model plugins live at `windows_ai/plugins/builtin/audio_models/`, `vision_models/`, `code_models/` respectively. There are NO directories at `windows_ai/plugins/audio_ai/`, `vision_ai/`, or `code_ai/`.

---

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
pytest -m e2e                         # Run end-to-end tests
pytest -m slow                        # Run slow tests
pytest -m critical                    # Run critical path tests
pytest --cov=windows_ai              # With coverage report
pytest tests/ -v --tb=short          # Short traceback format
```

**Test markers**: `unit`, `integration`, `e2e`, `slow`, `critical`

**Note:** Tests are configured for auto async mode. All async test functions work without explicit event loop setup.

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

**Workspace Scripts** (from root package.json):
```bash
npm run build:gui                     # Build Electron GUI
npm run build:icons                   # Generate icon assets
npm run start:backend                 # Start Python backend
npm run start:all                     # Start all services
```

---

## Architecture Overview

### Core Design Pattern: Master Orchestrator

The system uses a centralized orchestrator pattern where `WindowsAI` class (in `windows_ai/core/orchestrator.py`) acts as the master entry point to 43+ specialized managers, each handling specific domains (LLMs, vision, audio, databases, cloud services, etc.).

```
WindowsAI Orchestrator (Master Entry Point)
├── Auto Setup & Configuration
├── Dependency Installer
├── 43+ Specialized Managers
│   ├── LLM Manager (OpenAI, Anthropic, Google, etc.)
│   ├── Vision Manager (object detection, face recognition, OCR)
│   ├── Audio Manager (transcription, TTS, speech recognition)
│   ├── Database Manager (PostgreSQL, MongoDB, Redis, etc.)
│   ├── Cloud Manager (AWS, Azure, GCP)
│   ├── Automation Manager (RPA, workflows)
│   └── ... (37+ more managers)
└── Plugin System (2,151 plugins - 96.1% functional)
```

### Key Architectural Principles

1. **Zero Configuration**: Auto-setup, auto-install, auto-configure with smart defaults
2. **Graceful Degradation**: System continues even if some features fail
3. **Modular Design**: Each manager is independent and can be loaded on-demand
4. **Production Ready**: No placeholders or stubs in core features - all features are fully implemented (except noted gaps)
5. **Security First**: "Freedom First" philosophy - all restrictive features OFF by default, users opt-in

### Main Components

**Python Backend (`windows_ai/`)**

- `core/`: Core orchestrator and managers
- `api/`: FastAPI REST API endpoints
- `agents/`: Multi-agent system for complex tasks
- `plugins/`: Plugin system and individual plugins
- `integrations/`: Third-party service integrations
- `frameworks/`: AI framework abstractions
- `security/`: Security and sandboxing
- `config/`: Unified configuration system
- `iot/`: IoT device integration (partial)
- `mesh/`: Mesh networking (partial)
- `xr/`: XR/VR support (placeholder)
- `cloud_sync/`: Cloud synchronization
- `rag/`: RAG pipeline components
- `vector_db/`: Vector database integrations
- `workflow/`: Workflow automation
- `terminal/`: Terminal integration
- `snapshot/`: System snapshot capabilities
- `search/`: Search modules (mostly stubs - needs implementation)
- `powershell/`: PowerShell integration
- `system/`: System-level operations
- `system_controls/`: System control interfaces
- `updater/`: Auto-update system
- `rollback/`: Rollback capabilities

**Electron GUI (`apps/gui/`)**

- `main.js`: Electron main process (~15KB)
- `preload.js`: Preload script for security (~5.6KB)
- `updater.js`: Update handling (~10KB)
- `renderer/`: Frontend UI code
  - `index.html`: Main HTML template
  - `renderer.js`: Frontend logic with markdown rendering
  - `chat.css`: Chat interface styles
  - `styles.css`: Global styles
- `build/`: Build resources (icons, installers)
- `electron-builder.yml`: Electron Builder configuration

**Other Key Directories**

- `apps/`: Electron applications (gui, proxy, actions)
- `scripts/`: Build, automation, and utility scripts
- `tests/`: Comprehensive test suite (621+ tests)
- `docs/`: Documentation files
- `assets/`: Icons, templates, and resources
- `codex/`: Development task tracking and history

### Directory Structure Details

**Top-level directories:**
- `windows_ai/`: Main Python package (25 subdirectories, 200+ files)
- `src/`: Additional organized modules (mirrors some capabilities)
- `domains/`: Domain-specific implementations
- `agenthub/`: Agent coordination hub
- `automation/`: Automation workflows
- `model_discovery/`: AI model discovery system
- `mobile/`: Mobile companion (placeholder)
- `installer/`: Installation system
- `templates/`: Application templates
- `tools/`: Developer tools
- `vendor/`: Third-party dependencies

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

**Environment Variable Examples**:

```bash
export WINDOWSAI_SERVER__PORT=8080                    # Set server port
export WINDOWSAI_LLM__PROVIDER=anthropic              # Set LLM provider
export WINDOWSAI_LLM__API_KEY=sk-ant-xxxxx            # Set API key
export WINDOWSAI_LOCAL_MODELS__LLAMA_CPP_PATH=/path   # Set llama.cpp path
```

**See**: `windows_ai/config/README.md` for comprehensive configuration documentation

### Entry Points

- `windows_ai/__main__.py`: CLI entry point
- `windows_ai/app.py`: FastAPI application
- `apps/gui/main.js`: Electron entry point
- `build_exe.py`: Build script for PyInstaller

---

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
6. Write comprehensive tests in `tests/`
7. Update TODO_MASTER.md with completion status

### Adding a New Plugin

1. Create plugin file in `windows_ai/plugins/`
2. Inherit from base `Plugin` class
3. Implement required methods: `name`, `version`, `execute()`
4. Plugin can access config through kwargs in `execute()`
5. Register in plugin manager
6. Add to marketplace metadata
7. Write tests for the plugin

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

**Key agent files:**
- `code_completion_agent.py`: Code completion tasks
- `test_generator_mcp.py`: Test generation
- `import_fixer_agent.py`: Import fixing
- `coverage_analysis_mcp.py`: Coverage analysis

### Writing Tests

**Test Organization:**

```python
import pytest
from windows_ai.core.orchestrator import WindowsAI

@pytest.mark.unit
async def test_basic_functionality():
    """Test basic functionality"""
    ai = WindowsAI()
    result = await ai.some_method()
    assert result is not None

@pytest.mark.integration
async def test_integration():
    """Test integration between components"""
    pass

@pytest.mark.slow
async def test_expensive_operation():
    """Test that takes significant time"""
    pass

@pytest.mark.critical
async def test_critical_path():
    """Test critical functionality"""
    pass
```

**Running specific test categories:**
```bash
pytest -m unit          # Fast unit tests
pytest -m integration   # Integration tests
pytest -m critical      # Critical path only
pytest -m "not slow"    # Skip slow tests
```

### Security-First Development

**"Freedom First" Philosophy**: All restrictive security features are OFF by default. Users explicitly opt-in to security controls.

**When adding security features:**

1. Default state: DISABLED
2. Provide clear documentation on enabling
3. Make configuration obvious and accessible
4. Never enable without user consent
5. Log security state changes

**Example:**

```python
class SecurityFeature:
    def __init__(self, config: WindowsAIConfig):
        # Default to disabled - user must opt-in
        self.enabled = config.security.get('feature_name_enabled', False)

    async def initialize(self):
        if not self.enabled:
            logger.info("SecurityFeature disabled by default (Freedom First)")
            return

        logger.info("SecurityFeature enabled by user configuration")
        # Setup security feature
```

### Stub Detection and Implementation

**Before claiming a feature works:**

1. Read the actual implementation file
2. Check file size (stubs are typically <50 lines)
3. Look for TODO, FIXME, XXX, HACK, BUG comments
4. Verify imports are used, not just declared
5. Check for actual implementation logic

**Common stub patterns to avoid:**

```python
# BAD - This is a stub
class AudioPlugin(Plugin):
    async def execute(self, **kwargs):
        # TODO: Implement actual audio processing
        raise NotImplementedError("Audio processing not yet implemented")
```

**Proper implementation:**

```python
# GOOD - This is implemented
class AudioPlugin(Plugin):
    async def execute(self, **kwargs):
        audio_file = kwargs.get('audio_file')

        # Actual implementation with error handling
        try:
            result = await self._process_audio(audio_file)
            return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            return {"status": "error", "error": str(e)}
```

---

## Build Artifacts and Distribution

**Build Output Locations**

- Python backend: `dist/WindowsAI/` (PyInstaller output)
- Electron GUI: `apps/gui/dist/` (electron-builder output)
- Portable builds: `dist-simple/`

**PyInstaller Spec File**: `WindowsAI.spec` (auto-generated, can be customized)

**Icon Files**: `assets/icon.ico`, `apps/gui/build/icon.ico`

**Electron Builder Config**: `apps/gui/electron-builder.yml`

---

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

**Python Dependencies:**
- `requirements.txt`: Core Python dependencies
- `requirements-full.txt`: All optional dependencies
- `requirements-dev.txt`: Development dependencies
- `requirements-test.txt`: Testing dependencies
- `requirements.lock`: Locked versions

**Node Dependencies:**
- `package.json`: Root workspace configuration
- `apps/gui/package.json`: Electron app configuration
- Workspaces enabled for monorepo structure

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

**Default**: User chooses during setup, defaults OFF (Freedom First philosophy)

---

## Project Structure Context

The codebase has an extensive module structure with 200+ Python files in `windows_ai/`, organized by functionality. Key subdirectories include specialized systems for agents, APIs, cloud sync, configuration, core orchestration, frameworks, GUI, integrations, IoT, mesh networking, plugins, RAG systems, security, system controls, updaters, vector databases, and workflows.

The `src/` directory contains additional organized modules mirroring capabilities in domains, services, backends, automation, etc.

**File count breakdown** (from comprehensive analysis):
- Total Python files: 3,468
- Code quality markers: 938 (TODOs, FIXMEs, XXXs, HACKs, BUGs)
- Functional plugins: 2,068
- Stub plugins: 83 (critical gap in AI features)
- Generated plugins (unverified): 381

---

## Configuration Files

- `requirements.txt`: Core Python dependencies
- `requirements-full.txt`: All optional dependencies
- `requirements-dev.txt`: Development dependencies
- `requirements-test.txt`: Testing dependencies
- `requirements.lock`: Locked dependency versions
- `package.json`: Root workspace configuration
- `apps/gui/package.json`: Electron app configuration
- `pytest.ini`: Test configuration
- `electron-builder.yml`: Installer configuration
- `.pre-commit-config.yaml`: Pre-commit hooks
- `.commitlint.config.js`: Commit message linting (conventional commits)
- `.editorconfig`: Editor configuration
- `.gitignore`: Git ignore patterns
- `.gitleaks.toml`: Secret scanning configuration

---

## Privacy and Offline Mode

The system supports three modes:

- **Local Only**: Everything runs on PC, no data leaves
- **Cloud Hybrid**: User chooses what goes to cloud
- **Full Cloud**: Connect to GPT-4, Claude, Gemini, etc.

API keys are stored encrypted in user config directory.

---

## Git Workflow and Conventions

### Branch Naming

**For Claude Code tasks**, use branch naming pattern: `claude/<description>-<session-id>`

**Examples:**
- `claude/add-feature-xyz-a1b2c`
- `claude/fix-bug-abc-d3e4f`
- `claude/refactor-component-g5h6i`

**CRITICAL**: Branch name MUST start with `claude/` and end with session ID, otherwise git push will fail with 403 error.

### Commit Messages

Follow **Conventional Commits** specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

**Examples:**
```
feat(plugins): Add audio transcription plugin

Implement Whisper-based audio transcription with support for
multiple audio formats and languages.

Closes #123
```

```
fix(api): Resolve CORS issue in chat endpoint

Update CORS configuration to allow requests from Electron GUI.
Add proper error handling for cross-origin requests.
```

### Push Workflow

**For feature branches:**

```bash
# Push with upstream tracking
git push -u origin claude/feature-name-abc123

# Retry on network failures (up to 4 times with exponential backoff)
# Automatic retry: 2s, 4s, 8s, 16s
```

**For pull requests:**

```bash
# Create PR using GitHub CLI
gh pr create --title "feat: Add feature X" --body "$(cat <<'EOF'
## Summary
- Implemented feature X
- Added comprehensive tests
- Updated documentation

## Test plan
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
EOF
)"
```

---

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

**Completion Status**: ✅ 100% Complete

### Recent Security Enhancements (December 2025)

**Philosophy**: "Freedom First" - All restrictive security features OFF by default

**Implemented**:
- Unrestricted system configuration by default
- User-controlled security opt-in model
- Comprehensive security test suite
- Threat monitoring (optional, disabled by default)
- Audit logging (optional, disabled by default)

**File**: See commits `9473d65` and recent security module updates

### Windows Plugin Completion (December 2025)

**Completed**:
- ✅ 49 Windows Core Plugins (100%)
- ✅ 30 Windows OS Plugins (100%)
- ✅ Comprehensive implementations (185-1200 lines each)
- ✅ Full test coverage for Windows plugins

**Notable plugins**:
- Terminal, Window Manager, USB Management, Bluetooth
- PowerShell Bridge, Registry Management, Event Log
- WinRM, Windows Store API, WSL2, Hyper-V integration

### Comprehensive CLAUDE.md Documentation Update (January 2026)

**Overview**: Rewrote and expanded CLAUDE.md to serve as a complete AI-assistant guide for the Windows AI codebase.

**Changes Made** (merged via PR #492, originally proposed in PR #491):
- Added honest project status assessment (50-55% complete)
- Documented all architecture components and directory structure
- Included complete configuration system guide with examples
- Added development patterns, testing guidelines, and security philosophy
- Documented critical gaps: Audio AI, Vision AI, Code AI, Search modules
- Included git workflow, commit conventions, and branch naming
- Added best practices section for AI assistants
- Added quick reference commands and documentation links
- Provided 10 key takeaways for working with the codebase

**Completion Status**: ✅ 100% Complete

---

## Areas Needing Work

> **Note:** The following areas are NOT stubs — they have real implementations. They need expansion, testing, or integration work. Always check `ROADMAP.md` for the current phase priorities.

### 1. RAG Pipeline (3 files — needs expansion)

Location: `windows_ai/rag/` (engine.py, api.py, __init__.py)

**Needs:**
- Full retrieval chain with chunking, embedding, retrieval, re-ranking
- Integration with the existing 29-file search module
- Hybrid search (BM25 + dense vector)

### 2. Mobile Companion App

Location: `mobile/` (root-level directory)

**Has:** TypeScript modules (adapter, trainer, studio, toolkit, analyzer, monitor, bridge, coordinator), QR pairing flow
**Needs:** Integration with desktop backend, push notifications, testing

### 3. Test Coverage (target: 60%+, currently ~35%)

**Needs:**
- Unit tests for all 31 windows_os plugins
- Integration tests for search module (29 files)
- Tests for IoT, XR, and optimization modules
- Coverage reporting in CI

### 4. Documentation Consolidation (~65%)

**Needs:**
- Plugin index document (`docs/plugins/PLUGIN_INDEX.md`)
- API reference update (`docs/api/API_REFERENCE.md`)
- Plugin development guide

---

## Correct Plugin Paths — IMPORTANT

| Category | Correct Path | Count | Status |
|---|---|---|---|
| Windows | `windows_ai/plugins/builtin/windows/` | 51 | ✅ Production |
| Windows OS | `windows_ai/plugins/builtin/windows_os/` | 31 | ✅ Production |
| Audio Models | `windows_ai/plugins/builtin/audio_models/` | 29 | ✅ Functional (300–650 lines) |
| Vision Models | `windows_ai/plugins/builtin/vision_models/` | 21 | ✅ Functional (150–320 lines) |
| Code Models | `windows_ai/plugins/builtin/code_models/` | 16 | ✅ Functional (296–416 lines) |

**⚠️ These paths DO NOT EXIST:** `windows_ai/plugins/audio_ai/`, `windows_ai/plugins/vision_ai/`, `windows_ai/plugins/code_ai/`

---

## Best Practices for AI Assistants

### 1. Always Verify Before Claiming

```python
# DON'T assume features work - read the file first
# DO verify implementation before making claims

# Read file
with open('windows_ai/plugins/audio_ai/voice_cloning.py') as f:
    content = f.read()

# Check if it's a stub
if 'NotImplementedError' in content or 'TODO' in content:
    # It's a stub - don't claim it works
    pass
```

### 2. Honest Status Reporting

**DO:**
- "This feature is currently a stub and needs implementation"
- "The core functionality works, but advanced features are incomplete"
- "According to TODO_MASTER.md, this area is 20% complete"

**DON'T:**
- "All features are fully functional" (when many are stubs)
- "This works perfectly" (without checking the code)
- Claim features exist when they're placeholders

### 3. Reference Documentation Correctly

- Check TODO_MASTER.md for current completion status
- Read COMPREHENSIVE_GAP_ANALYSIS.md for detailed gaps
- Verify claims against actual code files
- Update documentation when making changes

### 4. Follow Security Philosophy

- Default to permissive settings (Freedom First)
- Let users opt-in to restrictions
- Document security implications clearly
- Never enable restrictive features without user consent

### 5. Test Coverage

- Write tests for new features
- Use appropriate pytest markers
- Ensure async tests work correctly
- Run tests before claiming completion

### 6. Configuration Management

- Use unified config system (WindowsAIConfig)
- Avoid creating new config systems
- Use environment variables for overrides
- Document all config options

### 7. Error Handling

```python
# DO: Comprehensive error handling
async def execute(self, **kwargs):
    try:
        result = await self._process()
        return {"status": "success", "result": result}
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {"status": "error", "error": "Internal error"}

# DON'T: Silent failures or bare excepts
async def execute(self, **kwargs):
    try:
        result = self._process()
        return result
    except:
        pass  # BAD - silent failure
```

---

## Useful Scripts

**Located in `scripts/` directory:**

- `create_comprehensive_tests.py`: Generate test stubs
- `implement_all_plugins.py`: Bulk plugin implementation
- `fix_all_documentation.py`: Documentation fixes
- `final_build_and_verify.py`: Build verification
- `fast_implement.sh`: Quick implementation workflow
- `generators/`: Code generation tools
- `automation/`: Automation utilities
- `ci/`: CI/CD scripts

**Entry point scripts** (root directory):

- `start-backend.sh`: Start Python backend
- `start-gui.sh`: Start Electron GUI
- `start-backend.bat`: Windows batch for backend
- `start-gui.bat`: Windows batch for GUI
- `build-release.sh`: Release build script

---

## Documentation References

**Primary Documentation:**
- `README.md`: User-facing overview
- `CLAUDE.md`: This file - AI assistant guide
- `TODO_MASTER.md`: Comprehensive task tracking
- `COMPREHENSIVE_GAP_ANALYSIS.md`: Detailed gap analysis
- `USER_MANUAL.md`: User manual
- `FEATURES.md`: Feature overview
- `CONTRIBUTING.md`: Contribution guidelines
- `SECURITY.md`: Security policy

**Technical Documentation** (`docs/`):
- `API_REFERENCE.md`: API documentation
- `CONFIGURATION_MIGRATION.md`: Config migration guide
- `DIRECTORY_STRUCTURE.md`: Directory organization
- `LOCAL_MODELS.md`: Local model usage
- `OLLAMA_INTEGRATION.md`: Ollama integration
- `FAQ.md`: Frequently asked questions

**Development Documentation:**
- `windows_ai/config/README.md`: Configuration system guide
- `codex/README_Codex.md`: Codex development environment
- Various `README.md` files in subdirectories

---

## Summary: Key Takeaways

1. **Project is ~50-55% complete** - Be honest about implementation status
2. **Core systems work well** - Orchestrator, API, security, build system
3. **Critical gaps exist** - Audio AI, Vision AI, Code AI, Search modules are mostly stubs
4. **Use unified config** - WindowsAIConfig for all configuration needs
5. **Security first** - But freedom-oriented (OFF by default)
6. **Test everything** - Comprehensive test suite with pytest markers
7. **Verify before claiming** - Read files, check for stubs/TODOs
8. **Follow conventions** - Commit messages, branch naming, code style
9. **Document changes** - Update TODO_MASTER.md and relevant docs
10. **Build works** - PyInstaller + Electron system is production-ready

---

**Last Updated**: March 10, 2026
**Repository**: https://github.com/Anthony5265/Windows-AI
**License**: MIT

---

## Quick Reference Commands

```bash
# Development
pytest -m unit                          # Run unit tests
pytest -m critical                      # Run critical tests
python -m windows_ai interactive       # Start CLI
npm run start:backend                  # Start backend API

# Building
python build_exe.py                    # Build Python executable
cd apps/gui && npm run build          # Build Electron app
npm run build:gui                      # Build GUI from root

# Git workflow
git checkout -b claude/feature-xyz123  # Create feature branch
git commit -m "feat: description"      # Conventional commit
git push -u origin claude/feature-xyz  # Push with tracking

# Configuration
export WINDOWSAI_SERVER__PORT=8080     # Override config
python -c "from windows_ai.config.unified_config import get_config; print(get_config())"
```

---

## Agent Compliance Rules

> **⚠️ MANDATORY — These rules apply to every Claude Code session working on this repository.**

1. **Read `ROADMAP.md` and `BLUEPRINT.md` first.** Before making any code changes, read both files in full. They are the single sources of truth for project status, architecture, and priorities.

2. **Follow the phased roadmap.** Work must follow the phase order (Phase 1 → 2 → 3 → 4). Do not skip ahead unless the user explicitly requests it.

3. **Update documentation.** When completing roadmap items, mark them `[x]` in `ROADMAP.md`. When adding new features, add them to the appropriate phase first.

4. **This file defers to ROADMAP.md and BLUEPRINT.md.** If anything in this `CLAUDE.md` file contradicts `ROADMAP.md` or `BLUEPRINT.md`, those files take precedence. Update this file to match.

5. **Verify before claiming.** Always check actual file contents (line counts, real code vs. stubs) before asserting implementation status. Use `find`, `wc -l`, or read files directly.

6. **Use correct plugin paths.** Plugins are at `windows_ai/plugins/builtin/{category}/`. Never reference `windows_ai/plugins/audio_ai/`, `vision_ai/`, or `code_ai/` — those paths do not exist.

---

*This guide is maintained to help AI assistants work effectively with the Windows AI codebase. Keep it updated as the project evolves.*

**Last Updated:** March 10, 2026  
**Authoritative documents:** `ROADMAP.md` (roadmap) · `BLUEPRINT.md` (architecture)
