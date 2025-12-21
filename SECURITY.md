# Security Policy

We align with the docs in `docs/security.md`, `docs/security_privacy.md`, and `docs/SECURITY_ENCRYPTION.md`.

## Reporting
Please report vulnerabilities via the project maintainers. Avoid filing public issues with sensitive details.

## Hardening
- Follow least-privilege defaults for permissions and environment variables.
- Enable the watchdog (`watchdog.py`) in production deployments.
- Review rollback hooks (`security/rollback.py`) and recovery steps in `docs/rollback.md`.
