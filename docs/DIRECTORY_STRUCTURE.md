# Windows AI - Directory Structure

This document provides a comprehensive overview of the Windows AI repository structure, explaining the purpose and contents of each major directory.

> Looking for the newest catalog? Start with the [Repository Map](structure/overview.md) and the generated
> [manifest](structure/manifest.json) to see where every folder and file lives. The [`generate_repo_manifest.py`](../scripts/generate_repo_manifest.py)
> helper keeps those resources in sync with the latest code layout.

**Last Updated:** November 9, 2025

---

## Root Directory Files

### Core Documentation (Keep Minimal)
- `README.md` - Main project documentation and quick start guide
- `CHANGELOG.md` - Version history and release notes
- `CONTRIBUTING.md` - Contribution guidelines for developers
- `SECURITY.md` - Security policy and vulnerability reporting
- `GETTING_STARTED.md` - Detailed setup and usage instructions
- `BUILD_WINDOWS_INSTALLER.md` - Instructions for building Windows installer
- `LICENSE` - Project license (MIT)

### Configuration Files
- `package.json`, `package-lock.json` - Node.js dependencies and workspace configuration
- `requirements.txt`, `requirements.lock` - Python dependencies
- `pytest.ini` - Python test configuration
- `commitlint.config.js` - Commit message linting
- `Dockerfile` - Container configuration
- `.gitignore` - Git ignore patterns
- `.gitleaks.toml` - Secret scanning configuration
- `.pre-commit-config.yaml` - Pre-commit hooks
- `.editorconfig` - Editor configuration
- `backend_bundle_simple.spec` - PyInstaller spec file

### Launch Scripts (Essential Only)
- `start-all.{sh,bat}` - Start all components (backend + GUI + tray)
- `start-backend.{sh,bat}` - Start FastAPI backend only
- `start-gui.{sh,bat}` - Start Electron chat GUI only
- `start-tray.{sh,bat}` - Start system tray app only
- `build-release.sh` - Build release packages (Linux/Mac)
- `build-complete-installer.bat` - Build complete Windows installer
- `build_installer.ps1` - PowerShell installer builder

### Build Artifacts
- `release-20251105-223624/` - Latest release build (kept for reference)
- `nssm-2.24/`, `nssm-2.24.zip` - NSSM (Non-Sucking Service Manager) for Windows service installation

---

## Core Application Directories

### `windows_ai/` - Python Backend (FastAPI)
**Primary backend application with 2,600+ lines of Python code**

Main modules:
- `main.py` - FastAPI application entry point (72+ endpoints)
- `scheduler.py` - Task scheduling and automation
- `folder_watcher.py` - Directory monitoring for automation
- `system_info.py` - System metrics and monitoring
- `task_manager.py` - Background task management
- `agents.py` - AI agent orchestration
- `explorer.py` - File system exploration
- `sso.py` - Single sign-on integration
- `policy.py` - Policy management
- `integrations.py` - External service integrations

Subdirectories:
- `plugins/` - Plugin loading and management
- `iot/` - IoT device integration
- `system/` - System-level operations
- `vector_db/` - Vector database integrations (Milvus, Pinecone, Chroma, Weaviate)
- `rag/` - Retrieval Augmented Generation
- `workflow/` - Workflow engine

### `windows-ai-agent/` - Node.js Agent Service
**Agent orchestration service**

Key files:
- Service management and coordination
- Plugin architecture support
- Inter-process communication with other components

### `windows-ai-tray/` - System Tray Application
**Electron-based system tray app**

Features:
- Quick command window (Ctrl+Shift+Space)
- Desktop notifications
- Status monitoring
- Quick actions menu
- System tray integration

### `apps/` - Node.js Applications
**Collection of Node.js applications and services**

Subdirectories:
- `actions/` - Action handlers
- `actions-api/` - Actions REST API
- `agenthub/` - Agent hub service
- `common/` - Shared utilities
- `gui/` - GUI components (likely deprecated in favor of root gui/)
- `mobile/` - Mobile app components
- `proxy/` - API proxy service

