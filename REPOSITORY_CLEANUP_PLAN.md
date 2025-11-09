# Windows-AI Repository Cleanup Plan

**Date:** November 9, 2025
**Status:** Ready for Execution

---

## Executive Summary

### Current State
- **Total Size:** 31 MB (25.1 MB code + 5.9 MB .git)
- **Total Files:** ~5,500+ files
- **Issues Found:** Significant duplication, obsolete files, poor organization
- **Estimated Cleanup:** ~3.3 MB savings, ~2,280 files removed

### What's Working (Core Features) ✅
- Backend Server (FastAPI, 72+ endpoints)
- Chat GUI (Electron-based)
- System Tray App
- 6 Built-in Plugins (Calendar, Code Executor, File Organizer, GitHub, System Info, Web Search)
- Automation Engine (folder watchers, schedulers)
- Mesh Networking (tested & working)

### What Needs Implementation ⚠️
- Real AI provider implementations (2,600+ templates exist, need real APIs)
- IoT integrations (code exists, dependencies missing)
- Advanced AI features (RAG, memory systems, agents)
- Full test coverage (currently 3/12 passing)

---

## Cleanup Phases

### Phase 1: Delete Duplicate Release Directories
**Impact:** ~1 MB savings, 50 files removed

**Action:**
```bash
# Keep only the latest release, delete 5 older ones
rm -rf release-20251105-222352/
rm -rf release-20251105-222643/
rm -rf release-20251105-222924/
rm -rf release-20251105-223226/
rm -rf release-20251105-223430/
# Keep: release-20251105-223624/
```

**Reason:** 6 identical timestamped release builds from same day, only need latest

---

### Phase 2: Clean Up Plugins Directory
**Impact:** ~172 KB savings, 2,211 files removed/consolidated

#### 2A: Review Invalid Plugins
**Location:** `plugins/_invalid/` (2,104 files, 122 KB)

**Action:**
- Review if any can be salvaged
- Document what went wrong
- Delete unfixable files
- Create summary in `docs/plugin-cleanup-report.md`

#### 2B: Consolidate Duplicate Plugins
**Location:** `plugins/_duplicates/` (107 files)

**Action:**
- Keep best implementation of each
- Delete duplicates
- Update plugin catalog

---

### Phase 3: Consolidate Extension Directories
**Impact:** ~3-4 MB savings after deduplication

**Current State:**
- `extensions_parallel/` (780 KB, 152 extensions)
- `extensions_supervised/` (2.9 MB, 20 extensions)
- `extensions_copilot_swarm/` (2.2 MB, 26 extensions)
- `extensions_output/` (8.5 KB, 1 extension)

**Action:**
1. Create new unified `extensions/` directory
2. Merge non-duplicate extensions from all 4 directories
3. Create `extensions/README.md` documenting structure
4. Archive old generation attempts to `archive/extension-generation/`
5. Update any references in code

---

### Phase 4: Organize Root Directory Documentation
**Impact:** Clean root from 42 MD files to ~8 core files

#### 4A: Keep in Root (Core Documentation)
- README.md
- CHANGELOG.md
- CONTRIBUTING.md
- SECURITY.md
- LICENSE
- GETTING_STARTED.md
- BUILD_WINDOWS_INSTALLER.md
- PLAN.md (if current)

#### 4B: Move to `docs/history/` (Session Reports - 13 files)
- SESSION_SUMMARY_2025-11-09.md
- WORK_SESSION_2025-11-09.md
- COMPLETE_STATUS_REPORT.md
- FINAL_STATUS_REPORT.md
- DEVELOPMENT_SUMMARY.md
- PROGRESS_REPORT.md
- PHASE_1_COMPLETE.md
- PHASE_2_PROGRESS.md
- PHASE_2_START.md
- INTEGRATION_COMPLETE.md
- WAVE_4_DEPLOYMENT.md
- BATCH_PROCESSING_LOG.md
- AGENT_FAILURE_ANALYSIS.md

