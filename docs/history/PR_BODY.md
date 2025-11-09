# Hardening: CI, OpenAPI refs, and Codex ergonomics

**Date:** 2025-08-03

## What changed
- **CI:** Added two workflows
  - `ci-python-node.yml` — runs Python tests (pytest) and Node tests for `apps/actions-api` on Ubuntu.
  - `ci-windows-powershell.yml` — runs PSScriptAnalyzer and a safe smoke load of `install/*.ps1` on Windows.
  - **OpenAPI:** Fixed `$ref` paths in `openapi/windows-ai.yaml` to point at
    `codex/SCHEMAS/*` (so schema resolution works from the repo root).
  - **Repo convenience:** Added root `requirements.txt` for Python services and a
    minimal `package.json` with workspaces so local tooling understands the repo
    shape.
- **Codex helper:** Added `codex/README_Codex.md` with the exact session bootstrap prompt and expectations.

## Why
- Avoids Codex "can't find schema / manifest" errors.
- Ensures PRs are gated on **both** Python and Node tests.
- Validates PowerShell scripts on a **Windows** runner and reports style/syntax issues with PSScriptAnalyzer.

## How to apply locally
```bash
# From your repo root
unzip WindowsAI_PR_All.zip -d .
git checkout -b chore/codex-hardening
git add -A
git commit -m "chore: CI + OpenAPI refs + Codex ergonomics"
git push -u origin chore/codex-hardening
# open a PR from the pushed branch
```

## After merge
- Codex can start from `codex/manifest.json` and follow `STATE.json` without path issues.
- CI will run on PRs and main branch pushes.
