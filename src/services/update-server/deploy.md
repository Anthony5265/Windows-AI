# Windows AI Update Server Deployment Guide

Complete guide for deploying the Windows AI update server to various platforms.

## Overview

The update server is a FastAPI application that serves:
- Update manifest (available versions, changelogs)
- Installer downloads
- Version checking API
- Statistics and monitoring

## Prerequisites

- Python 3.11+
- FastAPI and dependencies (see requirements.txt)
- Installer files to serve
- SSL certificate (for production)
- CDN (optional but recommended)

## Quick Start (Local Development)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start server
python update-server/server.py

# 3. Access server
# http://localhost:8011
```

## Production Deployment Options

### Option 1: Cloud Platform (Recommended)

#### A. Deploy to AWS (Elastic Beanstalk + S3)

**Architecture:**
- Elastic Beanstalk: Runs update server
- S3: Stores installer files
- CloudFront: CDN for downloads
- Route 53: DNS management
- Certificate Manager: SSL certificates

**Setup:**

1. **Create S3 bucket for installers**
```bash
aws s3 mb s3://windows-ai-installers
aws s3 cp dist/WindowsAI-Setup-0.5.0.exe s3://windows-ai-installers/downloads/
```

2. **Create Elastic Beanstalk application**
```bash
eb init -p python-3.11 windows-ai-update-server
eb create windows-ai-update-prod --envvars MANIFEST_PATH=/var/app/manifest.json
```

3. **Configure CloudFront CDN**
```bash
# Create CloudFront distribution pointing to S3 bucket
# Configure caching and SSL
```

4. **Deploy application**
```bash
eb deploy
```

**Cost Estimate:**
- Elastic Beanstalk: ~$10-30/month
- S3 Storage: ~$0.023/GB/month
- CloudFront: ~$0.085/GB transfer
- Total: ~$20-50/month for small scale

#### B. Deploy to Azure (App Service + Blob Storage)

**Architecture:**
- App Service: Runs update server
- Blob Storage: Stores installer files
- CDN: For downloads
- Application Insights: Monitoring

**Setup:**

1. **Create resource group**
```bash
az group create --name windows-ai-updates --location eastus
```

2. **Create storage account**
```bash
az storage account create \
  --name windowsaiupdates \
  --resource-group windows-ai-updates \
  --location eastus \
  --sku Standard_LRS
```

3. **Upload installers**
```bash
az storage blob upload \
  --account-name windowsaiupdates \
  --container-name downloads \
  --name WindowsAI-Setup-0.5.0.exe \
  --file dist/WindowsAI-Setup-0.5.0.exe
```

4. **Create App Service**
```bash
az webapp create \
  --resource-group windows-ai-updates \
  --plan windows-ai-plan \
  --name windows-ai-update-server \
  --runtime "PYTHON:3.11"
```

5. **Deploy application**
```bash
az webapp up --name windows-ai-update-server
```

**Cost Estimate:**
- App Service: ~$10-50/month
- Blob Storage: ~$0.018/GB/month
- CDN: ~$0.081/GB transfer
- Total: ~$15-60/month

#### C. Deploy to Google Cloud (Cloud Run + Cloud Storage)

**Architecture:**
- Cloud Run: Serverless container runtime
- Cloud Storage: Stores installer files
- Cloud CDN: For downloads
- Cloud Monitoring: Logs and metrics

**Setup:**

1. **Create storage bucket**
```bash
gsutil mb gs://windows-ai-installers
gsutil cp dist/WindowsAI-Setup-0.5.0.exe gs://windows-ai-installers/downloads/
```

2. **Containerize application**
```dockerfile
# Dockerfile already provided (see below)
```

3. **Build and deploy**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/update-server
gcloud run deploy update-server --image gcr.io/PROJECT_ID/update-server --platform managed
```

**Cost Estimate:**
- Cloud Run: Pay per request (~$0.40/million requests)
- Cloud Storage: ~$0.020/GB/month
- Cloud CDN: ~$0.08/GB transfer
- Total: ~$10-40/month (highly variable)

### Option 2: VPS / Dedicated Server

**Recommended Providers:**
- DigitalOcean ($5-20/month)
- Linode ($5-20/month)
- Vultr ($5-20/month)
- AWS Lightsail ($5-20/month)

**Setup:**

1. **Provision server**
```bash
# Ubuntu 22.04 LTS recommended
# Minimum: 1 GB RAM, 1 CPU, 25 GB disk
```

2. **Install dependencies**
```bash
sudo apt update
sudo apt install -y python3.11 python3-pip nginx certbot
```

3. **Clone repository**
```bash
git clone https://github.com/yourorg/Windows-AI.git
cd Windows-AI
pip install -r requirements.txt
```

4. **Configure systemd service**
```ini
# /etc/systemd/system/windows-ai-update.service
[Unit]
Description=Windows AI Update Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/windows-ai
ExecStart=/usr/bin/python3 update-server/server.py --host 127.0.0.1 --port 8011
Restart=always

[Install]
WantedBy=multi-user.target
```

5. **Configure Nginx reverse proxy**
```nginx
# /etc/nginx/sites-available/windows-ai-updates
server {
    listen 80;
    server_name updates.windows-ai.example.com;

    location / {
        proxy_pass http://127.0.0.1:8011;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /downloads/ {
        alias /opt/windows-ai/update-server/downloads/;
        sendfile on;
        tcp_nopush on;
    }
}
```

