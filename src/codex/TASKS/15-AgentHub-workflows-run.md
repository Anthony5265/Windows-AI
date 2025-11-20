# Task 15 — AgentHub-workflows-run


POST /workflows/run: validate spec, coerce inputs, dispatch by mode, return normalized result. Log runs.
Acceptance:
- Valid spec succeeds; invalid returns INVALID_SPEC.