#### 4C: Consolidate to `docs/ROADMAP.md` (8 files → 1)
Current files:
- COMPLETE_ROADMAP_TO_100.md (77 KB) ← **Use as primary source**
- ULTIMATE_EXTENSION_ROADMAP.md (85 KB)
- FILTERED_EXTENSION_ROADMAP.md (80 KB)
- EXTENSION_ROADMAP.md
- REMAINING_ROADMAP.md
- ROADMAP_STATUS.md
- ROADMAP_COMPLETION_REPORT.md
- ACTUAL_ROADMAP_REALITY.md

**Action:**
1. Create consolidated `docs/ROADMAP.md` with current state
2. Move originals to `docs/roadmap-archive/`
3. Include realistic completion status (10-15% complete)

#### 4D: Move to `docs/history/` (Cleanup & Process Files - 7 files)
- COMPLETE_CLEANUP_INSTRUCTIONS.md
- BRANCHES_TO_DELETE.txt
- ok_branches.txt
- FIX_ALL_BRANCHES_INVESTIGATION.md
- COMPREHENSIVE_FIXES_SUMMARY.md
- FINAL_MERGE_SUMMARY.md

#### 4E: Move to `docs/history/` (PR & Git Files - 4 files)
- PR_BODY.md
- PR_REVIEW_REPORT.md
- PR_MERGE_ACTIONS_COMPLETED.md
- AUDIT_SUMMARY.md

#### 4F: Move to `docs/` (Reference Files - 3 files)
- CLI_SYNTAX_REFERENCE.md
- README.windows-ai.md
- RELEASE_README.md
- RELEASE_NOTES.md

---

### Phase 5: Clean Up and Organize Scripts

#### 5A: Consolidate Orchestrator Scripts (Root → archive)
**Current:** 11 orchestrator scripts in root (150+ KB)

**Action:** Move to `archive/orchestrators/`
- COPILOT_OLLAMA_SWARM.ps1
- FULL_SWARM_ORCHESTRATOR.ps1
- FULL_SWARM_ORCHESTRATOR_BACKUP.ps1 ← DUPLICATE
- FULL_SWARM_FIXED.ps1
- SWARM_ORCHESTRATOR_FIXED.ps1
- PARALLEL_ORCHESTRATOR_V2.ps1
- SUPERVISED_SWARM.ps1
- TERMINAL_SWARM.ps1
- mega_swarm_orchestrator.ps1
- orchestrator_master.ps1
- launch_copilot_swarm.ps1

**Reason:** These appear to be for batch extension generation (already complete)

#### 5B: Consolidate Deployment Scripts (Root → archive)
**Action:** Move to `archive/deployment/`
- FINAL_WAVE.bat
- QUAD_DEPLOY.bat
- TURBO_MODE.bat
- WAVE2_TURBO.bat
- RESTART_SWARM.bat
- MONITOR.bat

#### 5C: Organize Utility Scripts
**Action:** Move to `scripts/utilities/`
- SIMPLE_EXTENSION_GENERATOR.ps1
- EMERGENCY_CLEANUP.ps1
- ai_cli_organizer.ps1
- ai_enhancements.ps1
- command_templates.ps1
- decision_logger.ps1
- error_pattern_db.ps1
- session_logger.ps1
- session_state_manager.ps1
- super_organizer.ps1
- stdin_yes_feeder.ps1
- unified_memory_manager.ps1
- unified_progress_tracker.ps1
- universal_cli_logger.ps1
- user_preferences.ps1

#### 5D: Keep in Root (Essential Launch Scripts)
- start-all.bat / start-all.sh
- start-backend.bat / start-backend.sh
- start-gui.bat / start-gui.sh
- start-tray.bat / start-tray.sh
- build-release.sh
- build-complete-installer.bat
- build_installer.ps1

---

### Phase 6: Remove Temp Files and Standardize Naming

#### 6A: Delete Temporary Files
```bash
rm windows-ai-agent/tmp.txt
rm windows-ai-agent/tmp_test.txt
rm test_auto_approve_200351.txt
rm test-chatgpt-review.txt
```