6. **Enable SSL with Let's Encrypt**
```bash
sudo certbot --nginx -d updates.windows-ai.example.com
```

7. **Start services**
```bash
sudo systemctl enable windows-ai-update
sudo systemctl start windows-ai-update
sudo systemctl restart nginx
```

**Cost Estimate:**
- VPS: $5-20/month
- Bandwidth: Usually included
- Total: $5-20/month

### Option 3: Docker Container

**Use Cases:**
- Containerized deployment
- Kubernetes clusters
- Docker Swarm

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY windows_ai/ windows_ai/
COPY update-server/ update-server/

# Expose port
EXPOSE 8011

# Run server
CMD ["python", "update-server/server.py", "--host", "0.0.0.0", "--port", "8011"]
```

**Build and run:**
```bash
# Build image
docker build -t windows-ai-update-server .

# Run container
docker run -d \
  -p 8011:8011 \
  -v $(pwd)/update-server/downloads:/app/update-server/downloads \
  -v $(pwd)/update-server/manifest.json:/app/update-server/manifest.json \
  --name update-server \
  windows-ai-update-server
```

**Docker Compose:**
```yaml
version: '3.8'

services:
  update-server:
    build: .
    ports:
      - "8011:8011"
    volumes:
      - ./update-server/downloads:/app/update-server/downloads
      - ./update-server/manifest.json:/app/update-server/manifest.json
    environment:
      - BASE_URL=https://updates.windows-ai.example.com
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - update-server
    restart: unless-stopped
```

## CDN Configuration

Using a CDN is highly recommended for:
- Faster downloads
- Reduced server load
- Better global performance
- DDoS protection

### Cloudflare (Free/Paid)

1. **Add domain to Cloudflare**
2. **Configure DNS:**
   ```
   updates.windows-ai.example.com -> A record -> Your server IP
   ```
3. **Enable proxy (orange cloud)**
4. **Configure caching rules:**
   - Cache Level: Standard
   - Browser Cache TTL: 1 hour
   - Edge Cache TTL: 1 day for installers

### AWS CloudFront

1. **Create distribution**
```bash
aws cloudfront create-distribution \
  --origin-domain-name your-server.example.com \
  --default-root-object index.html
```

2. **Configure caching behaviors**
```json
{
  "PathPattern": "/downloads/*",
  "TargetOriginId": "S3-windows-ai-installers",
  "ViewerProtocolPolicy": "redirect-to-https",
  "MinTTL": 86400,
  "DefaultTTL": 86400,
  "MaxTTL": 31536000
}
```

## Monitoring and Maintenance

### Health Checks

```bash
# Check server health
curl https://updates.windows-ai.example.com/health

# Check specific version
curl https://updates.windows-ai.example.com/updates/check?current_version=0.4.0
```

### Logs

```bash
# System logs (VPS)
sudo journalctl -u windows-ai-update -f

# Application logs
tail -f /var/log/windows-ai-update.log
```

### Metrics

Monitor:
- Request rate
- Response time
- Error rate
- Bandwidth usage
- Download counts by version

### Updating the Manifest

```bash
# 1. Add new release to manifest.json
# 2. Upload new installer to downloads directory
# 3. Update checksums
# 4. Reload server (or it will auto-reload)
```

## Security Best Practices

1. **HTTPS Only**
   - Use SSL certificates (Let's Encrypt is free)
   - Redirect HTTP to HTTPS

2. **Rate Limiting**
   - Implement rate limiting to prevent abuse
   - Nginx: `limit_req_zone $binary_remote_addr zone=one:10m rate=10r/s;`

3. **Authentication (Optional)**
   - For internal deployments, add basic auth
   - For public deployments, consider API keys for statistics

4. **Firewall**
   - Only allow ports 80, 443, and SSH
   ```bash
   sudo ufw allow 22
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```

5. **Regular Updates**
   - Keep server OS updated
   - Update Python dependencies regularly
   - Monitor security advisories

## Scaling

### Horizontal Scaling

Use load balancer with multiple instances:

```
                    ┌─> Update Server 1
Load Balancer ──────┤
                    └─> Update Server 2
                          │
                          v
                    CDN / S3 (Installers)
```

### Vertical Scaling

Increase server resources as needed:
- Start: 1 GB RAM, 1 CPU
- Medium: 2 GB RAM, 2 CPU
- Large: 4 GB RAM, 4 CPU

### Caching

- Enable response caching
- Use Redis for rate limiting
- CDN for installer files

## Troubleshooting

### Server not responding

```bash
# Check if server is running
sudo systemctl status windows-ai-update

# Check logs
sudo journalctl -u windows-ai-update -n 100
```

### High bandwidth usage

- Enable CDN
- Implement rate limiting
- Check for download bots

### Manifest not updating

```bash
# Reload manifest
curl -X POST https://updates.windows-ai.example.com/manifest/reload
```

## Cost Optimization

1. **Use CDN** - Reduces origin bandwidth costs
2. **Compress responses** - Enable gzip/brotli
3. **Cache aggressively** - Set long cache times for installers
4. **Monitor usage** - Set up billing alerts
5. **Use object storage** - S3/Blob Storage is cheaper than server storage

## Support

For deployment issues:
- Check deployment logs
- Review this documentation
- Open GitHub issue
- Contact support

---

**Last Updated**: 2025-01-10
**Version**: 1.0.0
