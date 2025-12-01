Open `codex/manifest.json`, `specs/WindowsAI_MasterSpec_latest.md` (or fallbacks), and `codex/STATE.json`.
Work only on tasks with `"status":"todo"`. For each:
- Plan → Implement → Test → Commit (Conventional Commits) → Update STATE with commit SHA → Append HISTORY log.
If blocked, mark `"status":"blocked"` and write a remediation hint. Always exit with a short summary.
