# Repository Organization Plan

## Current Issues Identified

1. **Root Directory Clutter**: 59 files at root level (should be <10)
2. **Duplicate Directories**: Multiple overlapping purposes
3. **Scattered Documentation**: 10+ markdown files at root
4. **Mixed Concerns**: Build scripts, config files, documentation all mixed
5. **No Clear Navigation**: No index or architecture documentation

## Target Structure

```
Windows-AI/
├── .github/                    # GitHub-specific files (workflows, templates)
├── .vscode/                    # VS Code settings
├── .devcontainer/              # Dev container config
│
├── docs/                       # ALL documentation (centralized)
│   ├── README.md               # Documentation index
│   ├── getting-started/        # User onboarding
│   ├── architecture/           # System design docs
│   ├── api/                    # API documentation
│   ├── deployment/             # Deployment guides
│   ├── security/               # Security documentation
│   ├── development/            # Developer guides
│   └── analysis/               # Analysis reports
│
├── src/                        # Source code (organized by purpose)
│   ├── windows_ai/             # Main Python package
│   │   ├── core/               # Core functionality
│   │   ├── plugins/            # Plugin system
│   │   │   └── builtin/        # Built-in plugins (6,450 files)
│   │   ├── services/           # Business logic services
│   │   ├── api/                # API layer
│   │   └── utils/              # Utilities
│   │
│   ├── gui/                    # GUI applications
│   │   ├── desktop/            # Desktop GUI (Electron/Qt)
│   │   ├── tray/               # System tray application
│   │   └── wizard/             # First-run wizard
│   │
│   ├── cli/                    # Command-line interfaces
│   ├── agents/                 # AI agent implementations
│   ├── iot/                    # IoT integrations
│   ├── mobile/                 # Mobile apps
│   └── xr/                     # XR/VR interfaces
│
├── scripts/                    # Development & deployment scripts
│   ├── build/                  # Build scripts
│   ├── deploy/                 # Deployment scripts
│   ├── dev/                    # Development utilities
│   ├── generators/             # Code generators
│   ├── automation/             # Automation scripts
│   └── ci/                     # CI/CD scripts
│
├── tests/                      # Test suites (mirrors src/ structure)
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── performance/
│
├── config/                     # Configuration files
│   ├── development/
│   ├── production/
│   └── templates/
│
├── assets/                     # Static assets
│   ├── images/
│   ├── icons/
│   ├── fonts/
│   └── themes/
│
├── build/                      # Build artifacts & installers
│   ├── installers/             # Installer files
│   ├── packages/               # Built packages
│   └── dist/                   # Distribution files
│
├── tools/                      # Development tools
│   ├── sdk/                    # SDK tools
│   ├── cli-tools/              # Command-line tools
│   └── utilities/              # Utility tools
│
├── examples/                   # Example code & demos
│   ├── plugins/
│   ├── integrations/
│   └── tutorials/
│
├── vendor/                     # Third-party dependencies
│   └── nssm-2.24/              # Windows service manager
│
├── .archive/                   # Deprecated/archived code
│
├── README.md                   # Main project readme
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # Contribution guidelines
├── LICENSE                     # License file
├── SECURITY.md                 # Security policy
├── requirements.txt            # Python dependencies
├── package.json                # Node.js dependencies
├── setup.py                    # Python package setup
└── pyproject.toml              # Modern Python config
```

## Organization Strategy

### Phase 1: Documentation Consolidation
Move all .md files from root → docs/ with proper categorization:
- Getting started guides → docs/getting-started/
- Architecture docs → docs/architecture/
- Analysis reports → docs/analysis/
- Deployment guides → docs/deployment/
- Security docs → docs/security/

### Phase 2: Source Code Organization
- Keep windows_ai/ as main package
- Move gui/, ui/, windows-ai-tray/ → src/gui/
- Move agents/, agenthub/ → src/agents/
- Move iot/ → src/iot/
- Move mobile/ → src/mobile/
- Move xr/ → src/xr/

### Phase 3: Scripts Consolidation
Merge scripts/, automation/, tools/ with proper categorization:
- Generator scripts → scripts/generators/
- Build scripts → scripts/build/
- CI scripts → scripts/ci/
- Dev utilities → scripts/dev/
- Deployment → scripts/deploy/

### Phase 4: Build & Installer Organization
- installer/ → build/installers/
- Merge install/ + installer/ content
- Add proper README to build/

### Phase 5: Configuration Cleanup
- Centralize config files → config/
- Create templates for different environments
- Document configuration options

### Phase 6: Assets & Resources
- Organize assets/ with clear subdirectories
- Add README explaining asset organization

### Phase 7: Clean Root Directory
Keep only essential files at root:
- README.md
- CHANGELOG.md
- CONTRIBUTING.md
- LICENSE
- SECURITY.md
- requirements.txt
- package.json
- pyproject.toml
- setup.py
- .gitignore
- .gitattributes
- .editorconfig

### Phase 8: Add Navigation & Documentation
- Create README.md in every directory
- Create docs/README.md as documentation hub
- Create ARCHITECTURE.md explaining structure
- Add INDEX.md files where needed

## Benefits

1. **Reduced Root Clutter**: From 59 files → ~12 essential files
2. **Clear Organization**: Purpose-based directory structure
3. **Easy Navigation**: README in every directory
4. **Professional Structure**: Follows industry best practices
5. **Scalable**: Easy to add new components
6. **Discoverable**: Clear paths to all resources

## Execution Order

1. Create new directory structure
2. Move documentation files
3. Move source code
4. Consolidate scripts
5. Organize build artifacts
6. Clean configuration
7. Archive deprecated code
8. Add navigation files
9. Update all paths in code
10. Test and verify
11. Commit changes
