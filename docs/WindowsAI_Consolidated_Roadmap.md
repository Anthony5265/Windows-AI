# Windows AI — Consolidated Roadmap & Blueprint

**Generated:** 2025-08-09 20:57:05

This file merges the current repo state with the Windows AI blueprint and marks what’s **Done**, **In Progress**, and **Not Started**, plus a **Keep vs Add** list and **Next Steps**.

## Quick Links
- Master Blueprint: docs/WindowsAI_Master_Blueprint.md
- Repo Organization Plan: docs/Repo_Organization_Plan.md
- Phase Tracking: docs/Phase_Tracking_Sheet.md
- Full Archive: docs/history/WindowsAI_Raw_Archive.md

## Status by Area
| Area | Status | Notes |
|---|---|---|
| Phase 0—Definition & Safety | ✅ | Goals locked, safety docs & diag workflow |
| Phase 1—Core Agent Scaffolding | ✅ | Agent/tray scaffolds + CI outline present |
| Phase 3.1—Tray polish & CI | 🔄 | Watchdog polish, notifications, .gitattributes |
| Phases 4–6 (GUI, Mesh, Packaging) | ⏳ | Planned per blueprint |

## Keep vs Add (structure)
**Keep:** keep existing repo layout; migrate gradually  
**Add:** pps/{gui,actions,agenthub,proxy}, ssets/workflows, config, scripts (added with .gitkeep)

## Workflow Key
Map OPENAI_API_KEY to the GitHub Actions secret in each workflow’s **root nv:** (the secret name is OPENAI_API_KEY).

## Next steps
1) Commit this PR branch with these docs  
2) Verify workflows (see CHANGES_PR.md)  
3) Start moving code into pps/ as it’s implemented
