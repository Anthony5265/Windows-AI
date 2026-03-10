# Windows AI Authentication & Security

## Overview

Windows AI supports multiple authentication methods for secure API access.

## Authentication Methods

### 1. API Key Authentication

Simple key-based authentication for development and server-to-server communication.

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8000/api/v1/health
```

**Generate API Key:**

```bash
# Via CLI
windows-ai auth generate-key --name "Development Key"

# Via API
curl -X POST http://localhost:8000/api/v1/auth/keys \
  -H "Authorization: Bearer ADMIN_KEY" \
  -d '{"name": "Development Key"}'
```

### 2. OAuth 2.0

For user-facing applications and third-party integrations.

#### Authorization Code Flow

```python
from requests_oauthlib import OAuth2Session

REDIRECT_URI = 'http://localhost:8000/callback'
SCOPES = ['read', 'write', 'admin']

# Step 1: Redirect user to authorization endpoint
oauth = OAuth2Session(
    client_id='YOUR_CLIENT_ID',
    redirect_uri=REDIRECT_URI,
    scope=SCOPES
)
authorization_url, state = oauth.authorization_url(
    'http://localhost:8000/api/v1/oauth/authorize'
)
print(f"Visit: {authorization_url}")

# Step 2: User authorizes and is redirected
redirect_response = input("Enter redirect URL: ")
token = oauth.fetch_token(
    'http://localhost:8000/api/v1/oauth/token',
    client_secret='YOUR_CLIENT_SECRET',
    authorization_response=redirect_response
)

# Step 3: Use token for API calls
r = oauth.get('http://localhost:8000/api/v1/plugins')
print(r.json())
```

#### Client Credentials Flow

For machine-to-machine authentication:

```python
import requests

token_response = requests.post(
    'http://localhost:8000/api/v1/oauth/token',
    data={
        'grant_type': 'client_credentials',
        'client_id': 'YOUR_CLIENT_ID',
        'client_secret': 'YOUR_CLIENT_SECRET',
        'scope': 'read write'
    }
)

token = token_response.json()['access_token']

# Use token
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(
    'http://localhost:8000/api/v1/plugins',
    headers=headers
)
```

### 3. JWT (JSON Web Tokens)

For session-based authentication.

```python
import jwt
from datetime import datetime, timedelta

# Create token
payload = {
    'sub': 'user@example.com',
    'iat': datetime.utcnow(),
    'exp': datetime.utcnow() + timedelta(hours=1),
    'scope': ['read', 'write']
}

token = jwt.encode(
    payload,
    'your-secret-key',
    algorithm='HS256'
)

# Use token
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(
    'http://localhost:8000/api/v1/plugins',
    headers=headers
)
```

## Scopes

| Scope | Permission | Use Case |
|-------|-----------|----------|
| `read` | Read plugin data, query results | Data retrieval |
| `write` | Modify plugins, execute queries | Data manipulation |
| `admin` | Full system access | Administration |
| `plugin:*` | All plugin operations | Plugin management |
| `config:*` | Configuration management | System setup |

## Rate Limiting

API requests are rate limited per authentication method:

| Method | Limit | Window |
|--------|-------|--------|
| API Key | 1000 requests | Per hour |
| OAuth Token | 500 requests | Per hour |
| Admin Key | Unlimited | N/A |

**Response Headers:**

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705330800
```

## Token Management

### Generate Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "password"
  }'
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Refresh Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }'
```

### Revoke Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/revoke \
  -H "Authorization: Bearer TOKEN"
```

## Security Best Practices

### 1. Key Rotation

Regularly rotate API keys and credentials:

```bash
# Generate new key
new_key=$(windows-ai auth generate-key --name "Production Key v2")

# Update environment
export WINDOWS_AI_API_KEY=$new_key

# Revoke old key
windows-ai auth revoke-key "old-key-id"
```

### 2. HTTPS Only

Always use HTTPS in production:

```python
ai = WindowsAI(
    api_key="your-api-key",
    base_url="https://api.windows-ai.com/v1",
    verify_ssl=True
)
```

### 3. Environment Variables

Never hardcode credentials:

```python
import os
from windows_ai import WindowsAI

api_key = os.getenv('WINDOWS_AI_API_KEY')
ai = WindowsAI(api_key=api_key)
```

### 4. Secret Management

Use secure secret storage:

**AWS Secrets Manager:**

```python
import boto3

client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='windows-ai-key')
api_key = secret['SecretString']
```

**HashiCorp Vault:**

```python
import hvac

client = hvac.Client(url='http://localhost:8200')
secret = client.secrets.kv.read_secret_version(path='windows-ai')
api_key = secret['data']['data']['api_key']
```

### 5. Audit Logging

Monitor authentication events:

```bash
# View authentication logs
curl http://localhost:8000/api/v1/audit-logs?event_type=auth \
  -H "Authorization: Bearer ADMIN_KEY"
```

### 6. MFA (Multi-Factor Authentication)

Enable 2FA for user accounts:

```bash
# Enable MFA
curl -X POST http://localhost:8000/api/v1/auth/mfa/enable \
  -H "Authorization: Bearer TOKEN" \
  -d '{"method": "totp"}'

# Verify MFA code
curl -X POST http://localhost:8000/api/v1/auth/mfa/verify \
  -d '{
    "code": "123456",
    "backup_codes": ["code1", "code2"]
  }'
```

### 7. CORS Configuration

```python
# In Windows AI configuration
CORS_ORIGINS = [
    "https://example.com",
    "https://app.example.com"
]
CORS_ALLOW_CREDENTIALS = True
```

## Common Authentication Errors

### 401 Unauthorized

```
Error: Invalid or missing authentication credentials

Solution:
- Verify API key is correct
- Check Authorization header format
- Ensure token hasn't expired
```

### 403 Forbidden

```
Error: Insufficient permissions for this resource

Solution:
- Check scopes for token
- Verify user role and permissions
- Contact administrator for access
```

### 429 Too Many Requests

```
Error: Rate limit exceeded

Solution:
- Implement exponential backoff
- Cache responses when possible
- Request rate limit increase
```

## Testing Authentication

### Unit Tests

```python
import pytest
from windows_ai import WindowsAI
from windows_ai.exceptions import AuthenticationError

def test_valid_api_key():
    ai = WindowsAI(api_key="valid-key")
    health = ai.health()
    assert health.status == "ok"

def test_invalid_api_key():
    ai = WindowsAI(api_key="invalid-key")
    with pytest.raises(AuthenticationError):
        ai.health()

def test_expired_token():
    ai = WindowsAI(api_key="expired-token")
    with pytest.raises(AuthenticationError):
        ai.query("SELECT * FROM data")
```

### Integration Tests

```bash
# Test API key authentication
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8000/api/v1/health

# Test OAuth flow
curl -X POST http://localhost:8000/api/v1/oauth/token \
  -d "grant_type=client_credentials&client_id=$CLIENT_ID&client_secret=$CLIENT_SECRET"

# Test rate limiting
for i in {1..1001}; do
  curl -H "Authorization: Bearer $API_KEY" \
       http://localhost:8000/api/v1/plugins
done
```

## Compliance

### GDPR

- User consent for data collection
- Data portability options
- Right to deletion support

### HIPAA

- Encryption at rest and in transit
- Audit logging
- Access controls and MFA

### SOC 2

- Security monitoring
- Incident response procedures
- Annual audits

## Support

- [GitHub Issues](https://github.com/Anthony5265/Windows-AI/issues)
- [Security Policy](../SECURITY.md)
- [Contact Security Team](security@windows-ai.com)
