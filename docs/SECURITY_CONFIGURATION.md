# Windows AI Security Configuration

## ⚠️ Security is OPTIONAL and OFF by Default

Windows AI follows a **"Freedom First"** philosophy - security features are **opt-in, not enforced**. This gives you maximum flexibility and control.

## Default Security Posture

### 🔓 What's OFF by Default

1. **Sandboxing** - Plugins have full system access
2. **Authentication** - No API keys required
3. **Authorization** - No permission checks enforced
4. **Content Guardrails** - No content filtering
5. **Rate Limiting** - No request throttling
6. **Audit Logging** - No access logging
7. **Compliance Enforcement** - No GDPR/HIPAA restrictions

### ✅ This Means You Can

- ✅ Run any plugin without restrictions
- ✅ Access all API endpoints without authentication
- ✅ Read/write/delete any files
- ✅ Spawn processes freely
- ✅ Make unlimited API calls
- ✅ Use any LLM model
- ✅ Execute any command
- ✅ Access registry and system resources
- ✅ Have full network access

## Why This Design?

Windows AI is a **local development tool** designed for:

- **Developers** who need full system access
- **Power users** who want maximum control
- **Experimentation** without restrictions
- **Personal productivity** tools
- **Learning and prototyping** environments

If you're running Windows AI on your personal machine for your own use, the default permissive mode is perfect. You own your machine, you control your data, you decide what to run.

## When to Enable Security

Consider enabling security features if you:

### 🛡️ Enable Authentication When

- Exposing Windows AI to a network
- Multiple users share the same installation
- Running on a server or cloud instance
- Need audit trails for compliance

### 🔒 Enable Sandboxing When

- Running untrusted third-party plugins
- Experimenting with experimental AI features
- Want resource limits (CPU/memory/disk)
- Need to protect sensitive system areas

### 🚦 Enable Content Guardrails When

- Interacting with public-facing systems
- Need content moderation for compliance
- Want to filter harmful/inappropriate content
- Building applications for general audiences

### 👥 Enable Permissions When

- Multiple users with different access levels
- Implementing role-based access control (RBAC)
- Need fine-grained resource access control
- Building enterprise/organizational tools

## How to Enable Security

### Option 1: Edit Configuration File

Edit `windows_ai/config/default.yaml`:

```yaml
# Security Settings
security:
  # Enable sandbox
  sandbox_enabled: true
  sandbox_level: "standard"  # none, minimal, standard, strict, maximum

  # Enable content guardrails
  guardrails_enabled: true
  guardrails_level: "standard"  # off, minimal, standard, strict

  # Authentication
  auth_enabled: true
  require_auth: true

  # Permissions
  permissions_enabled: true
  default_role: "user"  # guest, user, power_user, admin
```

### Option 2: Environment Variables

Set environment variables to enable features:

```bash
# Enable authentication
set WINDOWS_AI_API_KEY=your-secure-api-key-here

# Enable sandbox (Windows)
set WINDOWS_AI_SANDBOX_ENABLED=true
set WINDOWS_AI_SANDBOX_LEVEL=standard

# Enable guardrails
set WINDOWS_AI_GUARDRAILS_ENABLED=true
set WINDOWS_AI_GUARDRAILS_LEVEL=strict
```

### Option 3: GUI Settings

1. Launch Windows AI Control Center
2. Go to Settings → Security
3. Toggle features you want to enable
4. Configure security levels
5. Save configuration

## Security Levels Explained

### Sandbox Levels

| Level | Description | File Access | Network | Process Spawn |
|-------|-------------|-------------|---------|---------------|
| **none** | No restrictions (default) | Full | Allowed | Allowed |
| **minimal** | Basic protection | Full | Allowed | Allowed |
| **standard** | Balanced security | Limited | Allowed | Blocked |
| **strict** | High security | Read-only | Allowed | Blocked |
| **maximum** | Maximum isolation | Read-only | Blocked | Blocked |

### Guardrail Levels

| Level | Description | Content Filtering | Policy Enforcement |
|-------|-------------|-------------------|-------------------|
| **off** | No filtering (default) | None | None |
| **minimal** | Basic harmful content | Blocked | Basic |
| **standard** | Common harmful patterns | Filtered | Moderate |
| **strict** | Aggressive filtering | Strict | Comprehensive |

### Permission Roles

| Role | Description | API Access | File Access | System Access |
|------|-------------|------------|-------------|---------------|
| **admin** | Full access (default) | Full | Full | Full |
| **power_user** | Advanced access | Most | Write | Limited |
| **user** | Standard access | Standard | Read/Write | None |
| **guest** | Minimal access | Read-only | Read-only | None |

## Security Feature Matrix

