# Windows-AI Cloud Sync - Security & Encryption Architecture

## Executive Summary

Windows-AI Cloud Sync implements a **zero-knowledge** end-to-end encryption architecture where the sync server never has access to your plaintext data. All encryption and decryption happens exclusively on client devices using industry-standard cryptographic libraries.

**Key Security Guarantees**:
- ✅ Server cannot decrypt your data (zero-knowledge)
- ✅ Transport layer security (HTTPS/TLS)
- ✅ Authenticated encryption (integrity + confidentiality)
- ✅ Password-based key derivation (Argon2id)
- ✅ Forward secrecy ready
- ✅ Audit trail capability

## Table of Contents

- [Threat Model](#threat-model)
- [Cryptographic Primitives](#cryptographic-primitives)
- [Key Derivation](#key-derivation)
- [Encryption Process](#encryption-process)
- [Zero-Knowledge Architecture](#zero-knowledge-architecture)
- [Key Management](#key-management)
- [Attack Vectors & Mitigations](#attack-vectors--mitigations)
- [Security Audit](#security-audit)
- [Compliance](#compliance)

## Threat Model

### What We Protect Against

| Threat | Protection |
|--------|-----------|
| **Server Compromise** | E2E encryption (server sees only encrypted data) |
| **Network Sniffing** | TLS/HTTPS + encrypted payload |
| **Man-in-the-Middle** | TLS + certificate pinning ready |
| **Data Tampering** | HMAC authentication tags |
| **Password Guessing** | Argon2id with high cost parameters |
| **Weak Keys** | CSPRNG (cryptographically secure random) |
| **Replay Attacks** | Timestamps + nonces |

### Out of Scope (User Responsibility)

- **Device Compromise**: If attacker has root access to your device, they can access decrypted data
- **Password Sharing**: Using the same password on multiple untrusted services
- **Phishing**: Giving password to fake login pages
- **Physical Access**: Unencrypted devices left unlocked

## Cryptographic Primitives

### Primary: NaCl (libsodium)

When PyNaCl is available, we use **libsodium** which provides:

```python
# Authenticated Encryption
SecretBox = XSalsa20-Poly1305
- Cipher: XSalsa20 (stream cipher)
- MAC: Poly1305 (authenticator)
- Key: 256-bit
- Nonce: 192-bit (generated randomly)

# Key Derivation
Argon2id (Password Hashing Competition winner)
- Operations: OPSLIMIT_MODERATE (default)
- Memory: MEMLIMIT_MODERATE (default)
- Parallelism: Optimized by libsodium
- Salt: 128-bit (random)
```

**Why NaCl?**
- ✅ Audited and proven secure
- ✅ Misuse-resistant API (hard to use wrong)
- ✅ Constant-time operations (timing attack resistant)
- ✅ Industry standard (used by Signal, WireGuard, etc.)

### Fallback: Python Standard Library

When PyNaCl is unavailable, we use:

```python
# Key Derivation
PBKDF2-HMAC-SHA256
- Iterations: 100,000
- Salt: 128-bit (random)
- Key length: 256-bit

# Encryption
HMAC-based stream cipher
- Key stream: HMAC-SHA256 (counter mode)
- MAC: HMAC-SHA256
- IV: 128-bit (random)
- Key: 256-bit
```

**Note**: Fallback is secure but slower than NaCl. Install PyNaCl for best performance.

## Key Derivation

### Password to Encryption Key

```python
def derive_key_from_password(password, salt=None):
    """
    Derive 256-bit encryption key from user password using Argon2id

    Args:
        password: User's password (string)
        salt: 128-bit salt (random if not provided)

    Returns:
        (key, salt) tuple
    """
    if salt is None:
        salt = random_bytes(16)  # 128-bit

    # Argon2id parameters (MODERATE)
    ops_limit = 3  # ~2-3 seconds on modern CPU
    mem_limit = 67108864  # 64 MB

    key = argon2id.kdf(
        size=32,  # 256-bit key
        password=password.encode('utf-8'),
        salt=salt,
        opslimit=ops_limit,
        memlimit=mem_limit
    )

    return key, salt
```

### Why Argon2id?

**Argon2id** won the Password Hashing Competition (2015) and is recommended by:
- OWASP
- NIST
- libsodium
- Internet Engineering Task Force (IETF)

**Properties**:
- **Memory-hard**: Requires significant RAM, making GPU/ASIC attacks expensive
- **Time-hard**: Requires significant computation time
- **Side-channel resistant**: Constant-time execution
- **Configurable**: Can increase cost as hardware improves

**Cost Parameters**:
```
OPSLIMIT_INTERACTIVE: 2 ops, ~0.5s (login forms)
OPSLIMIT_MODERATE: 3 ops, ~2s (default for sync)
OPSLIMIT_SENSITIVE: 4 ops, ~10s (high-security scenarios)
```

## Encryption Process

### Data Encryption Flow

```
┌──────────────┐
│  Plain Data  │
└──────┬───────┘
       │
       ▼
┌────────────────────────┐
│  JSON Serialize        │
└──────┬─────────────────┘
       │
       ▼
┌────────────────────────┐
│  Compress (optional)   │
└──────┬─────────────────┘
       │
       ▼
┌────────────────────────┐
│  Generate Random       │
│  Nonce (192-bit)       │
└──────┬─────────────────┘
       │
       ▼
┌────────────────────────┐
│  XSalsa20 Encrypt      │
│  + Poly1305 MAC        │
└──────┬─────────────────┘
       │
       ▼
┌────────────────────────┐
│  Nonce + MAC +         │
│  Ciphertext            │
└──────┬─────────────────┘
       │
       ▼
┌────────────────────────┐
│  Base64 Encode         │
│  (for transport)       │
└──────┬─────────────────┘
       │
       ▼
┌──────────────┐
│  Encrypted   │
│  Payload     │
└──────────────┘
```

### Code Example

```python
from windows_ai.cloud_sync.encryption import SyncEncryption, EncryptionKey

# Initialize encryption
encryption = SyncEncryption()

# Derive key from password
key = encryption.create_key_from_password("user_password_123")

# Encrypt data
plaintext = b"Secret conversation data"
ciphertext = encryption.encrypt_data(plaintext, key)

# Decrypt data
decrypted = encryption.decrypt_data(ciphertext, key)
assert decrypted == plaintext
```

### Encrypted Data Format (NaCl)

```
┌─────────────────────────────────────────────────────┐
│                  Encrypted Blob                     │
├─────────────────────────────────────────────────────┤
│ Nonce (24 bytes)                                    │
├─────────────────────────────────────────────────────┤
│ Poly1305 MAC (16 bytes)                             │
├─────────────────────────────────────────────────────┤
│ XSalsa20 Ciphertext (variable length)               │
└─────────────────────────────────────────────────────┘

Total overhead: 40 bytes
```

## Zero-Knowledge Architecture

### Principle

**Zero-Knowledge** means the server learns nothing about the content of your data beyond:
- How much data you have
- When you last synced
- Which devices you use

The server **CANNOT**:
- ❌ Read your conversations
- ❌ See your settings
- ❌ Decrypt your automations
- ❌ Access your documents
- ❌ Recover your password

### Implementation

```python
# CLIENT SIDE
plaintext = {"title": "Secret Conversation"}

# 1. Encrypt with user's key (derived from password)
encrypted = encryption.encrypt_json(plaintext, user_key)

# 2. Send encrypted data to server
response = requests.post(
    "https://sync.server.com/api/sync/push",
    json={"data": encrypted}  # Server receives encrypted blob
)

# SERVER SIDE
# Server receives:
{
    "data": "i+X8f3k9...encrypted blob...j2K8d==",
    "timestamp": "2025-01-01T00:00:00Z",
    "device_id": "abc123"
}

# Server CANNOT decrypt this data
# Server stores it as-is in database
database.save(encrypted_blob)  # Still encrypted

# OTHER CLIENT
# Pull encrypted data from server
encrypted_blob = server.pull_data()

# Decrypt with user's key (same password)
plaintext = encryption.decrypt_json(encrypted_blob, user_key)
# NOW client can read: {"title": "Secret Conversation"}
```

### Server Never Has Your Key

```
User Password
     ↓
  Argon2id (CLIENT-SIDE ONLY)
     ↓
Encryption Key (256-bit)
     ↓
Encrypt Data (CLIENT-SIDE ONLY)
     ↓
Encrypted Blob → Upload to Server
     ↓
Server stores encrypted blob
     ↓
Server NEVER has encryption key
Server CANNOT derive key (no password)
```

### Authentication vs Encryption

**Important Distinction**:

```python
# JWT Token (for authentication)
auth_token = jwt.sign({"user_id": "abc123"}, server_secret)
# Purpose: Proves you're authorized to access your data
# Server CAN verify this

# Encryption Key (for data encryption)
encryption_key = argon2id(user_password, salt)
# Purpose: Encrypts your actual data
# Server NEVER has this

# Both are separate and serve different purposes
```

## Key Management

### Key Storage

**DO NOT** store encryption keys in:
- ❌ Plain text files
- ❌ Environment variables (on shared systems)
- ❌ Git repositories
- ❌ Cloud config services (without additional encryption)

**DO** store encryption keys:
- ✅ OS keychain (macOS Keychain, Windows Credential Manager)
- ✅ Encrypted configuration files
- ✅ Memory only (derive on each use)
- ✅ Hardware security modules (HSM) for enterprise

### Key Derivation vs Key Storage

**Recommended Approach** (default):
```python
# Derive key from password each time
password = get_password_from_user()  # Or OS keychain
key = encryption.create_key_from_password(password)
```

**Alternative** (requires secure storage):
```python
# Store derived key (encrypted with additional password)
master_password = get_password_from_user()
stored_key = load_encrypted_key_from_secure_storage(master_password)
```

### Key Backup & Recovery

```python
# Create encrypted backup of encryption key
backup_password = "different_strong_password"
backup = encryption.generate_key_backup(
    encryption_key,
    backup_password
)

# backup is a base64 string like:
# "eyJiYWNrdXBfc2FsdCI6IkFCQzEyMy4uLiIsImVuY3J5cHRlZF9rZXkiOiJYWVo0NTYuLi4ifQ=="

# Store this backup in:
# 1. Password manager (recommended)
# 2. Printed QR code in safe
# 3. Encrypted USB drive

# Restore from backup
restored_key = encryption.restore_key_from_backup(
    backup,
    backup_password
)
```

**Warning**: Losing your encryption key means **PERMANENT DATA LOSS**. Always maintain backups.

### Key Rotation

For advanced users, rotate encryption keys periodically:

```python
# 1. Create new key
new_key = encryption.rotate_key(old_key, "new_password")

# 2. Re-encrypt all data
for item in database.get_all_items():
    # Decrypt with old key
    plaintext = encryption.decrypt_data(item.data, old_key)

    # Encrypt with new key
    new_ciphertext = encryption.encrypt_data(plaintext, new_key)

    # Update database
    database.update(item.id, new_ciphertext)

# 3. Upload re-encrypted data
client.sync_all()

# 4. Securely delete old key
del old_key
```

## Attack Vectors & Mitigations

### 1. Password Brute Force

**Attack**: Attacker tries millions of passwords to find yours

**Mitigation**:
- **Argon2id** makes each attempt expensive (2-3 seconds, 64MB RAM)
- At 2 seconds per attempt:
  - 1 million attempts = 23 days
  - 1 billion attempts = 63 years
- Server-side rate limiting (after 5 failed attempts, enforce delays)

**User Defense**: Use strong, unique passwords (20+ characters, mix of types)

### 2. Man-in-the-Middle (MITM)

**Attack**: Attacker intercepts network traffic and reads/modifies data

**Mitigation**:
- **TLS/HTTPS**: All traffic encrypted in transit
- **E2E Encryption**: Even if TLS broken, data still encrypted
- **Certificate Pinning** (optional): Reject untrusted certificates

```python
# Enable certificate pinning
import httpx

client = httpx.Client(
    verify="/path/to/server-cert.pem"  # Only accept this certificate
)
```

### 3. Server Compromise

**Attack**: Attacker gains access to sync server

**What Attacker Gets**:
- ❌ Encrypted blobs (useless without keys)
- ✅ Metadata (user IDs, sync times, data sizes)

**What Attacker CANNOT Get**:
- ❌ Plaintext conversations
- ❌ Passwords
- ❌ Encryption keys

**Mitigation**: Zero-knowledge architecture ensures server compromise doesn't expose data

### 4. Replay Attacks

**Attack**: Attacker records encrypted data and resends it later

**Mitigation**:
- **Timestamps**: Reject old data
- **Nonces**: Detect duplicate messages
- **Version numbers**: Ensure monotonic increases

```python
# Each encrypted message includes timestamp
{
    "data": "encrypted_blob",
    "timestamp": "2025-01-01T12:00:00Z",
    "version": 5
}

# Server rejects if:
# - Timestamp too old (>1 hour)
# - Version <= current version
```

### 5. Side-Channel Attacks

**Attack**: Attacker measures timing, power consumption, or cache behavior

**Mitigation**:
- **Constant-time operations**: NaCl/libsodium uses constant-time crypto
- **No timing dependencies**: Verification always takes same time
- **Memory wiping**: Sensitive data zeroed after use

```python
# Secure comparison (constant-time)
import hmac
hmac.compare_digest(mac1, mac2)  # NOT: mac1 == mac2
```

### 6. Quantum Computing

**Future Threat**: Quantum computers may break current encryption

**Current Status**:
- **Symmetric encryption** (like AES-256, XSalsa20): Still secure
- **Asymmetric encryption** (like RSA, ECDH): Vulnerable to Shor's algorithm

**Our Approach**:
- We use **symmetric encryption** (XSalsa20) which is quantum-resistant
- Key exchange uses passwords (not public key crypto)
- Post-quantum algorithms ready (Kyber, Dilithium) when standardized

## Security Audit

### Audit Trail

Every encryption operation can be logged:

```python
# Create audit hash of encrypted data
audit_hash = encryption.create_audit_hash(encrypted_data)

# Store in audit log
audit_log.append({
    "timestamp": datetime.now(),
    "operation": "encrypt",
    "data_hash": audit_hash,
    "device_id": device_id,
})

# Later, verify data wasn't tampered with
assert encryption.verify_audit_hash(encrypted_data, audit_hash)
```

### Security Testing

Run security tests:

```bash
# Encryption tests
pytest tests/cloud_sync/test_encryption.py -v

# Key tests:
# - test_decrypt_with_wrong_key (should fail)
# - test_decrypt_tampered_data (should fail)
# - test_restore_with_wrong_backup_password (should fail)
# - test_large_data_encryption (performance)
# - test_unicode_json_encryption (encoding)
```

### Penetration Testing Checklist

- [ ] Attempt to decrypt data without key
- [ ] Try brute-force password attacks
- [ ] Intercept and modify network traffic
- [ ] Replay old encrypted messages
- [ ] Tamper with encrypted data
- [ ] Attempt timing attacks on verification
- [ ] Test with weak/known passwords
- [ ] Verify secure memory handling

## Compliance

### GDPR (General Data Protection Regulation)

**Requirements**:
- ✅ **Right to erasure**: Delete user data on request
- ✅ **Data portability**: Export user data in standard format
- ✅ **Encryption**: Protect personal data with encryption
- ✅ **Breach notification**: Notify within 72 hours

**Our Implementation**:
```python
# Delete user data (GDPR Article 17)
server.delete_user_data(user_id)

# Export user data (GDPR Article 20)
data = server.export_user_data(user_id, format="json")

# Encryption (GDPR Article 32)
# Already implemented with E2E encryption

# Breach notification (GDPR Article 33)
# Even if breached, data is encrypted (minimal risk)
```

### CCPA (California Consumer Privacy Act)

**Requirements**:
- ✅ **Right to know**: What data is collected
- ✅ **Right to delete**: Delete personal information
- ✅ **Right to opt-out**: Opt out of data sale

**Our Implementation**:
- **Transparency**: User controls all data
- **No data sale**: We don't sell user data
- **Deletion**: Full data deletion on request

### HIPAA (Health Insurance Portability and Accountability Act)

**Note**: Windows-AI is not HIPAA-certified by default

**If using for health data**:
- [ ] Sign Business Associate Agreement (BAA)
- [ ] Enable access logging
- [ ] Implement additional access controls
- [ ] Regular security audits
- [ ] Incident response plan

**Recommendation**: Consult HIPAA compliance expert if handling health data

## Best Practices Summary

### For Users

1. ✅ **Use strong, unique passwords** (20+ characters)
2. ✅ **Enable 2FA** on sync account (if available)
3. ✅ **Backup encryption key** securely
4. ✅ **Use same password** across all devices
5. ✅ **Keep devices updated** with security patches
6. ✅ **Enable full-disk encryption** on devices
7. ✅ **Lock devices when unattended**

### For Developers

1. ✅ **Never log passwords or keys**
2. ✅ **Use `hmac.compare_digest()` for comparisons**
3. ✅ **Wipe sensitive data** after use
4. ✅ **Validate all inputs** before encryption
5. ✅ **Use TLS/HTTPS** for all network traffic
6. ✅ **Implement rate limiting** on auth endpoints
7. ✅ **Regular security audits**
8. ✅ **Keep dependencies updated**

### For Server Operators

1. ✅ **Use HTTPS only** (no HTTP)
2. ✅ **Enable certificate pinning**
3. ✅ **Implement rate limiting**
4. ✅ **Log authentication attempts**
5. ✅ **Regular security updates**
6. ✅ **Backup encrypted databases**
7. ✅ **Monitor for anomalies**
8. ✅ **Incident response plan**

## References

### Cryptographic Standards

- **NaCl/libsodium**: https://nacl.cr.yp.to/
- **Argon2**: https://github.com/P-H-C/phc-winner-argon2
- **XSalsa20**: https://cr.yp.to/snuffle/xsalsa-20110204.pdf
- **Poly1305**: https://cr.yp.to/mac.html

### Security Guidelines

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **NIST Cryptographic Standards**: https://csrc.nist.gov/
- **libsodium Documentation**: https://doc.libsodium.org/

### Compliance

- **GDPR**: https://gdpr.eu/
- **CCPA**: https://oag.ca.gov/privacy/ccpa
- **HIPAA**: https://www.hhs.gov/hipaa/

## Support

For security concerns or to report vulnerabilities:
- **Email**: security@windows-ai.com
- **Bug Bounty**: Coming soon
- **Security Policy**: SECURITY.md

**Please DO NOT** publicly disclose security vulnerabilities. Report them privately first.

---

**Last Updated**: January 2025
**Version**: 1.0.0
**Author**: Windows-AI Security Team
