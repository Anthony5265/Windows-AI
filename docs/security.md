# Security Policies

The project bundles a lightweight `security` package providing several safety
mechanisms used across the system:

- **Permission management** – the `PermissionManager` records grants for
  plugins and core tools.  Both the installer and Control Center invoke it to
  prompt users before accessing the network or other sensitive resources.
- **Encryption helpers** – `security.crypto.encrypt` and
  `security.crypto.decrypt` offer simple symmetric encryption for small pieces
  of data.
- **Audit logging** – all permission decisions are written via
  `AuditLogger` so they can be reviewed later from the Control Center.
- **Rollback hooks** – the new `RollbackManager` lets components register
  cleanup callbacks that execute if an operation needs to be undone.

These utilities are intentionally minimal and serve as placeholders for more
robust security controls in production deployments.