---

## Feature Directories

### `plugins/` - Plugin System
**Extensible plugin architecture**

Categories:
- `ai_models/` - AI model plugins (2,600+ AI provider templates)
- `browsers/` - Browser automation plugins
- `datascience/` - Data science tools
- `devops/` - DevOps integrations
- `local_models/` - Local AI model support
- `swarm_generated/` - AI-generated plugins
- `testing/` - Testing utilities
- `windows/` - Windows-specific plugins

Built-in plugins (6 active):
- Web Search (DuckDuckGo)
- File Organizer
- System Info
- GitHub Integration
- Code Executor
- Calendar

### `automation/` - Automation Engine
**Automated task management**

Components:
- `builder.py` - Automation workflow builder
- `continuous_fix_bot.py` - Automated fix bot
- Folder watchers
- Scheduled tasks
- Web UI for automation management

### `gui/` - Main Chat GUI
**Electron-based chat interface**

Features:
- Modern chat interface with light/dark themes
- Real-time streaming AI responses
- Conversation history
- Multi-model support
- Settings panel
- Quick action buttons

### `control_center/` - Control Center
**Central management and coordination**

Components:
- `chat_ui.py` - Chat interface backend
- `backends.py` - Backend management
- Configuration management
- Service coordination

---

## Integration Directories

### `iot/` - Internet of Things
**IoT device integration**

Components:
- `device_manager.py` - Device discovery and management
- `mqtt_client.py` - MQTT protocol support
- `automation.py` - IoT automation rules
- `adapters/` - Device-specific adapters

### `mesh/` - Mesh Networking
**Local network mesh capabilities**

Components:
- `hub.py` - Mesh hub coordinator
- `node.py` - Mesh node implementation
- Peer discovery and communication
- Distributed AI processing

### `cloud_sync/` - Cloud Synchronization
**Cloud backup and sync**

Components:
- `provider.py` - Cloud provider abstraction
- Sync engine
- Conflict resolution

### `mobile/` - Mobile Companion
**Mobile app integration**

Features:
- Mobile companion app
- Remote control
- Notifications
- Sync with desktop

---

## Development Directories

### `tests/` - Test Suite
**Comprehensive testing infrastructure**

Structure:
- Unit tests for core components
- Integration tests
- Plugin tests (in `tests/plugins/`)
- Installer tests
- End-to-end tests

Current status: 3 of 12 tests passing (many need AI provider API keys)

### `scripts/` - Utility Scripts
**Development and build scripts**

Subdirectories:
- `utilities/` - General utilities (15 PowerShell scripts)
- `automation/` - Automation helpers

### `installer/` - Installation System
**Multi-platform installer**

Components:
- Windows installer (PowerShell)
- Linux/Mac installer (Shell)
- NSIS/WiX configurations
- Post-install scripts
- Uninstaller

### `codex/` - Task Management
**Development task tracking**

Contents:
- Task history
- Orchestrator prompts
- Development documentation

---

## Documentation Directories

### `docs/` - Documentation
**All project documentation (50+ files)**

Structure:
- `history/` - Session reports and progress logs (25 files)
- `roadmap-archive/` - Historical roadmap versions
- `reference/` - CLI syntax, release notes
- `cleanup-reports/` - Repository cleanup documentation
- `audit/` - Audit reports
- `project-core/` - Core project documentation
- `ROADMAP.md` - Current project roadmap (89KB)
- Feature documentation (IoT, mesh, XR, etc.)
- Architecture documentation
- API reference

### `specs/` - Specifications
**Technical specifications**

Contents:
- Feature specifications
- API specifications
- Protocol definitions

### `openapi/` - API Specifications
**OpenAPI/Swagger specs**

Contents:
- REST API definitions
- API documentation
- Client generation specs

---

## Advanced Feature Directories

### `domains/` - Domain Logic
**Domain-specific business logic**

