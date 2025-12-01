# Source Code Directory

This directory contains all source code for the Windows AI project, organized by component and purpose.

## Directory Structure

### Core Package
**`windows_ai/`** - Main Python package (monorepo)
- `core/` - Core functionality and utilities
- `plugins/` - Plugin system and 6,450+ built-in plugins
- `services/` - Business logic and service layer
- `api/` - API endpoints and interfaces
- `utils/` - Shared utilities and helpers

### User Interfaces
**`gui/`** - Graphical user interfaces
- `desktop/` - Main desktop GUI application
- `tray/` - System tray application
- `wizard/` - First-run setup wizard
- `control_center/` - Control center interface

**`cli/`** - Command-line interfaces
- `terminal/` - Terminal integration
- Command-line tools and utilities

### AI Components
**`agents/`** - AI agent implementations
- Agent orchestration
- Multi-agent systems
- Agent frameworks

### Platform Integrations
**`iot/`** - Internet of Things integrations
- Smart home device adapters
- IoT protocols (MQTT, Zigbee, Matter, etc.)
- Device management

**`mobile/`** - Mobile applications
- Android app
- iOS app
- React Native components

**`xr/`** - Extended Reality (VR/AR)
- VR interfaces
- AR components
- Spatial computing

### Core Services
**`services/`** - Backend services
- `cloud_sync/` - Cloud synchronization
- `updater/` - Auto-update system
- `update-server/` - Update server
- `snapshot/` - System snapshot service
- `model_discovery/` - AI model discovery

### Business Logic
**`domains/`** - Domain-specific logic
**`backends/`** - Backend implementations
**`automation/`** - Automation workflows
**`workflows/`** - Workflow engine

### Infrastructure
**`search/`** - Search functionality
**`codex/`** - Code analysis and generation
**`marketplace/`** - Plugin marketplace
**`mesh/`** - Distributed computing mesh
**`eco/`** - Ecosystem management
**`security/`** - Security components
**`optimization/`** - Performance optimization
**`performance/`** - Performance monitoring

### Integrations
**`integrations/`** - External integrations
- `context_menu/` - Windows context menu integration
- Other platform integrations

### Applications
**`apps/`** - Standalone applications built on Windows AI

## Development Guidelines

### Adding New Components

1. **Choose the Right Location:**
   - Core functionality → `windows_ai/core/`
   - New plugin → `windows_ai/plugins/builtin/`
   - UI component → `gui/` or `cli/`
   - Service → `services/`
   - Agent → `agents/`

2. **Follow Structure:**
   ```
   component/
   ├── __init__.py
   ├── README.md
   ├── module.py
   └── tests/
   ```

3. **Include Documentation:**
   - Add README.md in new directories
   - Document all public APIs
   - Include usage examples

### Code Organization Principles

1. **Separation of Concerns:** Each directory has a single, clear purpose
2. **Low Coupling:** Minimize dependencies between components
3. **High Cohesion:** Related functionality stays together
4. **Testability:** All components should be unit testable
5. **Reusability:** Shared code goes in `utils/` or `core/`

### Import Conventions

```python
# Core imports
from windows_ai.core import CoreComponent

# Service imports
from windows_ai.services.cloud_sync import SyncManager

# Plugin imports
from windows_ai.plugins.base import IntegrationPlugin

# Utility imports
from windows_ai.utils.helpers import helper_function
```

## Testing

Tests for each component should be in the main `tests/` directory at the repository root, mirroring the source structure:

```
tests/
├── unit/
│   ├── windows_ai/
│   ├── gui/
│   └── agents/
├── integration/
└── e2e/
```

## Building

Most components are built as part of the main package:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Build package
python setup.py build

# Install in development mode
pip install -e .
```

## Dependencies

- **Python:** 3.8+
- **Node.js:** 16+ (for GUI components)
- **Platform:** Windows 10/11 (primary), Linux (partial support)

See `requirements.txt` for Python dependencies.

## Architecture Notes

### Plugin System
The plugin system (`windows_ai/plugins/`) is the heart of Windows AI:
- 6,450+ built-in plugins
- 35+ integration categories
- Production-ready with real API implementations
- See [Plugin Architecture](../docs/architecture/plugins.md)

### Service Layer
Services provide shared functionality across components:
- Cloud synchronization
- Auto-updates
- Model discovery
- Snapshot management

### Agent Framework
The agent system enables autonomous AI operations:
- Multi-agent orchestration
- Tool use and function calling
- Long-running tasks
- Agent communication

## Performance Considerations

- Plugin lazy-loading for faster startup
- Async/await patterns throughout
- Connection pooling for API calls
- Caching strategies for expensive operations

## Security

- All API keys use environment variables
- No hardcoded secrets
- Input validation on all boundaries
- Secure credential storage
- See [Security Documentation](../docs/security/)

## Contributing

See the main [Contributing Guide](../CONTRIBUTING.md) for:
- Code style guidelines
- PR process
- Review requirements
- Testing requirements

---

**Component Count:** 20+ major components
**Plugin Count:** 6,450+ built-in plugins
**Languages:** Python, TypeScript/JavaScript, PowerShell
**Platform:** Windows-first, cross-platform capable
