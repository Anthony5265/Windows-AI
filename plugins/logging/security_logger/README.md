# Security Logger

Tamper-evident audit log focused on authentication, authorization,
and other security-sensitive events. Each record is chained via a
SHA-256 digest so log tampering can be detected during verification.

## Capabilities

- Structured event payloads with actor/target metadata
- Automatic hash-chaining for integrity verification
- Helper for raising instant alerts (`flag_alert`)
- JSON Lines output for ingestion into SIEM pipelines

```python
from plugins.logging.security_logger.security_logger import SecurityLogger

sec = SecurityLogger(log_dir="logs/security")
sec.log_event("token_issued", actor="svc_auth", target="user123")
assert sec.verify_chain()
```
