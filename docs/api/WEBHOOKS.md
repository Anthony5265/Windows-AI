# Windows AI Webhooks Documentation

## Overview

Webhooks allow Windows AI to send real-time events to your application. This enables event-driven architectures and real-time integrations.

## Getting Started

### 1. Register a Webhook

```bash
curl -X POST http://localhost:8000/api/v1/webhooks \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-domain.com/webhooks/windows-ai",
    "events": ["plugin.loaded", "query.completed"],
    "active": true
  }'
```

### 2. Handle Webhook Events

Your endpoint should:
- Accept POST requests
- Return HTTP 200 status
- Process within 5 seconds
- Implement exponential backoff for retries

```python
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/webhooks/windows-ai', methods=['POST'])
def handle_webhook():
    event = request.get_json()
    
    # Verify signature
    signature = request.headers.get('X-Webhook-Signature')
    if not verify_signature(event, signature):
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Process event
    event_type = event.get('type')
    event_data = event.get('data')
    
    if event_type == 'plugin.loaded':
        handle_plugin_loaded(event_data)
    elif event_type == 'query.completed':
        handle_query_completed(event_data)
    
    return jsonify({'status': 'received'}), 200
```

## Event Types

### Plugin Events

#### plugin.loaded
Fired when a plugin is loaded.

```json
{
  "type": "plugin.loaded",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "plugin_name": "data_cleaner",
    "version": "1.0.0",
    "category": "data_processing"
  }
}
```

#### plugin.unloaded
Fired when a plugin is unloaded.

```json
{
  "type": "plugin.unloaded",
  "timestamp": "2024-01-15T10:35:00Z",
  "data": {
    "plugin_name": "data_cleaner",
    "reason": "user_request"
  }
}
```

#### plugin.error
Fired when a plugin encounters an error.

```json
{
  "type": "plugin.error",
  "timestamp": "2024-01-15T10:40:00Z",
  "data": {
    "plugin_name": "api_gateway",
    "error": "Connection timeout",
    "error_code": "TIMEOUT",
    "severity": "high"
  }
}
```

### Query Events

#### query.started
Fired when a query execution begins.

```json
{
  "type": "query.started",
  "timestamp": "2024-01-15T10:45:00Z",
  "data": {
    "query_id": "q-12345",
    "query": "SELECT * FROM users",
    "user": "user@example.com"
  }
}
```

#### query.completed
Fired when a query completes successfully.

```json
{
  "type": "query.completed",
  "timestamp": "2024-01-15T10:46:00Z",
  "data": {
    "query_id": "q-12345",
    "result_count": 150,
    "execution_time_ms": 245,
    "success": true
  }
}
```

#### query.failed
Fired when a query fails.

```json
{
  "type": "query.failed",
  "timestamp": "2024-01-15T10:47:00Z",
  "data": {
    "query_id": "q-12345",
    "error": "Database connection failed",
    "error_code": "DB_ERROR",
    "query": "SELECT * FROM users"
  }
}
```

### Authentication Events

#### auth.login
Fired on successful login.

```json
{
  "type": "auth.login",
  "timestamp": "2024-01-15T10:50:00Z",
  "data": {
    "user": "user@example.com",
    "ip_address": "192.168.1.100",
    "method": "password"
  }
}
```

#### auth.logout
Fired on logout.

```json
{
  "type": "auth.logout",
  "timestamp": "2024-01-15T10:55:00Z",
  "data": {
    "user": "user@example.com",
    "session_duration_seconds": 300
  }
}
```

#### auth.failed
Fired on authentication failure.

```json
{
  "type": "auth.failed",
  "timestamp": "2024-01-15T11:00:00Z",
  "data": {
    "user": "user@example.com",
    "ip_address": "192.168.1.100",
    "reason": "invalid_password"
  }
}
```

### Configuration Events

#### config.updated
Fired when configuration changes.

```json
{
  "type": "config.updated",
  "timestamp": "2024-01-15T11:05:00Z",
  "data": {
    "changes": {
      "log_level": ["INFO", "DEBUG"],
      "cache_enabled": [true, false]
    },
    "updated_by": "admin@example.com"
  }
}
```

## Webhook Management

### List Webhooks

