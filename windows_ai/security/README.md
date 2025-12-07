# Windows AI Security Module

## ⚠️ Important: Security is OFF by Default

This folder contains Windows AI's security infrastructure, but **all features are OPTIONAL and disabled by default**.

## Default Behavior

- **No sandboxing** - Plugins have full system access
- **No authentication** - API accessible without keys
- **No permissions** - No access control enforced
- **No guardrails** - No content filtering

This provides **maximum freedom** for local development and personal use.

## Files in This Module

| File | Purpose | Default State |
|------|---------|---------------|
| `sandbox.py` | Execution isolation & resource limits | OFF (SandboxLevel.NONE) |
| `permissions.py` | Role-based access control (RBAC) | OFF (not enforced) |
| `guardrails.py` | Content filtering & policy enforcement | OFF (no filtering) |
| `auth.py` | Authentication & authorization | OFF (allows all if no API key) |
| `credential_vault.py` | Secure credential storage | Available but not required |
| `security_scanning.py` | Security vulnerability scanning | Available but not active |

## How to Enable Security

Edit `windows_ai/config/default.yaml`:

```yaml
security:
  sandbox_enabled: true
  sandbox_level: "standard"
  auth_enabled: true
  permissions_enabled: true
  guardrails_enabled: true
```

Or set environment variables:

```bash
set WINDOWS_AI_API_KEY=your-secure-key
set WINDOWS_AI_SANDBOX_ENABLED=true
```

## When to Enable Security

✅ Enable when:

- Deploying to servers or networks
- Multiple users access the system
- Running untrusted third-party plugins
- Compliance requirements (GDPR, HIPAA, etc.)
- Need audit trails

❌ Keep OFF when:

- Local development on your personal machine
- You control all code and plugins
- Maximum flexibility is priority
- Single-user environment

## Documentation

See `docs/SECURITY_CONFIGURATION.md` for comprehensive security guide.

## Philosophy

Windows AI follows **"Freedom First"** design:

1. **Local Development = Full Freedom** (default)
2. **Production Deployment = Enable Security** (opt-in)
3. **You Choose Your Security Posture** (not imposed)

The security infrastructure is **here when you need it**, but **out of your way when you don't**.
