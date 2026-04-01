# Installer Assistant Vision

## Purpose

Windows AI is intended to provide a user-friendly Windows installation and onboarding experience that does not require technical skill.

A major part of that vision is an integrated AI-guided setup assistant embedded into the installer flow, first-run flow, or both.

The goal is to reduce friction, explain choices clearly, automate safe setup steps, and help users get into the product with minimal manual work.

---

## Product idea

Instead of making users manually install prerequisites, choose runtimes blindly, configure providers by hand, or troubleshoot confusing setup issues, Windows AI should guide them through setup with a lightweight built-in assistant.

This assistant may be implemented as:
- an embedded lightweight local model
- a bundled assistant service
- a bootstrap helper process
- a first-run guided onboarding agent
- a hybrid local/cloud onboarding experience

The exact implementation can vary, but the user-facing outcome should remain the same:

**install Windows AI, follow the guided experience, and start using it without needing developer skills.**

---

## Responsibilities of the setup assistant

The assistant should help with:

- welcoming the user and explaining the setup process
- detecting basic environment capabilities
- helping choose between local and cloud AI modes
- preparing or validating required components
- explaining optional downloads in plain language
- handling first-run configuration
- surfacing errors in user-friendly language
- guiding recovery steps when setup problems occur

---

## Design goals

### 1. Reduce technical friction
The setup flow should avoid exposing users to unnecessary implementation details.

### 2. Explain choices clearly
Users should understand what Windows AI is doing and why.

### 3. Prefer automation where safe
If a step can be handled automatically and safely, Windows AI should do it.

### 4. Respect privacy
Local-first options should be supported wherever practical, and cloud usage should be clearly communicated.

### 5. Keep the product approachable
The setup assistant should make Windows AI feel welcoming rather than intimidating.

---

## Example user flow

1. User downloads `WindowsAI-Setup.exe`
2. User runs installer
3. Installer launches or includes setup assistant
4. Assistant checks system readiness
5. Assistant helps select recommended setup path
6. Assistant prepares required components
7. Assistant completes first-run configuration
8. User enters the app in a usable state

---

## Suggested architecture directions

Possible implementation options:

### Option A: Embedded lightweight local assistant
A small bundled local model or rules-driven assistant helps with setup and onboarding entirely on-device.

### Option B: Bootstrap helper service
A lightweight helper executable handles environment checks, setup tasks, and guided onboarding.

### Option C: Hybrid onboarding assistant
A minimal local assistant manages setup locally, with optional cloud-assisted help for richer onboarding or troubleshooting.

---

## Risks and constraints

- installer size growth
- offline vs online setup tradeoffs
- safe privilege elevation
- antivirus false positives
- hardware variability across Windows systems
- balancing simplicity against advanced configuration flexibility

---

## Current repo gap

Based on product direction, the integrated setup assistant should be treated as a first-class part of Windows AI.

If the current codebase does not yet include a clear implementation of this onboarding/bootstrap concept, it should be added back into the roadmap and tracked explicitly as a missing product-critical capability.

---

## Roadmap recommendation

Track the following as explicit milestones:

- installer bootstrap helper
- AI-guided onboarding flow
- first-run setup assistant
- user-friendly environment validation
- local/cloud configuration wizard
- setup recovery and troubleshooting flow

---

## Success criteria

Windows AI should eventually reach a point where a non-technical user can:

- download the installer
- run it
- follow guided prompts
- complete setup with minimal confusion
- begin using core Windows AI features without manual developer-style setup
