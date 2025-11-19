# Scripts Directory

This directory contains all development, build, deployment, and utility scripts for the Windows AI project.

## Directory Structure

### 🏗️ Build Scripts
**`build/`** - Scripts for building the project
- `build-release.sh` - Build production release
- `build-portable.ps1` - Build portable version
- `build_installer.ps1` - Build Windows installer
- `*.spec` - PyInstaller specifications
- `build-artifacts.js` - Artifact generation

**Usage:**
```bash
# Build release version
./build/build-release.sh

# Build Windows installer
powershell ./build/build_installer.ps1
```

### 🚀 Deployment Scripts
**`deploy/`** - Deployment and distribution scripts
- Deployment automation
- Release publishing
- Update management

### 🧪 Development Scripts
**`dev/`** - Development utilities
- `start-all.sh/bat` - Start all services
- `start-backend.sh/bat` - Start backend only
- `start-gui.sh/bat` - Start GUI only
- `start-tray.sh/bat` - Start system tray
- `start-watchdog.sh/bat` - Start watchdog process
- `watchdog.py` - Process monitoring
- `plugin_agent.py` - Plugin development agent
- `lint.js` - Code linting
- Development environment setup

**Usage:**
```bash
# Start all components
./dev/start-all.sh

# Start backend only
./dev/start-backend.sh
```

### ⚙️ Generators
**`generators/`** - Code generation scripts
- `generate_all_385_plugins.py` - Generate 385 core plugins
- `generate_production_plugins.py` - Generate production plugins
- `generate_plugin.py` - Plugin template generator
- `generate_local_models.py` - Local model integrations
- `generate_specialized_models.py` - Specialized AI models
- `generate_ai_providers.py` - AI provider integrations
- `generate_windows_integration.py` - Windows OS integration
- `generate_infrastructure.py` - Infrastructure code
- `generate_tier3.py` - Tier 3 components
- `complete_*.py` - Roadmap completion scripts
- `COMPLETE_*.py` - Mass plugin generation
- `batch_generate_all.py` - Batch generation
- `implement_roadmap.py` - Roadmap implementation
- `comprehensive_roadmap_implementation.py` - Full roadmap
- `wave2_tasks.py` - Wave 2 task generation
- `complete_missing.py` - Complete missing items
- `complete_roadmap.py` - Roadmap completion

**Usage:**
```bash
# Generate a new plugin
python generators/generate_plugin.py --name MyPlugin --type integration

# Generate all 385 plugins
python generators/generate_all_385_plugins.py

# Complete roadmap items
python generators/complete_roadmap.py
```

### 🤖 Automation
**`automation/`** - Automation workflows
- CI/CD automation
- Scheduled tasks
- Batch operations

### 🔧 Utilities
**`utilities/`** - Utility scripts
- `cleanup_phase1.py` - Repository cleanup
- `deep_repo_cleanup.py` - Deep cleanup
- `roadmap_tracker.py` - Track roadmap progress
- `check_batch.py` - Batch verification
- `create_icon.py` - Icon generation
- `Add-ChatGPTSessionLog.ps1` - Session logging
- General-purpose tools

**Usage:**
```bash
# Track roadmap progress
python utilities/roadmap_tracker.py

# Clean repository
python utilities/cleanup_phase1.py

# Generate icon
python utilities/create_icon.py
```

### 🔄 CI/CD
**`ci/`** - Continuous Integration scripts
- CI pipeline scripts
- Test runners
- Code quality checks

## Script Categories

### Build & Packaging
Build scripts create distributable packages:
- Windows installer (.exe)
- Portable version (.zip)
- MSI package
- PyInstaller bundles

### Code Generation
Generators automate code creation:
- Plugin scaffolding
- Model integrations
- Boilerplate code
- API clients

### Development
Dev scripts streamline development:
- Start/stop services
- Watch for changes
- Lint and format code
- Run tests locally

### Deployment
Deployment scripts handle releases:
- Version bumping
- Changelog generation
- Release notes
- Publishing to package managers