Components:
- `audio_processing.py` - Audio/speech processing
- `computer_vision.py` - Image/video processing
- Domain-specific AI models
- Business rule engines

### `sdk/` - Software Development Kit
**Extension development SDK**

Components:
- Plugin development templates
- API clients
- Helper libraries
- Documentation

### `marketplace/` - Plugin Marketplace
**Plugin discovery and distribution**

Features:
- Plugin browsing
- Plugin installation
- Rating and reviews
- Update management

### `xr/` - Extended Reality
**AR/VR/MR support**

Features:
- Spatial computing
- 3D visualization
- Immersive interfaces

### `eco/` - Eco Computing
**Energy efficiency and monitoring**

Components:
- `monitor.py` - Energy usage monitoring
- `reports.py` - Efficiency reporting
- Optimization recommendations

### `search/` - Universal Search
**Advanced search capabilities**

Features:
- File search
- Semantic search
- Cross-application search

### `terminal/` - Terminal Integration
**Terminal/CLI integration**

Features:
- Command-line interface
- Shell integration
- Terminal-based UI

---

## Support Directories

### `config/` - Configuration
**Service configuration files**

Contents:
- `defaults.json` - Default configuration
- `fix_bot.json` - Fix bot configuration
- `pr_fix_bot.json` - PR fix bot configuration
- Service-specific configs

### `assets/` - Static Assets
**Media and static files**

Structure:
- `terminal/` - Terminal assets
- `videos/` - Demo videos
- `workflows/` - Workflow definitions
- Images, icons, etc.

### `backends/` - Backend Implementations
**Alternative backend implementations**

Contents:
- Backend service variants
- Protocol adapters

### `context_menu/` - Context Menu
**Windows Explorer integration**

Components:
- `handler.py` - Context menu handler
- `install.ps1` - Installation script
- Registry files for Windows integration

### `first-run-wizard/` - Setup Wizard
**Initial setup experience**

Components:
- Welcome screens
- Configuration wizard
- Quick setup
- Tutorial

### `wizard/` - Configuration Wizards
**Interactive configuration tools**

Features:
- Setup wizards
- Guided configuration
- Best practice recommendations

---

## Archive Directories

### `archive/` - Archived Content
**Historical and experimental code**

Structure:
- `orchestrators/` - Old batch generation scripts (11 PowerShell files)
- `deployment/` - Old deployment scripts (6 batch files)
- `extension-generation/` - Extension generation attempts (~6 MB)
  - `extensions_parallel/` - 152 parallel-generated extensions
  - `extensions_supervised/` - 20 supervised extensions
  - `extensions_copilot_swarm/` - 26 swarm-generated extensions
  - `extensions_output/` - 1 output extension

**Purpose:** Preserved for reference but not actively used. Can be deleted after 30-day review period.

### `proposed-patches/` - Proposed Changes
**Experimental patches and features**

Contents:
- Proof-of-concept implementations
- Experimental features
- Pending patches

---

## Miscellaneous Directories

### `agents/` - Agent Definitions
**AI agent configurations**

Contents:
- Agent templates
- Agent configurations
- Agent behaviors

### `model_discovery/` - Model Discovery
**AI model detection and management**

Features:
- Local model detection
- Model registry
- Model compatibility checking

### `optimization/` - Performance Optimization
**Performance tuning**

Components:
- `profiling.py` - Performance profiling
- `tuning.py` - Auto-tuning
- Optimization strategies

### `performance/` - Performance Monitoring
**Runtime performance analysis**

Features:
- Metrics collection
- Performance dashboards
- Bottleneck detection

### `security/` - Security Features
**Security hardening**

Components:
- Authentication
- Authorization
- Encryption
- Audit logging

### `snapshot/` - State Snapshots
**System state management**

Features:
- Configuration snapshots
- State backups
- Rollback support

### `ui/` - UI Components
**Reusable UI components**

Contents:
- Shared UI widgets
- Style definitions
- UI utilities

### `updater/` - Auto-Update
**Application update mechanism**

