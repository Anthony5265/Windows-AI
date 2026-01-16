# Config Consolidation Mapping and Migration Guide
# Windows AI Unified Configuration System

## Project Config Files Identified (23+ files)

### Already in config/ directory:
1. config/.pre-commit-config.yaml
2. config/defaults.json
3. config/fix_bot.json
4. config/pr_fix_bot.json
5. config/project-metadata.json
6. config/proxy.yaml
7. config/pytest.ini
8. config/search.yaml

### Windows AI Config:
9. windows_ai/config/default.yaml

### Hidden Config Directories:
10. .claude/settings.json
11. .windows-ai/config.json
12. .windows-ai/scheduler.json
13. .windows-ai/watchers.json
14. .vscode/settings.json
15. .devcontainer/devcontainer.json

### Domain/Feature Configs:
16. agenthub/memory/redaction_rules.yaml
17. agenthub/monitoring/anomaly_rules.yaml
18. agenthub/workflow_router_rules.yaml
19. iot/device_profiles.yaml
20. model_discovery/policies/resource_quota.yaml
21. model_discovery/providers/open_source_curation.yaml
22. model_discovery/resolvers/compatibility_matrix.yaml
23. windows_ai/security/threat_monitor_rules.yaml

### Application Configs:
24. apps/gui/electron-builder.yml
25. install/signing/sign-config.json
26. update-server/manifest.json

## Migration Strategy

### Phase 1: Create Unified Config System (This Task)
- Create config/settings.py for programmatic access
- Create config/config.yaml for YAML-based configuration
- Map all existing configs to unified structure
- Document migration path

### Phase 2: Update Imports
- Update windows_ai modules to use unified config
- Update test fixtures to use unified config
- Update CLI tools to use unified config

### Phase 3: Deprecation
- Mark old config locations as deprecated
- Maintain backward compatibility
- Log warnings when old configs are accessed
- Plan full removal in next release

## Unified Config Structure

### config/settings.py
- Centralized Python configuration module
- Type hints for all settings
- Environment variable support
- Config validation
- Singleton pattern for global access

### config/config.yaml
- Main YAML configuration file
- Organized by feature/domain
- Comments explaining each section
- Environment variable interpolation

## Implementation Timeline

1. Create config/settings.py with unified interface
2. Create config/config.yaml as main config source
3. Update critical imports in:
   - windows_ai/main.py
   - windows_ai/__main__.py
   - windows_ai/api/server.py
   - tests/conftest.py
4. Test with existing test suite
5. Document migration in config/README.md
6. Create deprecation warnings in old config modules

## Current Status: IN PROGRESS
- settings.py: Created ✓
- config consolidation mapping: Complete ✓
- Import updates: Pending
- Migration documentation: Pending
