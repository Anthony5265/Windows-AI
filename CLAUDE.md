# CLAUDE.md

This file provides guidance to Claude Code and other Claude-based agents working in Windows-AI.

## Authority

Before changing the repository, read:

1. `AI_BLUEPRINT.md` — the **single source of truth** for product direction, architecture, priorities, and completion criteria.
2. `AGENTS.md` — the repository-wide AI-agent operating rules.

Do not rely on `BLUEPRINT.md`, `ROADMAP.md`, historical plans, old task queues, generated reports, or previous agent-session instructions as competing sources of truth. Historical material is reference-only unless its requirements have been incorporated into `AI_BLUEPRINT.md`.

## Development mode

Windows-AI is in active implementation.

- Build production functionality first.
- Inspect the existing implementation before creating new architecture.
- Prefer integration, repair, consolidation, and extension over parallel systems.
- Preserve compatible behavior unless the canonical blueprint deliberately requires a change.
- Keep responsibilities separated and repository structure coherent.
- Remove obsolete duplication when safe.
- Keep documentation and configuration aligned with actual behavior.

## Testing policy

**Testing is deferred until the final development phase.**

Do not create or prioritize test suites, coverage campaigns, benchmark-only work, or broad testing during normal implementation. A build or validation command may be used only when intrinsically necessary to implement or package production functionality.

Do not treat existing test status, coverage targets, or historical QA plans as active development gates.

Final validation happens after the implementation required by `AI_BLUEPRINT.md` is substantially complete.

## Repository workflow

For each change:

1. Read `AI_BLUEPRINT.md` and relevant `AGENTS.md` guidance.
2. Inspect the existing implementation and its callers.
3. Determine whether the capability already exists elsewhere.
4. Reuse or integrate existing architecture where possible.
5. Implement the smallest coherent production change that advances the canonical architecture.
6. Update affected documentation/configuration when behavior changes.
7. Remove obsolete competing implementations or planning artifacts when safe.

## Architecture guardrails

Use the architecture defined by `AI_BLUEPRINT.md`, including the canonical application runtime, agent orchestration, provider/model abstraction, unified Tool/Action architecture, permission boundaries, built-in tools, plugins, MCP, workspace context, memory/knowledge, Windows capabilities, APIs, and local/cloud/hybrid routing.

Do not introduce a second master blueprint, competing runtime, competing tool registry, or competing agent system without an explicit architectural decision incorporated into `AI_BLUEPRINT.md`.

## AI-agent behavior

- Inspect repository state; never invent it.
- Do not claim a feature is complete merely because an interface or file exists.
- Follow the implementation and integration requirements in `AI_BLUEPRINT.md`.
- When asked to continue development, continue implementation rather than stopping at planning.
- Keep the repository internally consistent as older components are consolidated.

## Security

Never commit credentials, API keys, tokens, passwords, private keys, or machine-specific secrets. Never weaken security merely to make development easier.

## Completion

Development is complete only when the implementation required by `AI_BLUEPRINT.md` is substantially present, integrated, documented, and production-ready. Comprehensive testing and final validation are a separate final phase.

**Canonical rule: Develop first. Validate at the end.**
