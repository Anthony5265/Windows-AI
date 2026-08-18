# Windows-AI GitHub Copilot Instructions

## Authority

Before changing this repository, read:

1. `AI_BLUEPRINT.md` — the single source of truth for product direction, architecture, priorities, and completion criteria.
2. `AGENTS.md` — the required operating rules for AI coding agents.

Historical plans, old roadmaps, task queues, reports, and generated planning documents are reference material only. Do not create or follow a competing master plan.

## Development mode

Windows-AI is in active implementation.

- Build production functionality first.
- Start with the existing repository structure and understand it before introducing architecture.
- Prefer repairing, integrating, consolidating, and extending existing systems over parallel implementations.
- Keep responsibilities separated and public interfaces coherent.
- Remove obsolete duplication when safe and update documentation/configuration when behavior changes.
- Continue implementation when work is requested; do not stop at a plan when repository tooling permits the implementation.

## Required file-by-file workflow

When performing a repository-wide audit, process directories and files in deterministic repository order:

1. Inspect the current file and its surrounding module.
2. Determine its purpose and dependencies.
3. Decide whether it should be kept, corrected, consolidated, moved, replaced, or removed.
4. Make the smallest coherent production change required.
5. Preserve required behavior and update references when moving or removing files.
6. Continue to the next file without skipping unrelated repository areas.

Do not claim a repository-wide audit is complete until every repository item in scope has been reviewed.

## Testing policy

**Testing is deferred until the final development phase.**

Do not create, expand, or prioritize test suites, coverage targets, benchmark-only work, or testing campaigns during active implementation. Build/package validation may be used only when it is intrinsically required to implement production functionality.

Final validation and comprehensive testing happen after implementation is substantially complete.

## Architecture

Follow `AI_BLUEPRINT.md`. Windows-AI has one canonical runtime and one unified Tool/Action architecture spanning built-in tools, plugins, MCP, agents, providers, workspaces, Windows capabilities, and services.

Do not introduce a second runtime, competing tool registry, competing agent system, or another master blueprint without first making an explicit architectural decision in `AI_BLUEPRINT.md`.

## AI-agent behavior

- Inspect repository state; never invent it.
- Follow existing interfaces before creating new ones.
- Integrate new functionality into the canonical runtime and architecture.
- Do not declare functionality complete merely because a file or interface exists; follow its integration path.
- Do not use historical planning artifacts as current authority.

## Security

Never commit credentials, API keys, tokens, passwords, private keys, or machine-specific secrets. Preserve security boundaries and permission checks.

## Completion

Development is complete only when the implementation required by `AI_BLUEPRINT.md` is substantially implemented, integrated, organized, documented, and production-ready. Comprehensive testing and final validation are a separate final phase.

**Canonical rule: Develop first. Validate at the end.**