### Utilities
Utility scripts for maintenance:
- Repository cleanup
- Progress tracking
- Batch operations
- Data migration

## Common Tasks

### Starting Development
```bash
# 1. Set up environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 2. Install dependencies
pip install -r requirements-dev.txt

# 3. Start all services
./scripts/dev/start-all.sh
```

### Building for Release
```bash
# 1. Run tests
pytest

# 2. Build release
./scripts/build/build-release.sh

# 3. Create installer
powershell ./scripts/build/build_installer.ps1
```

### Generating Code
```bash
# Generate new plugin
python scripts/generators/generate_plugin.py \
  --name MyPlugin \
  --type integration \
  --api-base https://api.example.com

# Generate batch of plugins
python scripts/generators/batch_generate_all.py --count 100
```

### Cleanup Operations
```bash
# Clean build artifacts
python scripts/utilities/cleanup_phase1.py

# Deep repository cleanup
python scripts/utilities/deep_repo_cleanup.py --dry-run
```

## PowerShell Scripts

Windows-specific scripts use PowerShell:

```powershell
# Set execution policy (if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run PowerShell script
powershell -File scripts/build/build-portable.ps1

# With parameters
powershell -File scripts/dev/start-all.ps1 -Verbose
```

## Environment Variables

Scripts may require environment variables:

```bash
# Development
export WINDOWS_AI_ENV=development
export LOG_LEVEL=debug

# Production
export WINDOWS_AI_ENV=production
export API_KEY=your-key-here

# Build
export BUILD_VERSION=2.0.0
export SIGN_CERT=path/to/cert.pfx
```

## Adding New Scripts

### Guidelines

1. **Use Descriptive Names:**
   - ✅ `generate_plugin.py`
   - ❌ `gen.py`

2. **Add to Correct Directory:**
   - Build-related → `build/`
   - Generators → `generators/`
   - Dev tools → `dev/`
   - Utilities → `utilities/`

3. **Include Documentation:**
   ```python
   """
   Script: generate_plugin.py
   Purpose: Generate plugin scaffolding
   Usage: python generate_plugin.py --name PluginName
   """
   ```

4. **Add Shebang:**
   ```python
   #!/usr/bin/env python3
   ```

5. **Make Executable:**
   ```bash
   chmod +x script_name.py
   ```

### Script Template

```python
#!/usr/bin/env python3
"""
Script Name: my_script.py
Purpose: Brief description of what this script does
Author: Your Name
Date: 2025-11-19

Usage:
    python my_script.py [options]

Options:
    --help    Show this help message
    --verbose Enable verbose output

Examples:
    python my_script.py
    python my_script.py --verbose
"""

import argparse
import logging

def main():
    """Main script logic"""
    parser = argparse.ArgumentParser(description="Script description")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Your code here
    pass

if __name__ == "__main__":
    main()
```

## Testing Scripts

Test scripts before committing:

```bash
# Dry run (if supported)
python scripts/utilities/cleanup.py --dry-run

# Test in isolated environment
python -m venv test_env
source test_env/bin/activate
python scripts/your_script.py
```

## Troubleshooting

### Common Issues

**Script not found:**
```bash
# Ensure you're in repository root
cd /path/to/Windows-AI

# Use relative or absolute paths
python scripts/dev/start-all.py
```

**Permission denied:**
```bash
# Make script executable
chmod +x scripts/build/build-release.sh
```

**Module not found:**
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

**PowerShell execution policy:**
```powershell
# Set policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Script Maintenance

- **Review regularly** for outdated scripts
- **Archive unused** scripts to `.archive/`
- **Document changes** in script headers
- **Test after updates** to Python/Node versions
- **Keep dependencies** up to date

## Contributing

When contributing scripts:
1. Follow existing patterns
2. Add comprehensive documentation
3. Include usage examples
4. Test thoroughly
5. Update this README

See [Contributing Guide](../CONTRIBUTING.md) for details.

---

**Total Scripts:** 50+ scripts across all categories
**Languages:** Python, PowerShell, Bash, JavaScript
**Purpose:** Development, build, deployment, automation
