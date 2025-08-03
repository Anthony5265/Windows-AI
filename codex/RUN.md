# Windows AI — Codex Control Folder (RUN THIS EACH SESSION)

Paste this into your assistant and follow it exactly:

> Open `codex/manifest.json`. Then open `specs/WindowsAI_MasterSpec_latest.md` (if present) and `codex/STATE.json`.
> List all tasks with status `"todo"` in `codex/STATE.json` and load matching cards from `codex/TASKS/` (ascending numeric order).
> For each task:
>  1) Draft a short plan.
>  2) Implement the changes. Create files under the correct repo paths (move from `codex/` mirrors when required).
>  3) Run tests/linters/build described by the task. If a step is missing, generate it.
>  4) Commit using Conventional Commits. Update `codex/STATE.json` with the task's new status and the commit SHA.
>  5) Append a run log to `codex/HISTORY/<ISO8601>.md` with: summary, changed files, commands, next steps.
> Stop when no `todo` tasks remain OR on a blocking error. If blocked, set `"status":"blocked"` and write a hint.

**Conventions**
- Use **/api/actions/execute** as the Actions API endpoint (OpenAPI in `codex/openapi/windows-ai.yaml`).
- Respect `codex/SCHEMAS/*.json` when generating JSON/YAML.
- Keep human docs in `docs/` and machine contracts in `openapi/` at repo root. If those folders don't exist yet,
  copy the mirrors from `codex/ROOT_FILES` and `codex/openapi` to the repo root as part of Task 00.
- Always update `codex/STATE.json`. Never rely on ephemeral memory to remember progress.