Features:
- Update checking
- Download management
- Installation
- Rollback

### `workflows/` - Workflow Definitions
**Predefined workflows**

Contents:
- Workflow templates
- Common automation patterns
- Workflow examples

---

## Organization Principles

### Root Directory Rules
1. **Keep minimal** - Only essential documentation and launch scripts
2. **No session logs** - All progress reports in `docs/history/`
3. **No temporary files** - Use `.gitignore` patterns
4. **No build artifacts** - Except one reference release

### Documentation Rules
1. **All docs in `docs/`** - Except 6-7 core root files
2. **History in `docs/history/`** - Session reports, progress logs
3. **Archive old versions** - Keep in `docs/*-archive/`
4. **One canonical roadmap** - `docs/ROADMAP.md`

### Code Organization Rules
1. **Python in `windows_ai/`** - Main backend application
2. **Node.js in `apps/` or named dirs** - Separate services
3. **Tests in `tests/`** - Mirror source structure
4. **Scripts in `scripts/`** - Organized by purpose

### Asset Management Rules
1. **Static assets in `assets/`** - Images, videos, etc.
2. **Binary tools documented** - Download instructions for large binaries
3. **Build artifacts ignored** - Except reference releases
4. **No large binaries in git** - Use external hosting when possible

---

## Quick Reference

### Finding Specific Functionality

| What I'm Looking For | Directory |
|----------------------|-----------|
| Backend API code | `windows_ai/main.py` |
| Chat GUI | `gui/` or `windows-ai-tray/` |
| Plugin development | `plugins/`, `sdk/` |
| Tests | `tests/` |
| Installation | `install/`, `installer/` |
| Documentation | `docs/` |
| Build scripts | Root `build-*.{sh,bat,ps1}` |
| Automation setup | `automation/` |
| IoT integration | `iot/` |
| Mesh networking | `mesh/` |
| Mobile app | `mobile/` |
| AI model plugins | `plugins/ai_models/` |

### File Count by Category

| Category | Directories | Approx Files |
|----------|-------------|--------------|
| Python Code | 15 | 500+ |
| Node.js Code | 10 | 200+ |
| Tests | 1 | 100+ |
| Documentation | 1 | 60+ |
| Plugins | 1 | 400+ |
| Scripts | 2 | 30+ |
| Configuration | 3 | 50+ |
| Archives | 1 | 2,000+ |

---

## Maintenance Guidelines

### Adding New Code
- **Python backend** → `windows_ai/`
- **Node.js service** → `apps/` or new named directory
- **Plugin** → `plugins/[category]/`
- **Test** → `tests/` (mirror source structure)

### Adding Documentation
- **User docs** → `docs/`
- **API docs** → `docs/reference/api/overview.md` or `openapi/`
- **Session reports** → `docs/history/`
- **Architecture** → `docs/architecture_overview.md`

### Adding Scripts
- **Build scripts** → Keep in root (if essential) or `scripts/`
- **Utility scripts** → `scripts/utilities/`
- **Automation** → `scripts/automation/`

### Cleanup Checklist
- [ ] Remove temporary files before commit
- [ ] Don't commit build artifacts (except reference release)
- [ ] Don't commit session logs to root
- [ ] Update documentation when structure changes
- [ ] Keep root directory minimal

---

## Future Improvements

### Planned Structure Changes
1. Consolidate `gui/` and `windows-ai-tray/` if overlapping
2. Consider merging `apps/gui/` with root `gui/`
3. Review and potentially remove `proposed-patches/` after 30 days
4. Delete `archive/` contents after 30-day review period
5. Create unified `extensions/` when properly implemented

### Documentation Improvements
1. Add per-directory README.md files
2. Create architecture diagrams
3. Document inter-component communication
4. Add developer onboarding guide

---

**Note:** This structure reflects the repository state after the comprehensive cleanup completed on November 9, 2025. The organization follows best practices for maintainability, clarity, and developer productivity.

For questions or suggestions about repository organization, please see `CONTRIBUTING.md`.
