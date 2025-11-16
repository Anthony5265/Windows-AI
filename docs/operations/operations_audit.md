# Operations Readiness Audit

**Version:** 2025-11-15  
**Owner:** Operations & Reliability Working Group  
**Cadence:** Monthly (or before every release candidate)

This document replaces the placeholder text that previously mirrored items from the architecture roadmap. It defines how to evaluate Windows-AI’s operational readiness across infrastructure, automation, observability, and recovery workflows.

---

## 1. Scope & Objectives
- **Systems in scope:** FastAPI backend, automation engine (folder watchers + scheduler), Electron GUI, tray app, watchdog, mesh/iot services, plugin ecosystem, release packaging scripts.
- **Objectives:** Verify that each system can be deployed, monitored, supported, and recovered with acceptable risk.
- **Outputs:** Audit scorecard (Section 5), remediation tickets, dashboard updates, and sign-off recorded in the sprint ledger.

---

## 2. Control Checklist

| Control Area | Checks | Evidence |
|--------------|--------|----------|
| **Configuration Management** | Central config repo? Versioned defaults? Secrets separation? | `config/`, `.env.example`, console screenshots |
| **Deployability** | Reproducible build (scripts/start-*.sh/.bat), container and installer parity, watchdog coverage | Build logs, CI artifacts |
| **Observability** | Logging enabled for every service? Metrics export? Alert hooks? | `windows_ai/system_monitor.py`, `docs/observability/*`, Grafana snapshot |
| **Automation & Jobs** | Folder watchers defined? Scheduler tasks persisted? Backoff/retry logic? | `watchers.yaml`, `scheduler.json`, pytest outputs |
| **Security & Access** | Least-privilege service users? Secrets encrypted? Audit logging? | `docs/security/*`, key rotation scripts |
| **Incident Response** | Runbook currency? On-call rotation defined? Escalation timings? | `docs/operations/incident-playbook.md`, calendar invites |
| **Backup & Recovery** | Data directories backed up? Restore tested in last 60 days? | `docs/operations/backup-strategy.md`, recovery log |
| **Change Management** | Release checklist? Rollback plan? Communication template? | `docs/operations/release-calendar.md`, `rollback/` scripts |

Each check is marked **Pass**, **Partial**, or **Fail** with notes and links.

---

## 3. Maturity Scoring
- **Pass (Green):** Evidence attached, automation in place.
- **Partial (Yellow):** Manual procedure exists but lacks automation or documentation.
- **Fail (Red):** Control missing, obsolete, or untested in the past release cycle.

Overall readiness score = (# Pass) / (total controls). Thresholds:
- ≥0.85 → Release may proceed (with minor follow-ups).
- 0.7–0.85 → Release requires risk review.
- <0.7 → Block release until remediation completed.

---

## 4. Audit Workflow
1. **Kickoff:** Ops lead reviews this checklist at sprint planning.
2. **Evidence collection:** Owners attach links/screenshots/logs in the audit tracker (Notion or markdown table).
3. **Gap analysis:** Missing items become GitHub issues tagged `ops-gap`.
4. **Review meeting:** 30-minute session with backend + platform owners; finalize score.
5. **Sign-off:** Update `WINDOWS_AI_UNIFIED_ROADMAP.md` Sprint Ledger and archive evidence bundle under `docs/operations/audit-history/YYYY-MM.md`.

---

## 5. Scorecard Template

| Control | Status | Owner | Notes/Links |
|---------|--------|-------|-------------|
| Deployability scripts | Pending | Release Eng | e.g., `build-release.sh` log |
| Watchdog coverage | Pending | Platform | `watchdog.py` metrics |
| Observability alerts | Pending | Ops | Grafana dashboard link |
| Backup validation | Pending | Ops | Restore log |
| Incident playbook | Pending | Support | `docs/operations/incident-playbook.md` |
| Security review | Pending | Security | Audit summary |

Copy this table into each monthly audit record.

---

## 6. Tooling & Dependencies
- **Dashboards:** Future `operations_dashboard.md` will describe Prometheus/Grafana layouts that feed this audit.
- **Playbooks:** Refer to `operations_playbook.md` (to be authored) for mitigation steps.
- **Inspector automation:** TODO file `operations_inspector.py` (future) will run these checks headlessly.

---

## 7. Next Steps
1. Populate the November 2025 scorecard with current evidence.
2. Draft dashboard/playbook/scorecard docs so this audit can reference them.
3. Automate evidence collection via CLI (`scripts/ops/audit.py`, future work).

Refer to Section 5 of the unified roadmap for the remaining governance artefacts.