#### 6B: Move Test Files to `/tests/`
```bash
mv test_baidu_plugin.py tests/plugins/
mv test_bedrock_plugin.py tests/plugins/
mv test_gpt4all_plugin.py tests/plugins/
mv test_gte_plugin.py tests/plugins/
mv test_serge_plugin.py tests/plugins/
```

#### 6C: Standardize Directory Naming
**Issue:** Inconsistent naming conventions
- `context_menu/` vs `context-menu-handler/` (DUPLICATE)
- `windows-ai-agent/` vs `windows_ai/` (different purposes, OK)

**Action:**
1. Remove duplicate `context-menu-handler/` directory
2. Keep `context_menu/` as canonical implementation

#### 6D: Move Miscellaneous Files
```bash
# CSV files
mkdir -p data/reconciliation/
mv reconcile_20250807-233516.csv data/reconciliation/

# AutoHotkey scripts
mv click_yes_agent.ahk scripts/automation/

# Consider external download
# nssm-2.24.zip (344 KB) - document download location instead
```

#### 6E: Remove Duplicate Configuration Files
```bash
# Keep only one
rm gitleaks.toml  # Keep .gitleaks.toml
```

---

### Phase 7: Update Configuration and Create Summary

#### 7A: Update .gitignore
Add patterns to prevent future issues:
```gitignore
# Temporary files
tmp*.txt
test_*.txt
*.tmp

# Build artifacts
release-*/
dist/
build/

# Archives
nssm-*.zip

# Session logs
*SESSION*.md
*WORK_SESSION*.md
```

#### 7B: Create New Directory Structure Documentation
**File:** `docs/DIRECTORY_STRUCTURE.md`
- Document purpose of each major directory
- Explain organization principles
- Guide for future development

#### 7C: Create Cleanup Summary
**File:** `REPOSITORY_CLEANUP_SUMMARY.md`
- What was removed and why
- What was reorganized
- New structure overview
- Space savings achieved

---

## New Directory Structure (After Cleanup)

```
Windows-AI/
├── README.md                    # Main documentation
├── CHANGELOG.md                 # Version history
├── CONTRIBUTING.md              # Contribution guidelines
├── SECURITY.md                  # Security policy
├── LICENSE                      # License file
├── GETTING_STARTED.md           # Quick start guide
├── BUILD_WINDOWS_INSTALLER.md   # Build instructions
│
├── Start Scripts (8 files)
│   ├── start-all.{bat,sh}
│   ├── start-backend.{bat,sh}
│   ├── start-gui.{bat,sh}
│   ├── start-tray.{bat,sh}
│   ├── build-release.sh
│   └── build-complete-installer.bat
│
├── Core Application
│   ├── apps/                    # Node.js applications
│   ├── windows_ai/              # Python backend
│   ├── windows-ai-agent/        # Agent service
│   └── windows-ai-tray/         # Tray application
│
├── Features & Components
│   ├── plugins/                 # Plugin system (cleaned)
│   ├── extensions/              # Extensions (consolidated)
│   ├── automation/              # Automation logic
│   ├── iot/                     # IoT integrations
│   ├── mesh/                    # Mesh networking
│   ├── sdk/                     # Extension SDK
│   └── [other feature dirs]
│
├── Development
│   ├── tests/                   # All tests
│   ├── scripts/                 # Utility scripts
│   │   ├── utilities/
│   │   └── automation/
│   ├── installer/               # Installation files
│   └── codex/                   # Task management
│
├── Documentation
│   ├── docs/
│   │   ├── ROADMAP.md          # Consolidated roadmap
│   │   ├── DIRECTORY_STRUCTURE.md
│   │   ├── history/            # Session reports
│   │   └── roadmap-archive/    # Old roadmap versions
│
├── Build Artifacts
│   ├── release-20251105-223624/ # Latest release only
│   └── dist/                    # Build outputs
│
└── Archive (new)
    ├── archive/
    │   ├── orchestrators/      # Old generation scripts
    │   ├── deployment/         # Old deployment scripts
    │   └── extension-generation/ # Old extension attempts
```

