# Deployment Guide for Windows AI

This guide covers deployment options for Windows AI.

## Prerequisites

- Docker & Docker Compose (for containerized deployment)
- Python 3.10+ (for direct installation)
- PostgreSQL 12+ (for database)
- Redis 6+ (for caching)

## Quick Start with Docker Compose

```bash
# 1. Clone repository
git clone https://github.com/Anthony5265/Windows-AI.git
cd Windows-AI

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Start services
docker-compose up -d

# 4. Verify services
docker-compose ps

# 5. Check logs
docker-compose logs -f windows-ai

# 6. Access application
# API: http://localhost:8000
# UI: http://localhost:5000
```

## Production Deployment

### 1. Environment Setup

```bash
# Create .env file with production settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:password@db-host:5432/windows_ai
REDIS_URL=redis://redis-host:6379/0

# Security
SECRET_KEY=your-secret-key-here
API_KEY=your-api-key-here
JWT_SECRET=your-jwt-secret-here

# Storage
MINIO_ENDPOINT=s3-host:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

### 2. Database Setup

```bash
# Using PostgreSQL Docker
docker run -d \
  --name windows-ai-db \
  -e POSTGRES_USER=windows_ai \
  -e POSTGRES_PASSWORD=secure-password \
  -e POSTGRES_DB=windows_ai \
  -v postgres-data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:15

# Run migrations
docker exec windows-ai-db python -m windows_ai.db migrate
```

### 3. Application Deployment

#### Option A: Docker Container

```bash
# Build image
docker build -t windows-ai:latest .

# Run container
docker run -d \
  --name windows-ai \
  -e ENVIRONMENT=production \
  -p 8000:8000 \
  -p 5000:5000 \
  --network host \
  windows-ai:latest

# View logs
docker logs -f windows-ai
```

#### Option B: Kubernetes

```yaml
# windows-ai-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: windows-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: windows-ai
  template:
    metadata:
      labels:
        app: windows-ai
    spec:
      containers:
      - name: windows-ai
        image: windows-ai:latest
        ports:
        - containerPort: 8000
        - containerPort: 5000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

Deploy to Kubernetes:

```bash
kubectl apply -f windows-ai-deployment.yaml
```

#### Option C: Traditional Server

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure systemd service
sudo tee /etc/systemd/system/windows-ai.service > /dev/null <<EOF
[Unit]
Description=Windows AI Application
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/windows-ai
ExecStart=/usr/local/bin/python -m windows_ai
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 3. Start service
sudo systemctl daemon-reload
sudo systemctl start windows-ai
sudo systemctl enable windows-ai

# 4. Monitor
sudo systemctl status windows-ai
sudo journalctl -u windows-ai -f
```

### 4. Reverse Proxy Configuration (Nginx)

```nginx
# /etc/nginx/sites-available/windows-ai

upstream windows_ai_app {
    server localhost:8000;
}

upstream windows_ai_ui {
    server localhost:5000;
}

server {
    listen 80;
    server_name api.windows-ai.com;

    location / {
        proxy_pass http://windows_ai_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name ui.windows-ai.com;

    location / {
        proxy_pass http://windows_ai_ui;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 5. SSL/TLS Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d api.windows-ai.com -d ui.windows-ai.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### 6. Monitoring & Logging

#### Application Monitoring

```python
# Use Prometheus metrics
from prometheus_client import start_http_server, Counter, Histogram

# Start metrics server
start_http_server(8001)

# Track metrics
request_count = Counter('windows_ai_requests_total', 'Total requests')
request_duration = Histogram('windows_ai_request_duration_seconds', 'Request duration')
```

#### Log Aggregation

```yaml
# docker-compose.yml additions for ELK stack
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
  environment:
    - discovery.type=single-node

logstash:
  image: docker.elastic.co/logstash/logstash:8.0.0
  volumes:
    - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

kibana:
  image: docker.elastic.co/kibana/kibana:8.0.0
  ports:
    - "5601:5601"
```

## Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check database connection
curl http://localhost:8000/health/db

# Check cache connection
curl http://localhost:8000/health/cache

# Full health status
curl http://localhost:8000/health/full
```

## Scaling

### Horizontal Scaling

```bash
# Scale to 5 replicas
docker-compose up --scale app=5
```

### Database Optimization

- Enable connection pooling (PgBouncer)
- Configure replication for high availability
- Regular backup schedule

```bash
# Automated backups
0 2 * * * pg_dump -U windows_ai windows_ai | gzip > /backups/db-$(date +\%Y\%m\%d).sql.gz
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| 502 Bad Gateway | Check application logs: `docker logs windows-ai` |
| High Memory Usage | Scale application, check for memory leaks |
| Database Connection Errors | Verify connection string, check database status |
| Slow Response Times | Monitor API metrics, optimize queries |

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true
python -m windows_ai
```

## Backup & Recovery

```bash
# Backup database
docker exec windows-ai-db pg_dump -U windows_ai windows_ai > backup.sql

# Restore database
docker exec -i windows-ai-db psql -U windows_ai windows_ai < backup.sql

# Backup application data
docker exec windows-ai tar czf /tmp/app-backup.tar.gz /app/data/
docker cp windows-ai:/tmp/app-backup.tar.gz ./
```

## Security Checklist

- [ ] Update all dependencies: `pip install --upgrade -r requirements.txt`
- [ ] Set strong database passwords
- [ ] Enable SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Enable authentication on all endpoints
- [ ] Regular security scans: `bandit -r windows_ai/`
- [ ] Monitor logs for suspicious activity
- [ ] Implement rate limiting
- [ ] Regular backup tests

## Support & Resources

- [Troubleshooting Guide](./TROUBLESHOOTING.md)
- [API Docs Index](./api/README.md)
- [API Reference](./api/API_REFERENCE.md)
- [Configuration Guide](./deployment/CONFIGURATION.md)
- [Documentation Hub](./README.md)

