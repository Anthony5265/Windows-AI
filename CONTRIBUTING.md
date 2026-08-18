# Contributing to Windows-AI

Thank you for helping improve Windows-AI. This repository is a Windows-first AI platform with a Python core, desktop applications, agents, tools, integrations, and extensibility layers.

## Source of truth

Before making changes, read [`AI_BLUEPRINT.md`](AI_BLUEPRINT.md). It is the **single canonical blueprint** for active development.

Also read [`AGENTS.md`](AGENTS.md) for repository-wide AI-agent and development rules.

Do not create or follow competing blueprints, roadmaps, or active development plans unless the repository owner explicitly requests one.

## Development workflow

1. Fork or clone the repository.
2. Install the appropriate runtime dependencies for the area you are changing.
3. Inspect the existing implementation before introducing new architecture.
4. Prefer extending or consolidating existing systems over creating duplicates.
5. Keep changes focused, production-oriented, and compatible with the canonical architecture.
6. Update documentation when behavior, APIs, configuration, or architecture changes.
7. Open a pull request with a clear description of the change.

## Python setup

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Node setup

```bash
npm install
```

The repository contains multiple application workspaces under `apps/`; use the workspace-specific commands documented by the application you are changing.

## Code style

- Follow the repository `.editorconfig`.
- Python: use type hints where practical and keep imports organized.
- Prefer small, cohesive modules over growing monolithic entry points.
- Use existing exception, logging, configuration, permission, and tool abstractions.
- Do not silently introduce credentials, tokens, or machine-specific paths.
- Avoid unnecessary breaking API changes.

## Adding functionality

### Tools

New AI-callable capabilities should use the unified tool architecture under `windows_ai/tools/` whenever the capability is intended to be invoked by an agent or model.

### Plugins

Use the existing plugin manager, lifecycle, validation, and permission systems rather than creating a second plugin runtime.

### API routes

Use the existing FastAPI API architecture and register routes through the established API/server structure.

### Agents

Use the existing agent/runtime architecture and route tool execution through the canonical tool router.

## Testing policy

Testing is intentionally **deferred during the active implementation phase** according to the project blueprint.

Do not turn ordinary feature work into a test-writing campaign, expand test coverage as a development objective, or treat historical test plans as current product requirements.

Testing remains part of the project and will be performed comprehensively during the **final validation phase** after implementation is substantially complete.

When final validation begins, the repository's existing test, security, performance, packaging, API, GUI, and compatibility infrastructure should be brought up to the required release standard.

## Pull requests

Every pull request should explain:

- What changed.
- Why it changed.
- Which architectural area it affects.
- Any migration or configuration implications.
- Any documentation that was updated.

Keep unrelated cleanup out of focused feature changes unless the cleanup is necessary to preserve architectural consistency.