```bash
curl http://localhost:8000/api/v1/webhooks \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Response:

```json
{
  "webhooks": [
    {
      "id": "wh-123",
      "url": "https://your-domain.com/webhooks/windows-ai",
      "events": ["plugin.loaded", "query.completed"],
      "active": true,
      "created_at": "2024-01-15T10:00:00Z",
      "last_triggered": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Update Webhook

```bash
curl -X PUT http://localhost:8000/api/v1/webhooks/wh-123 \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "events": ["plugin.loaded", "query.completed", "query.failed"],
    "active": true
  }'
```

### Delete Webhook

```bash
curl -X DELETE http://localhost:8000/api/v1/webhooks/wh-123 \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Test Webhook

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/wh-123/test \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Security

### Webhook Signature Verification

Each webhook request includes a signature header:

```
X-Webhook-Signature: sha256=5d41402abc4b2a76b9719d911017c592
```

Verify the signature:

```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected_signature = 'sha256=' + hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

# Usage
@app.route('/webhooks/windows-ai', methods=['POST'])
def handle_webhook():
    payload = request.get_data(as_text=True)
    signature = request.headers.get('X-Webhook-Signature')
    
    if not verify_signature(payload, signature, 'your-webhook-secret'):
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Process webhook
    return jsonify({'status': 'received'}), 200
```

### Best Practices

1. **Always verify signatures** - Validate incoming webhooks
2. **Use HTTPS** - Always use secure endpoints
3. **Implement retry logic** - Handle transient failures
4. **Log events** - Maintain audit trail
5. **Monitor delivery** - Track webhook health
6. **Handle duplicates** - Some events may be delivered twice
7. **Set timeouts** - Respond quickly (< 5 seconds)

## Retry Policy

Webhooks are retried with exponential backoff:

| Attempt | Delay | Max Wait |
|---------|-------|----------|
| 1 | 60s | 60s |
| 2 | 120s | 120s |
| 3 | 300s | 300s |
| 4 | 600s | 600s |
| 5 | 1800s | 1800s |

After 5 failed attempts, the webhook is disabled.

## Examples

### Slack Notification

```python
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

@app.route('/webhooks/windows-ai', methods=['POST'])
def handle_webhook():
    event = request.get_json()
    
    if event['type'] == 'plugin.error':
        send_slack_alert(event['data'])
    
    return jsonify({'status': 'received'}), 200

def send_slack_alert(data):
    message = {
        "text": f":warning: Plugin Error: {data['plugin_name']}",
        "attachments": [{
            "color": "danger",
            "fields": [
                {"title": "Plugin", "value": data['plugin_name']},
                {"title": "Error", "value": data['error']},
                {"title": "Severity", "value": data['severity']}
            ]
        }]
    }
    requests.post(SLACK_WEBHOOK_URL, json=message)
```

### Database Logging

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from datetime import datetime

engine = create_engine('postgresql://user:password@localhost/windows_ai')

@app.route('/webhooks/windows-ai', methods=['POST'])
def handle_webhook():
    event = request.get_json()
    
    # Log to database
    log_event(event)
    
    return jsonify({'status': 'received'}), 200

def log_event(event):
    with Session(engine) as session:
        log_entry = WebhookLog(
            event_type=event['type'],
            timestamp=datetime.fromisoformat(event['timestamp']),
            data=event['data']
        )
        session.add(log_entry)
        session.commit()
```

### Analytics Tracking

```python
import requests
from datetime import datetime

ANALYTICS_API = "https://analytics.example.com/api/events"

@app.route('/webhooks/windows-ai', methods=['POST'])
def handle_webhook():
    event = request.get_json()
    
    # Track analytics
    track_event(event['type'], event['data'])
    
    return jsonify({'status': 'received'}), 200

def track_event(event_type, data):
    analytics_event = {
        "event": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "properties": data
    }
    requests.post(ANALYTICS_API, json=analytics_event)
```

## Monitoring

### Webhook Health

```bash
curl http://localhost:8000/api/v1/webhooks/health \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Response:

```json
{
  "total_webhooks": 5,
  "active_webhooks": 4,
  "failed_deliveries": 2,
  "last_check": "2024-01-15T11:10:00Z"
}
```

### Delivery History

```bash
curl http://localhost:8000/api/v1/webhooks/wh-123/deliveries \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Troubleshooting

### Webhooks Not Triggering

1. Verify webhook is active: `active: true`
2. Check event type subscription
3. Monitor logs: `/api/v1/webhooks/wh-123/logs`
4. Test webhook: `POST /api/v1/webhooks/wh-123/test`

### Failed Deliveries

1. Check endpoint availability
2. Verify response time (< 5 seconds)
3. Return HTTP 200 status
4. Check signature verification
5. Review retry logs

## Support

- [GitHub Issues](https://github.com/Anthony5265/Windows-AI/issues)
- [Documentation](https://windows-ai.readthedocs.io)
