# Operations Readiness Dashboard

**Version:** 2025-11-15  
**Owner:** Operations & Reliability Working Group  
**Cadence:** Updated continuously; formal review before every audit + release candidate

This dashboard translates the audit checklist into live telemetry so the team can
see deployment, monitoring, and recovery posture at a glance. It consumes the
same data sources referenced in `operations_audit.md` and exposes drill-down
links to the relevant runbooks.

---

## 1. Objectives & Success Criteria
- **Real-time awareness:** Surface health of core services (backend, GUI, tray, automation engine, watchdog) and key background jobs.
- **Evidence for audits:** Provide screenshot/export that proves controls are working (deployability, observability, automation, security, incident readiness).
- **Alert triage:** Route threshold breaches to on-call channels with links to runbooks and mitigation actions.
- **Trend analysis:** Track SLOs (availability, restart counts, queue delays) across releases to detect regressions early.

Success Criteria:
1. All panels backed by automated metrics or log queries (no manual data entry).
2. Exportable JSON/screenshot stored with monthly audit evidence.
3. Every widget links to at least one playbook/runbook when remediation is required.

---

## 2. Data Sources & Collection

| Source | Metric/Log | Collection Method | Notes |
|--------|------------|-------------------|-------|
| **Prometheus / node-exporter** | CPU, memory, disk for Windows-AI host | `prometheus.yml` scrape | Windows exporters installed via `scripts/ops/windows_exporter_setup.ps1` |
| **FastAPI backend** | Request rate, error rate, latency | Instrumentation via `windows_ai/main.py` + `prometheus_client` middleware | Emits `/metrics` endpoint |
| **Watchdog service** | Restart counts, health probes | `watchdog.py` log file + custom counter exported via StatsD | Alerts when restart loop > 3/hr |
| **Automation engine** | Folder watcher status, scheduler queue depth | `automation/status.json` written every minute | Ship to Loki via `promtail` |
| **Windows Event Log** | Service crashes, permission issues | Collected via nxlog -> Loki | Use saved queries for "Windows-AI" source |
| **Deployment pipeline** | Last build hash, artifact checksum | `build-release.sh` writes to `artifacts/build-info.json` | Displayed in dashboard header |
| **Backup jobs** | Success timestamp, duration | `scripts/ops/backup.ps1` posts to InfluxDB | Compare vs RPO target (24h) |
| **Incident management** | Open incidents, MTTR | Lightweight Notion table exported as CSV daily | Used for historical trend panel |

---

## 3. Dashboard Layout

| Row | Panel | Description | Thresholds / Alerts |
|-----|-------|-------------|---------------------|
| Header | Release Overview | Build hash, config profile, audit score, on-call rotation | Turns red if audit score < 0.85 or on-call unset |
| 1 | Service Availability | Uptime % for backend/GUI/tray/watchdog (rolling 24h) | Alert < 99% or 3 consecutive restart events |
| 1 | API Health | P99 latency + error rate per endpoint | Alert if P99 > 3s or error rate > 2% |
| 2 | Resource Utilization | CPU, memory, disk usage stacked by component | Warn > 80% sustained for 10m |
| 2 | Automation Jobs | Folder watcher heartbeat + scheduler backlog | Alert if heartbeat stale > 2m or backlog > 50 jobs |
| 3 | Backup & Recovery | Last successful backup timestamp, restore test result | Alert if backup > 24h old or last restore > 60d |
| 3 | Security & Access | Failed auth attempts, privilege escalations from Windows logs | Alert on >5 failed auth/min or new admin account |
| 4 | Incident Timeline | Open incidents, MTTR trend, mitigation status | Highlight unresolved incidents > 24h |
| 4 | Change Management | Upcoming releases, rollback readiness checklist | Alert if rollback artifacts missing or release overdue |

Each panel links to the appropriate runbook:
- `/docs/operations/incident-playbook.md`
- `/docs/operations/maintenance-calendar.md`
- `/docs/security/*`
- `/docs/operations/operations_audit.md` (scorecard source)

---

## 4. Alerting & Notification Channels

| Channel | Purpose | Trigger Source |
|---------|---------|----------------|
| **Teams: #ops-alerts** | High-priority service incidents | Grafana alert rules for availability, automation backlog, security anomalies |
| **Email: ops@windows-ai.local** | Daily summary & audit evidence | Scheduled Grafana report (PDF + CSV) |
| **PagerDuty** | Critical out-of-hours alerts | Prometheus Alertmanager forwarder |
| **Notion Task Board** | Remediation tracking | Ops engineer copies alert ID + context to task card |

Alert rules live in `infrastructure/monitoring/alertmanager.yml`. Each rule includes:
- Owner tag (release-eng, platform, automation, security)
- Runbook URL
- Severity (info/warn/critical)

---

## 5. Implementation Steps
1. **Provision monitoring stack** – Deploy Prometheus + Grafana (Docker compose under `infrastructure/monitoring/`).
2. **Instrument services** – Enable metrics middleware in FastAPI, add StatsD counters for watchdog + automation, configure exporters.
3. **Configure data pipelines** – Promtail/nxlog for Windows Event Logs, Notion CSV sync script (`scripts/ops/notion_export.py`), backup job webhooks.
4. **Create dashboard JSON** – Grafana folder `operations/windows-ai.json`; versioned in `infrastructure/monitoring/grafana_dashboards/`.
5. **Automate evidence export** – Grafana report scheduled daily to `docs/operations/dashboard-history/YYYY-MM-DD.pdf`.
6. **Wire alerts** – Define rules in Alertmanager, integrate with Teams webhooks + PagerDuty integration key.
7. **Document ownership** – Update `docs/operations/operations_registry.md` with on-call + dashboard maintainer.

---

## 6. Maintenance & Review Cadence
- **Daily:** Check for red panels, ensure reports delivered.
- **Weekly:** Rotate on-call, verify alert recipients, confirm backup freshness.
- **Monthly:** Include dashboard screenshot + JSON export in the audit evidence bundle.
- **After incidents:** Annotate Grafana (e.g., add markers for outages) to preserve learning context.
- **After releases:** Update release overview widget with new build hash and config profile.

Change requests (new panels, thresholds) go through the Ops Working Group and should be noted in the sprint ledger.

---

## 7. Open Work Items
- Automate ingestion of Notion incident data (currently manual export).
- Add synthetic transaction checks for GUI/tray to catch UX regressions.
- Integrate future `operations_inspector.py` to set dashboard annotations when automated checks run.
- Expand security panel once `docs/security/security_dashboard.md` is authored to avoid duplication.

Once these items are addressed, update the Rolling Backlog in `WINDOWS_AI_UNIFIED_ROADMAP.md`.
