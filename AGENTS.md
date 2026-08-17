# Windows-AI AI Agent Instructions

## Mandatory first step

Before modifying this repository, read:

1. `AI_BLUEPRINT.md`

`AI_BLUEPRINT.md` is the **single canonical source of truth** for active Windows-AI development.

## Development rules

- Follow `AI_BLUEPRINT.md` over older roadmaps, blueprints, TODO files, reports, or historical agent instructions.
- Build and improve production functionality first.
- Inspect the existing implementation before changing it.
- Reuse existing architecture and avoid duplicate systems.
- Preserve existing functionality and APIs unless a deliberate architectural change is required.
- Do not create competing development plans unless the repository owner explicitly asks for one.

## Testing is deferred

**DO NOT prioritize testing during active development. Testing is reserved for the final phase after the product implementation is substantially complete.**

During active development, AI agents should NOT:

- Write new test suites as part of normal feature work.
- Expand test coverage.
- Run broad test campaigns.
- Spend development time fixing unrelated existing test failures.
- Treat test coverage or test results as active feature-completion requirements.
- Allow historical test plans or test reports to override `AI_BLUEPRINT.md`.

A build command or other validation step may be used only when intrinsically necessary to implement/package the production functionality, but testing is not the development objective.

## Final validation

Testing becomes a dedicated final project phase only after the active implementation roadmap is substantially complete. At that point, perform comprehensive unit, integration, end-to-end, GUI, API, security, packaging, compatibility, performance, and release validation as appropriate.

## Working principle

**Develop first. Validate at the end.**

Do not mistake the deferred testing policy for permission to intentionally introduce insecure behavior, secrets, or unnecessary breaking changes.