---

## Execution Checklist

### Pre-Cleanup
- [ ] Review current git status
- [ ] Ensure all changes are committed
- [ ] Create backup branch: `backup/pre-cleanup-2025-11-09`
- [ ] Run tests to establish baseline

### Phase 1: Critical Deletions
- [ ] Delete 5 old release directories
- [ ] Review and clean plugins/_invalid/
- [ ] Consolidate plugins/_duplicates/
- [ ] Remove temporary files

### Phase 2: Reorganization
- [ ] Consolidate extension directories
- [ ] Create docs/ subdirectories
- [ ] Move documentation files
- [ ] Move script files
- [ ] Standardize naming

### Phase 3: Documentation
- [ ] Create consolidated ROADMAP.md
- [ ] Create DIRECTORY_STRUCTURE.md
- [ ] Update .gitignore
- [ ] Create REPOSITORY_CLEANUP_SUMMARY.md

### Phase 4: Validation
- [ ] Run tests (ensure none broken)
- [ ] Verify all imports still work
- [ ] Test start scripts
- [ ] Review git diff

### Phase 5: Commit
- [ ] Stage all changes
- [ ] Create detailed commit message
- [ ] Push to cleanup branch
- [ ] Create PR for review

---

## Expected Results

### Space Savings
- **Before:** 31 MB (25.1 MB code)
- **After:** ~27 MB (21 MB code)
- **Savings:** ~3-4 MB, ~2,280 files removed

### Organization Improvements
- **Root MD files:** 42 → 8 (core docs only)
- **Root scripts:** 30+ → 8 (launch scripts only)
- **Release directories:** 6 → 1
- **Extension directories:** 4 → 1 (consolidated)
- **Plugin files:** -2,211 invalid/duplicate files

### Clarity Improvements
- Single authoritative roadmap
- Clear directory structure
- Better documentation organization
- Removed obsolete files
- Standardized naming

---

## Risk Mitigation

### Backup Strategy
1. Create git branch before cleanup: `backup/pre-cleanup-2025-11-09`
2. Tag current state: `pre-cleanup-20251109`
3. Keep archive/ directory for 30 days before final removal
4. Document all moves in REPOSITORY_CLEANUP_SUMMARY.md

### Testing Strategy
1. Run full test suite before cleanup
2. Run full test suite after cleanup
3. Verify all start scripts work
4. Check import paths aren't broken
5. Validate build process still works

### Rollback Plan
If issues arise:
```bash
git checkout backup/pre-cleanup-2025-11-09
# Or
git reset --hard pre-cleanup-20251109
```

---

## Timeline Estimate

- **Phase 1 (Deletions):** 30 minutes
- **Phase 2 (Reorganization):** 1-2 hours
- **Phase 3 (Documentation):** 1 hour
- **Phase 4 (Validation):** 30 minutes
- **Phase 5 (Commit):** 15 minutes

**Total:** 3-4 hours

---

## Questions to Answer Before Starting

1. **Keep or delete orchestrator scripts?**
   - Used for batch extension generation
   - Generation appears complete
   - **Recommendation:** Archive, don't delete

2. **Keep nssm-2.24.zip in repo?**
   - 344 KB binary file
   - Could be downloaded during build
   - **Recommendation:** Document download location, remove from repo

3. **What to do with _invalid plugins?**
   - 2,104 files that failed to generate
   - **Recommendation:** Delete after documenting issues

4. **Merge or archive old roadmaps?**
   - 8 files, ~250 KB
   - **Recommendation:** Create consolidated ROADMAP.md, archive originals

---

## Post-Cleanup Tasks

1. Update README.md with new structure
2. Update CONTRIBUTING.md with file organization guidelines
3. Run full test suite
4. Update any broken import paths
5. Test build process
6. Create release notes documenting cleanup
7. Update any CI/CD scripts if needed

---

**Status:** Ready to begin Phase 1
**Approved by:** Pending approval
**Execution Date:** TBD
