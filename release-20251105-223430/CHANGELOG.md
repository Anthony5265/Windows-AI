# Changelog

All notable changes to Windows AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
