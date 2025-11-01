# Windows AI Build Plan

## Phase 0 — Definition + Safety Net ✅
- Goals, runtime, UI, secrets policy set
- Branching model decided: feature/windows-ai-phase-1
- Safety files added: PLAN.md, CHANGELOG.md, rollback + verify scripts
- Diagnostic workflow ready

## Phase 1 — Core Agent (next step)
- windows-ai-agent/ Node service with plugins (shell, files, openai, github)
- wai CLI
- PowerShell installer as Windows service
- CI build artifact + smoke tests
- README.windows-ai.md with setup screenshots

## Phase 2 — Tray GUI
- Electron tray app
- Command box + status
- Toggle for triggers

## Phase 3 — Integrations
- GitHub trigger UI
- Folder watcher automation
- Scheduled jobs

## Phase 4 — Packaging
- Windows installer build
- Release pipeline

---
**Progress Tracking:**  
- [x] Phase 0  
- [ ] Phase 1  
- [ ] Phase 2  
- [ ] Phase 3  
- [ ] Phase 4  
