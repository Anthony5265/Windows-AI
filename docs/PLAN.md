# Windows AI Delivery Plan

This plan mirrors the PhaseTracker goals and is scoped to reach 100% completion:

- Phase 0: Charter + guardrails, publish this plan, initialize changelog and root security policy, keep rollback hooks ready.
- Phase 1: Keep backend and plugin runtime stable, persist user config under `%USERPROFILE%/.windows-ai/config.json`, and keep folder watchers + scheduler configs active.
- Phase 2: Maintain GUI + tray scaffolds and ensure at least two automation + scheduler templates remain healthy.
- Phase 3: Ensure IoT, mesh, discovery, search, and cloud sync surfaces exist (cloud_sync stub included) and stay wired into the repo.
- Phase 4: Ship packaging assets plus release automation (`build-release.sh`) and watchdog service (`watchdog.py`), with installer validation tests.
- Phase 5: Keep marketplace, registry, model discovery, and community docs (CONTRIBUTING, ROADMAP, ROADMAP_IMPLEMENTATION, CHANGELOG) up-to-date.
- Phase 6: Maintain policy docs (security, privacy, encryption) and keep a minimal policy engine with permissions + audit stubs.
- Phase 7: Provide watchdog, update server assets, deployment start scripts, and rollback automation with runbooks.
- Phase 8: Provide first-run and desktop onboarding wizards alongside mobile and app portfolio docs.
- Phase 9: Preserve SDK coverage, OpenAPI spec, CLI distribution, and developer docs (API_REFERENCE, ACTIONS_API, ENHANCEMENTS_SUMMARY).

## Near-term checkpoints
- Keep automation configs versioned (watchers.json, scheduler.json, config.json).
- Run release script before packaging artifacts; keep watchdog enabled for runtime checks.
- Update changelog when shipping new milestones and align docs with code changes.
