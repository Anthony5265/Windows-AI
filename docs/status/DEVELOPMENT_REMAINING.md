# Windows AI — Development Remaining (Snapshot)

**Date:** 2026-04-13 (updated)
**Source of truth:** `ROADMAP.md` (last updated 2026-03-10)

This checklist captures all roadmap items still marked incomplete (`[ ]`) in the current master roadmap.

## Phase 1 — Stability & Completeness
- Wire up remaining XR features when OpenXR hardware is available.
- Reach 60%+ overall test coverage (roadmap notes current ~40%).

## Phase 2 — Feature Completion
### GUI
- Plugin marketplace browser in GUI.
- Multi-agent task flow visualization (graph/timeline).
- Accessibility improvements (screen reader support, keyboard navigation).
- Windows Hello biometric login integration.

### Mobile Companion
- Complete `mobile/` TypeScript companion app integration.
- QR pairing flow between desktop and mobile.
- Remote monitoring of desktop AI agent.
- Voice commands via mobile.

## Phase 3 — Production Hardening
### Build & Distribution
- Verify/test PyInstaller build on Windows 10/11.
- Validate Electron NSIS installer + auto-update.
- Produce portable ZIP distribution.
- Create Windows Store MSIX package.
- Add CI/CD automated release pipeline on tag push.

## Phase 4 — Ecosystem & Community
### Community
- Plugin marketplace website.
- Community Discord / GitHub Discussions.
- Plugin of the week / featured plugins.

### XR/AR/VR Expansion
- Full spatial UI framework completion.
- HoloLens/Quest integration testing.
- AR overlay for Windows desktop.
- Voice + gesture AI interaction in XR spaces.
