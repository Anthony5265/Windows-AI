# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.5.x   | :white_check_mark: |
| < 0.5   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### 1. Do Not Open a Public Issue

Please **do not** create a public GitHub issue for security vulnerabilities.

### 2. Use GitHub Security Advisories

Report via GitHub Security Advisories:
https://github.com/yourorg/Windows-AI/security/advisories/new

Or email: **security@windows-ai.example.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### 3. Response Timeline

- **24 hours**: Initial acknowledgment
- **72 hours**: Preliminary assessment
- **7 days**: Detailed response with fix timeline

### 4. Disclosure Policy

- We will work with you to understand and fix the issue
- We request a 90-day embargo before public disclosure
- We will credit you in the security advisory (unless you prefer anonymity)

## Security Best Practices

### For Users

**1. Keep Windows AI Updated**
```
Settings → Updates → Check for Updates
Enable auto-updates for security patches
```

**2. Use Signed Installers Only**
- Download only from official GitHub Releases
- Verify digital signatures before installing
- Never run unsigned installers

**3. Protect API Access**
- Windows AI listens on localhost:8010 by default
- Do not expose this port to the internet
- Use firewall rules to block external access

**4. Review Plugin Permissions**
- Only install plugins from trusted sources
- Review plugin code before installation
- Check requested permissions

**5. Secure Configuration Files**
```
Location: %APPDATA%\WindowsAI\config.json
- Do not store API keys in plain text
- Set proper file permissions
- Exclude from cloud backup if sensitive
```

### For Developers

**1. Code Signing**
- Sign all installer executables
- Use valid certificates from trusted CAs
- Timestamp signatures for long-term validity

**2. Input Validation**
```python
# Always validate and sanitize user inputs
def execute_command(user_input):
    safe_input = sanitize(user_input)
    if not validate(safe_input):
        raise ValueError("Invalid input")
    return process(safe_input)
```

**3. Secure File Operations**
```python
# Prevent path traversal
from pathlib import Path

def safe_file_access(user_path):
    safe_path = Path(user_path).resolve()
    allowed_dir = Path("C:\\allowed\\directory").resolve()
    if not safe_path.is_relative_to(allowed_dir):
        raise ValueError("Access denied")
    return safe_path
```

## Known Security Considerations

### Local API Access

**Risk:** Windows AI backend runs on localhost:8010 without authentication.

**Mitigation:**
- Only accessible from localhost by default
- Firewall blocks external access
- Future versions will add API key authentication

### Plugin System

**Risk:** Plugins run with user privileges and can access file system.

**Mitigation:**
- Plugin permissions system
- User approval before installation
- Sandboxing in future versions

### Auto-Update System

**Risk:** Update mechanism could be compromised.

**Mitigation:**
- Updates signed with code signing certificate
- Signature verification before installation
- HTTPS for update downloads
- Checksum validation

## Security Features Roadmap

### Planned (v0.6.0)
- [ ] API key authentication
- [ ] Chat history encryption at rest
- [ ] Plugin sandboxing
- [ ] Rate limiting on API endpoints

## Security Contact

- **GitHub Security Advisories**: https://github.com/yourorg/Windows-AI/security/advisories
- **Email:** security@windows-ai.example.com

## Hall of Fame

Thank you to security researchers who have responsibly disclosed vulnerabilities:

*None yet - be the first!*

---

*Last updated: 2025-01-10 | Windows AI v0.5.0*
