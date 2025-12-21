# API Reference (Minimal)

## Phase status endpoints
- GET /phases/status — returns overall completion and per-phase details.
- GET /phases/status/{id} — returns a single phase summary.

## Core agent
- FastAPI entrypoint: `windows_ai/main.py`
- Plugin loading: `windows_ai/plugins/loader.py`, registry: `windows_ai/plugins/registry.py`

## Operations
- Update server: `update-server/server.py`, manifest: `update-server/manifest.json`
- Watchdog entry: `watchdog.py`

## SDK and distribution
- OpenAPI spec: `openapi/windows-ai.yaml`
- CLI package: `windows-ai-agent/`
- SDK roots: `sdk/`