| Feature | Default | How to Enable | Impact |
|---------|---------|---------------|--------|
| Authentication | OFF | Set `WINDOWS_AI_API_KEY` | Requires API key for all requests |
| Sandbox | OFF | Set `sandbox_enabled: true` | Restricts plugin system access |
| Permissions | OFF | Set `permissions_enabled: true` | Enforces role-based access |
| Guardrails | OFF | Set `guardrails_enabled: true` | Filters content |
| Rate Limiting | OFF | Set `rate_limit: N` | Limits requests per minute |
| Audit Logging | OFF | Set `audit_enabled: true` | Logs all API access |
| HTTPS/TLS | OFF | Configure SSL cert | Encrypts network traffic |

## Best Practices

### For Local Development (Default)

```yaml
security:
  sandbox_enabled: false
  auth_enabled: false
  permissions_enabled: false
  guardrails_enabled: false
```

**Result:** Maximum freedom, fastest development, full system access

### For Shared Development Server

```yaml
security:
  sandbox_enabled: true
  sandbox_level: "minimal"
  auth_enabled: true
  permissions_enabled: true
  default_role: "user"
  guardrails_enabled: false
```

**Result:** Basic protection, user isolation, still flexible

### For Production Deployment

```yaml
security:
  sandbox_enabled: true
  sandbox_level: "strict"
  auth_enabled: true
  require_auth: true
  permissions_enabled: true
  default_role: "guest"
  guardrails_enabled: true
  guardrails_level: "standard"
```

**Result:** Secure, controlled, compliant

### For Public-Facing Service

```yaml
security:
  sandbox_enabled: true
  sandbox_level: "maximum"
  auth_enabled: true
  require_auth: true
  permissions_enabled: true
  default_role: "guest"
  guardrails_enabled: true
  guardrails_level: "strict"
  rate_limit: 60
  audit_enabled: true
```

**Result:** Maximum security, full audit trail, rate limited

## Security Infrastructure

Windows AI includes comprehensive security infrastructure that's available when you need it:

### Available Security Components

1. **Sandbox System** (`windows_ai/security/sandbox.py`)
   - RestrictedPython-based execution isolation
   - Resource limits (CPU, memory, disk)
   - File system access control
   - Network access control
   - Process spawning control

2. **Permission System** (`windows_ai/security/permissions.py`)
   - Role-based access control (RBAC)
   - Fine-grained resource permissions
   - Permission inheritance
   - User/group management
   - 5-level permission model (NONE/READ/WRITE/EXECUTE/ADMIN)

3. **Authentication System** (`windows_ai/api/auth.py`)
   - API key authentication
   - Bearer token authentication
   - Session management
   - User management

4. **Content Guardrails** (`windows_ai/security/guardrails.py`)
   - Content filtering
   - Policy enforcement
   - PII detection
   - Harmful content blocking
   - Compliance checks

5. **Compliance Plugins** (39 plugins available)
   - GDPR compliance
   - HIPAA compliance
   - SOC2 compliance
   - ADA compliance
   - CCPA compliance
   - COPPA compliance
   - And more...

All of these are **available but not active** by default. Enable what you need, when you need it.

## FAQ

### Q: Is it safe to run Windows AI with default settings?

**A:** Yes! On your personal machine, the default permissive mode is safe. You're running local code you control. Just like running Python scripts, Node.js apps, or any other development tool.

### Q: Should I enable security for production?

**A:** Yes! If deploying to servers, networks, or multi-user environments, enable appropriate security features. See "For Production Deployment" above.

### Q: Can I enable just authentication without sandboxing?

**A:** Absolutely! All security features are independent. Mix and match as needed.

### Q: Will enabling security slow down Windows AI?

**A:** Sandboxing adds minimal overhead. Authentication/permissions add negligible latency. Most security features have < 1% performance impact.

### Q: Can I programmatically control security settings?

**A:** Yes! Use the API to enable/disable features at runtime, create custom security policies, and implement your own security logic.

### Q: Is there logging for security events?

**A:** Yes! When `audit_enabled: true`, all authentication attempts, permission checks, and security violations are logged.

### Q: What about plugin security?

**A:** By default, plugins have full system access. Enable `sandbox_enabled: true` to restrict plugins to sandboxed environments with resource limits.

## Summary

Windows AI's "Freedom First" approach means:

✅ **Default:** Full freedom, no restrictions, maximum productivity
🛡️ **Optional:** Comprehensive security available when you need it
🔧 **Flexible:** Enable only the features you want
📈 **Scalable:** From local dev to secure enterprise deployments

**You control your security posture. Not the other way around.**

For more information:

- Configuration reference: `docs/configuration.md`
- API security: `docs/api-security.md`
- Plugin development: `docs/plugin-security.md`
