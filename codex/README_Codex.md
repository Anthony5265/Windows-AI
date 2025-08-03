# Codex Runner — Windows AI

Codex entrypoint files and rules:

- **Manifest:** `codex/manifest.json` (must point to `specs/WindowsAI_MasterSpec_latest.md`)
- **Spec fallback chain:** `specs/WindowsAI_MasterSpec_v*`
- **Task list:** `codex/TASKS/`
- **STATE:** `codex/STATE.json` (Codex updates this as it works)
- **SCHEMAS for OpenAPI:** `codex/SCHEMAS/`

### How to run Codex

> Paste the following (exact) prompt when you start a new Codex session:

```
Open codex/manifest.json, then specs/WindowsAI_MasterSpec_latest.md and codex/STATE.json.
Work tasks with "status":"todo" in codex/STATE.json in ascending numeric order.
For each task:
  1) Make a short plan.
  2) Implement code and config changes (create files in the correct repo paths).
  3) Run tests/linters/build steps described in the task/spec. If missing, generate sensible tests.
  4) Commit using Conventional Commits. Include the task number in the scope, e.g., feat(task-0007): <message>.
  5) Update codex/STATE.json with the new status and the commit SHA.
  6) Append a run log to codex/HISTORY/<ISO8601>.md: summary, changed files, commands run, next steps.
Stop when no "todo" tasks remain or ~90 minutes pass; output a session summary and write it to codex/HISTORY.
```

### Notes

- The OpenAPI file under `openapi/windows-ai.yaml` now references the schemas under `codex/SCHEMAS/` using correct relative `$ref` paths.
- CI workflows are split:
  - **Linux**: Python tests + Node workspace tests.
  - **Windows**: PSScriptAnalyzer lints PowerShell scripts and does a low‑risk smoke load of installer scripts.
