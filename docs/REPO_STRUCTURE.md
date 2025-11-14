# Repository Organization Guide

This guide summarizes the purpose of every top-level directory in the Windows AI
monorepo and highlights notable subdirectories or files. Use it as a map when
navigating the codebase or planning cross-service work.

## Core Applications

- **`windows_ai/`** – Python FastAPI backend that powers the local agent.
  - `routers/`, `services/`, and `models/` capture API surface and business
    logic.
  - `automation/` inside the backend hosts scheduled jobs and file watchers.
- **`windows-ai-agent/`** – Node.js service implementing the command-and-control
  layer for Windows integrations.
  - `src/cli/` for command-line tooling.
  - `src/plugins/` contains integration hooks that mirror backend abilities.
- **`windows-ai-tray/`** – Electron-based system tray UI that gives users quick
  access to commands and status.
  - `app/` holds renderer code and preload scripts.
- **`gui/`** – Main Electron chat experience with streaming conversations and
  workspace management.
  - `apps/main/` drives the renderer, while `apps/background/` handles process
    management.
- **`apps/`** – Additional Node.js microservices (actions, proxy, agent hub,
  webhooks) that extend the core experience.
  - Each workspace declares its dependencies inside `package.json` files.

## AI and Automation Extensions

- **`plugins/`** – Modular plugins for automation, search, scheduling, and
  model management.
  - Organized by capability (e.g., `automation`, `content`, `system`).
- **`automation/`** – Standalone automation workflows and reusable job
  templates.
- **`control_center/`** – Coordination services that broker messages between the
  backend, tray, and GUI components.
- **`mesh/`** – Foundations for the distributed mesh-network vision, including
  peer discovery and synchronization.
- **`iot/`** – Device connectors and automations specific to home IoT setups.

## Platform Integrations & Installers

- **`installer/`**, **`build-complete-installer.bat`**, **`build-release.sh`** –
  Assets for packaging the full Windows AI distribution.
- **`windows-ai-tray/startup/`** & **`start-*.{sh,bat}`** scripts – Convenience
  launchers across Windows, macOS, and Linux.
- **`nssm-2.24/`** and `nssm-2.24.zip` – Windows service wrapper binaries.
- **`build_installer.ps1`** and `build-complete-installer.bat` – PowerShell and
  batch utilities for shipping signed builds.

## Configuration & Shared Assets

- **`config/`** – Default configuration templates (YAML, JSON) for backend and
  automation services.
- **`assets/`** – Shared branding (icons, logos, fonts) consumed by the GUI and
  tray.
- **`docs/`** – Project documentation, architecture notes, and release guides.
- **`specs/`**, **`openapi/`**, **`docs/structure/`** – Protocol definitions and
  generated API specifications.
- **`context_menu/`**, **`control_center/`**, **`first-run-wizard/`** – UX
  helpers surfaced during onboarding or contextual interactions.

## Development Tooling & Infrastructure

- **`scripts/`** – Utility scripts for building, linting, releasing, and
  generating manifests.
- **`start-*.sh`, `start-*.bat`** – Helper scripts to launch subsets of the
  stack for development and demos.
- **`Dockerfile`**, **`docker/`**, **`backend_bundle_simple.spec`** – Container
  recipes and PyInstaller specs for bundling services.
- **`tests/`** – Automated test suites across Python and JavaScript packages.
- **`automation/ci/`**, **`workflows/`** – Continuous integration helpers and
  GitHub Actions workflows.
- **`requirements*.txt`, `package.json`, `package-lock.json`** – Dependency
  locks for Python and Node.js environments.

## Archived, Experimental, and Legacy Areas

- **`archive/`** – Deprecated assets retained for historical reference.
- **`proposed-patches/`**, **`release-*/`** – Saved patches and release artifacts
  for tracing changes over time.
- **`eco/`**, **`domains/`**, **`marketplace/`** – Exploratory initiatives and
  prototypes that may evolve into full features.

---

### How to Use This Guide

1. Locate the directory relevant to your task.
2. Follow the referenced subdirectories or scripts to identify the owning
   service.
3. Cross-reference with the manifest in `docs/structure/` for machine-readable
   context or use `scripts/generate_repo_manifest.py` to regenerate metadata.

> **Tip:** When adding new components, update this guide and the manifest so the
> repository remains discoverable for every contributor.
