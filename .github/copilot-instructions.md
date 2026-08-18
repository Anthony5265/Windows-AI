# Windows-AI GitHub Copilot Instructions

## Authority

Before changing this repository, read:

1. `AI_BLUEPRINT.md` — the **single source of truth** for Windows-AI product direction, architecture, priorities, and completion criteria.
2. `AGENTS.md` — the required operating rules for AI coding agents.

Do not treat `BLUEPRINT.md`, `ROADMAP.md`, historical plans, old task queues, reports, or generated planning documents as competing sources of truth. Historical material is reference-only unless its requirements have been incorporated into `AI_BLUEPRINT.md`.

## Development mode

Windows-AI is in active implementation.

- Build production functionality first.
- Inspect existing code before creating new architecture.
- Prefer integrating, repairing, consolidating, and extending existing systems over creating parallel implementations.
- Preserve compatible behavior unless the canonical blueprint requires a deliberate change.
- Keep code organized by responsibility.
- Remove obsolete duplication when it is safe to do so.
- Keep documentation aligned with implemented behavior.

## Testing policy

**Testing is deferred until the final development phase.**

During active development, do not create or prioritize test suites, coverage work, benchmark-only work, or test campaigns. A validation/build command may be used when it is intrinsically necessary to implement or package production functionality, but testing is not an active completion gate.

Final validation will occur only after the implementation is substantially complete.

## Repository workflow

For every change:

1. Read `AI_BLUEPRINT.md`.
2. Read the relevant existing implementation.
3. Determine whether the capability already exists.
4. Reuse or integrate existing architecture when possible.
5. Implement the smallest coherent production change that advances the canonical architecture.
6. Update affected documentation or configuration when behavior changes.
7. Keep the repository free of obsolete duplicate plans and implementations.

## Architecture principles

Windows-AI uses the canonical architecture defined by `AI_BLUEPRINT.md`, including:

- Canonical application runtime
- Agent orchestration
- Provider/model abstraction
- Unified Tool/Action architecture
- Permission and execution boundaries
- Built-in tools
- Plugin ecosystem
- MCP integration
- Workspace/project context
- Memory and knowledge systems
- Windows-native capabilities
- API/service interfaces
- Local, cloud, and hybrid model routing

Do not introduce a second runtime, competing tool registry, competing agent system, or another master blueprint without an explicit architectural decision incorporated into `AI_BLUEPRINT.md`.

## AI-agent behavior

Do not invent repository state. Inspect it.

Do not claim a feature is complete merely because a file or interface exists. Follow the implementation and integration requirements in `AI_BLUEPRINT.md`.

Do not stop at planning when implementation is requested. Continue through the repository's active development scope using the available repository tooling.

## Security

Never commit credentials, API keys, tokens, passwords, private keys, or machine-specific secrets. Do not disable security controls merely to make development easier.

## Completion

The project is considered development-complete only when the implementation required by `AI_BLUEPRINT.md` is substantially present, integrated, documented, and production-ready. Comprehensive testing and final validation happen afterward as a dedicated final phase.

**Canonical rule: Develop first. Validate at the end.**
