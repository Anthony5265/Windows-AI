# Changelog

All notable changes to Windows AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- API key authentication for remote access
- Chat history encryption at rest
- Plugin sandboxing
- Rate limiting on API endpoints
- Mobile companion app

## [0.5.0] - 2025-01-10

### Added
- **Phase 5: Installer Hardening & Production Readiness**
  - Complete production-ready NSIS installer with digital code signing support
  - Automated installer testing infrastructure with GitHub Actions
  - Rollback functionality with system restore point creation
  - Secure update verification with SHA256 checksums

- **Auto-Update System**
  - Complete auto-update implementation with frontend UI
  - Automatic update checking with configurable intervals (1h, 6h, 12h, 24h)
  - Download progress tracking with real-time updates
  - One-click update installation with automatic restart
  - Update notification system with changelog preview
  - Update preferences UI in settings (auto-check, auto-download, channel selection)
  - Support for stable/beta/alpha release channels
  - Background update checker service
  - Update API endpoints: status, check, download, install, preferences

- **Comprehensive Documentation Suite (40,000+ words)**
  - **QUICK_START.md**: 5-minute getting started guide
  - **USER_GUIDE.md**: Complete 15,000+ word feature guide covering all functionality
  - **FAQ.md**: 50+ frequently asked questions organized by topic
  - **PLUGIN_DEVELOPMENT.md**: Complete plugin development guide with 3 working examples
  - **TROUBLESHOOTING.md**: Systematic problem-solving guide for all issue types
  - **API_REFERENCE.md**: Complete HTTP API documentation with examples in Python and PowerShell
  - **SECURITY.md**: Enhanced security policy with best practices and reporting procedures

- **Enhanced OpenAPI/Swagger Documentation**
  - Organized endpoints with tags (health, chat, automation, plugins, models, updates, config, websocket)
  - Detailed request/response examples in JSON
  - Interactive Swagger UI at http://localhost:8010/docs
  - ReDoc alternative interface at http://localhost:8010/redoc
  - Complete API metadata with contact info and license
  - Enhanced docstrings for all endpoints with prerequisites and warnings

- **Portable Build System**
  - Complete portable ZIP distribution with embedded Python and Node.js runtimes
  - No installation required - runs from any folder
  - Batch and PowerShell launcher scripts
  - Portable mode with self-contained data storage
  - USB drive compatible
  - Automated build script (build-portable.ps1)
  - Portable-specific README with usage instructions

- **Update Server Infrastructure**
  - Production-ready FastAPI update server
  - Manifest-based update distribution system
  - Version comparison and update checking
  - Secure downloads with checksum verification
  - Docker deployment support
  - CDN-ready architecture
  - Statistics and monitoring endpoints

### Changed
- Updated installer to v0.5.0 with hardened security
- Improved backend version management (now 0.5.0)
- Enhanced error handling throughout the application
- Better memory management in installer
- Improved update notification UX with slide-in animations

### Fixed
- Installer memory leak issues
- Service startup race conditions
- Configuration migration bugs
- Update client callback error handling

### Security
- Added Authenticode code signing support for all installers
- Implemented secure update verification with SHA256 checksums
- Enhanced input validation across all API endpoints
- Improved path traversal protection in file operations
- Secure update server with HTTPS support
- Update manifest signature verification

### Documentation
- Created 6 comprehensive user-facing documentation files
- Enhanced API documentation with OpenAPI/Swagger
- Added security policy and vulnerability reporting guide
- Created portable build documentation
- Updated deployment guides for update server

## [0.2.0] - 2025-11-06

### Added
- **Windows Executable Release**: Professional NSIS installer for x64 and ia32 architectures
- **Portable Version**: Standalone executable requiring no installation
- **Application Icons**: Custom gradient icon with "W" branding in multiple sizes (.ico, .png)
- **Release Build Script**: Automated `build-release.sh` for complete release packaging
- **Release Documentation**: Comprehensive RELEASE_NOTES.md and RELEASE_README.md
- **Enhanced Package Scripts**: Added build:gui, build:icons, build:release, test:python scripts
- **Icon Generator**: Python script (`scripts/create_icon.py`) for automated icon creation
- **Version Bump**: Updated to v0.2.0 across all package.json files

### Fixed
- **AgentHub Import Error**: Added missing `Iterable` import from typing module (apps/agenthub/main.py:2)
- **AgentHub Duplicate Methods**: Removed duplicate `deregister()` and `list_agents()` method definitions (apps/agenthub/main.py:53-60)
- **AgentHub Missing Attributes**: Added `_last_train` and `_last_run` dictionaries to `__init__` (apps/agenthub/main.py:34-35)
- **AgentHub Missing Class**: Added `CollaborationProtocol` base class definition (apps/agenthub/main.py:23-25)
- **AgentHub Missing Constant**: Added `MARKETPLACE_URL` environment variable (apps/agenthub/main.py:88-90)
- **Deprecated Locale Function**: Replaced `locale.getdefaultlocale()` with `locale.getlocale()` in installer/locales/__init__.py (line 17)
- **TypeScript Compilation**: Fixed actions-api build by installing @types/node dependency

### Improved
- **Electron Builder Configuration**: Complete electron-builder.yml with NSIS and portable targets
- **Repository Metadata**: Added description and repository URL to package.json
- **GUI Package Metadata**: Added author, description, and main entry point to apps/gui/package.json
- **Build System**: Comprehensive build scripts for icons, GUI, and complete releases
- **Error Handling**: Better try-catch for locale detection with fallback to "en"

### Documentation
- Created RELEASE_NOTES.md with complete feature list and migration guide
- Created RELEASE_README.md for end-user distribution package
- Updated package.json with repository information and improved scripts
- Enhanced inline code comments and documentation

### Technical
- Upgraded version from 0.1.0 to 0.2.0
- Icon system: 256x256 PNG and multi-size ICO (256, 128, 64, 48, 32, 16)
- Build targets: NSIS installer (x64, ia32) and portable executable (x64)
- Test suite: 172 tests with improved exclusion of GUI-dependent tests
- TypeScript compilation: Successfully building actions-api without errors

## [0.1.0] - 2025-08-07 — Phase 1 scaffolding

### Added
- Initial project scaffolding
- windows-ai-agent with CLI and plugins
- System tray application scaffold
- CI workflow windows-ai-agent-ci.yml
- README.windows-ai.md documentation
- FastAPI backend with chat, automation, and plugin support
- Electron GUI with chat interface
- LiteLLM integration for multi-model AI support
- Folder watchers and task scheduler
- 6 built-in plugins (web search, file organizer, system info, GitHub, code executor, calendar)
- System tray with global hotkey support
- Conversation history persistence
- WebSocket and SSE streaming support

[0.2.0]: https://github.com/Anthony5265/Windows-AI/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Anthony5265/Windows-AI/releases/tag/v0.1.0
