# Windows AI Repository Map

The Windows AI monorepo is grouped into curated categories so contributors can quickly locate code,
documentation, and operational assets.  Every top-level path is assigned to exactly one category.  Use the
tables below to understand what lives where and cross-reference the machine-readable manifest for
automation-friendly access.

## Documentation & Knowledge Base

| Path | Type | Summary |
| --- | --- | --- |
| `docs` | Directory | Product documentation, runbooks, and feature guides. |
| `specs` | Directory | Architecture briefs, proposals, and detailed specifications. |
| `codex` | Directory | AI co-pilot work queues and generated task inventories. |
| `assets` | Directory | Shared imagery, icons, and media assets. |
| `openapi` | Directory | Service definitions expressed as OpenAPI contracts. |
| `README.md` | File | Entry point for the repository. |
| `GETTING_STARTED.md` | File | Onboarding checklist for new contributors. |
| `CHANGELOG.md` | File | Record of user-visible changes. |
| `GUI_BACKEND_INTEGRATION_SUMMARY.md` | File | Notes on how the GUI connects to backend services. |

## Client Interfaces & UX

| Path | Type | Summary |
| --- | --- | --- |
| `apps` | Directory | Desktop application bundles, including GUI binaries. |
| `control_center` | Directory | Control Center interface for managing the platform. |
| `gui` | Directory | Shared GUI components and static assets. |
| `ui` | Directory | Web UI source and build outputs. |
| `terminal` | Directory | Terminal client and shell integrations. |
| `wizard` | Directory | Installation wizard implementation. |
| `first-run-wizard` | Directory | Guided first-run configuration experience. |
| `windows-ai-tray` | Directory | Windows system tray companion. |
| `mobile` | Directory | Mobile companion clients. |
| `iot` | Directory | IoT control experiences and dashboards. |
| `xr` | Directory | Extended reality experiments. |

## Core Runtime & Services

| Path | Type | Summary |
| --- | --- | --- |
| `windows-ai-agent` | Directory | Primary agent runtime orchestration. |
| `windows_ai` | Directory | Shared Python packages and service utilities. |
| `agents` | Directory | Agent definitions and behaviours. |
| `backends` | Directory | Backend services for inference, storage, and orchestration. |
| `cloud_sync` | Directory | Cloud synchronization components. |
| `mesh` | Directory | Mesh networking services. |
| `domains` | Directory | Vertical-specific service packages. |
| `search` | Directory | Search and indexing services. |
| `sdk` | Directory | SDKs for extending Windows AI. |
| `model_discovery` | Directory | Model registry and discovery tooling. |
| `optimization` | Directory | Optimization utilities (depth limited in manifest). |
| `performance` | Directory | Performance benchmarking artefacts. |
| `workflows` | Directory | Reusable workflow definitions consumed by the runtime. |

## Automation, Integrations & Extensions

| Path | Type | Summary |
| --- | --- | --- |
| `automation` | Directory | Automation templates and orchestration helpers. |
| `plugins` | Directory | Plugin development kits and examples. |
| `context_menu` | Directory | Windows shell context menu integrations. |
| `eco` | Directory | Sustainability and eco-mode features. |
| `marketplace` | Directory | Marketplace services and tooling. |
| `install` | Directory | Installer runtime components and helper binaries. |
| `installer` | Directory | Installer build logic and packaging scripts. |
| `update-server` | Directory | Update server deployment assets. |
| `updater` | Directory | Client updater implementation. |

## Operations, Tooling & Deployment

| Path | Type | Summary |
| --- | --- | --- |
| `scripts` | Directory | Operational and developer helper scripts. |
| `.devcontainer` | Directory | Development container configuration. |
| `.github` | Directory | GitHub workflows, bots, and templates. |
| `Dockerfile` | File | Container build definition. |
| `backend_bundle_simple.spec` | File | PyInstaller specification for backend bundling. |
| `BUILD_WINDOWS_INSTALLER.md` | File | Checklist for assembling Windows installers. |
| `build-complete-installer.bat` | File | Windows batch helper for installer packaging. |
| `build-release.sh` | File | Release automation for Unix-like environments. |
| `build_installer.ps1` | File | PowerShell entry point for installer builds. |
| `start-all.sh` | File | Launches the full local stack on Unix systems. |
| `start-all.bat` | File | Launches the full local stack on Windows. |
| `start-backend.sh` | File | Starts backend services on Unix. |
| `start-backend.bat` | File | Starts backend services on Windows. |
| `start-gui.sh` | File | Runs the GUI locally on Unix. |
| `start-gui.bat` | File | Runs the GUI locally on Windows. |
| `start-tray.sh` | File | Starts the tray application on Unix. |
| `start-tray.bat` | File | Starts the tray application on Windows. |
| `start-watchdog.sh` | File | Launches watchdog monitoring on Unix. |
| `start-watchdog.bat` | File | Launches watchdog monitoring on Windows. |
| `watchdog.py` | File | Python watchdog service entry point. |

## Security, Compliance & Governance

| Path | Type | Summary |
| --- | --- | --- |
| `security` | Directory | Security reviews and compliance records. |
| `SECURITY.md` | File | Security reporting process and best practices. |
| `LICENSE` | File | Open-source license. |
| `CONTRIBUTING.md` | File | Guidelines for contributors. |

## Testing & Quality Assurance

| Path | Type | Summary |
| --- | --- | --- |
| `tests` | Directory | Unit, integration, and end-to-end tests. |
| `pytest.ini` | File | Pytest configuration. |
| `requirements-test.txt` | File | Python dependencies required for the test suite. |

## Configuration & Dependency Management

| Path | Type | Summary |
| --- | --- | --- |
| `config` | Directory | Shared configuration files used across services. |
| `requirements.txt` | File | Primary Python dependency list. |
| `requirements-dev.txt` | File | Additional dependencies for development workflows. |
| `requirements.lock` | File | Locked versions for deterministic builds. |
| `package.json` | File | Node.js package manifest. |
| `package-lock.json` | File | Locked Node.js dependency graph. |
| `commitlint.config.js` | File | Commit linting configuration. |
| `.coveragerc` | File | Coverage settings for Python tooling. |
| `.editorconfig` | File | Editor defaults. |
| `.gitattributes` | File | Git attribute definitions. |
| `.gitignore` | File | Version control ignore list. |
| `.gitleaks.toml` | File | Secret scanning rules. |
| `.pre-commit-config.yaml` | File | Pre-commit hook definitions. |
| `node_modules` | Directory | Installed Node.js dependencies (summarised in manifest). |

## Archives & Releases

| Path | Type | Summary |
| --- | --- | --- |
| `archive` | Directory | Historical reference material. |
| `snapshot` | Directory | Frozen snapshots of important repo states. |
| `proposed-patches` | Directory | Work-in-progress patches and examples. |
| `release-20251105-223624` | Directory | Captured release artefact bundle. |
| `nssm-2.24` | Directory | Bundled NSSM utility. |
| `nssm-2.24.zip` | File | Original NSSM archive. |

## Using the Manifest

For a programmatic view—including nested directory listings—consult
[`manifest.json`](manifest.json).  Regenerate it after restructuring the repo to keep this overview, the
manifest, and the codebase perfectly aligned.
