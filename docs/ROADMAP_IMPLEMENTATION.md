# Roadmap Implementation Notes

- Release pipeline: use `build-release.sh` to bundle artifacts after tests and lint.
- Operations: enable `watchdog.py`, maintain `update-server/manifest.json`, and provide `start-*` scripts for ops teams.
- Policy engine: keep `security/permissions.py` and `security/audit.py` minimal but present for enforcement hooks.
- Onboarding: ship `first-run-wizard/wizard.html` and `wizard/wizard.html` as ready-to-ship experiences.
- Developer docs: maintain `API_REFERENCE.md`, `ACTIONS_API.md`, and `ENHANCEMENTS_SUMMARY.md` alongside the OpenAPI spec.
