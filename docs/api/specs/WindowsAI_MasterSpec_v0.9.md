# Windows AI — Master Spec v0.9 (Enterprise Hardening)
Date: 2025-08-03

Purpose: add SSO, policy, observability+, and secure packaging.

Highlights
- SSO via Microsoft Entra ID (MSAL): device code, interactive, IWA
- Policy: ADMX templates (egress, sources, telemetry, updates)
- Security: BitLocker guidance; AppLocker/WDAC samples; signed installers
- Observability+: OTLP exporter; ETW provider + Event Log channel
- Admin Mode + offline update bundles
