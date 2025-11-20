# Compliance Logger

Tracks the outcome of security/compliance controls together with remediation
exceptions so Windows-AI can produce SOC2/ISO-style evidence on demand.

## Features
- Persist every control validation with owner, result, and evidence references.
- Capture remediation exceptions with due dates and owners.
- Generate quick audit summaries for a given period.
- Purge historical entries automatically based on `retention_days`.

## Usage
```python
from datetime import datetime, timedelta
from plugins.logging.compliance_logger.compliance_logger import (
    ComplianceLogger,
    ControlResult,
)

logger = ComplianceLogger()
logger.record_control(
    ControlResult(
        control_id="AC-01",
        status="pass",
        owner="security-team",
        evidence_path="evidence/ac-01.pdf",
    )
)

logger.record_exception(
    control_id="DP-04",
    description="Missing data retention job",
    severity="high",
    remediation_owner="data-platform",
    remediation_due=datetime.utcnow() + timedelta(days=7),
)

report = logger.generate_audit_report(period_days=30)
```

See `compliance_logger.py` for the full API surface.
