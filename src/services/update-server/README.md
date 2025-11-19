# Windows AI Update Server

Production-ready update server for serving Windows AI updates, manifests, and installers.

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python server.py

# Access at http://localhost:8011
```

### Docker

```bash
# Build and run
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## API Endpoints

### Health Check
```
GET /health
```

### Get Manifest
```
GET /manifest.json
```

### Check for Updates
```
GET /updates/check?current_version=0.4.0&channel=stable
```

### Download Release
```
GET /releases/{version}/download
```

### Get Release Info
```
GET /releases/{version}
```

### Statistics
```
GET /statistics
```

## Configuration

### Environment Variables

- `BASE_URL`: Base URL for the update server
- `LOG_LEVEL`: Logging level (default: info)
- `MANIFEST_PATH`: Path to manifest.json
- `DOWNLOADS_PATH`: Path to downloads directory

### Command Line Arguments

```bash
python server.py \
  --manifest manifest.json \
  --downloads downloads/ \
  --host 0.0.0.0 \
  --port 8011 \
  --base-url https://updates.example.com
```

## Directory Structure

```
update-server/
├── server.py              # Main server application
├── manifest.json          # Update manifest
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
├── deploy.md            # Deployment guide
├── README.md            # This file
└── downloads/           # Installer files (gitignored)
    └── WindowsAI-Setup-*.exe
```

## Deployment

See [deploy.md](deploy.md) for comprehensive deployment guide covering:

- Cloud platforms (AWS, Azure, GCP)
- VPS deployment
- Docker containers
- CDN configuration
- SSL setup
- Monitoring
- Scaling

## Adding New Releases

1. **Build installer** with build-installer.ps1
2. **Sign installer** with sign-installer.ps1
3. **Calculate checksums**:
   ```bash
   sha256sum WindowsAI-Setup-0.6.0.exe
   ```
4. **Update manifest.json**:
   ```json
   {
     "version": "0.6.0",
     "releaseDate": "2025-02-01T00:00:00Z",
     "files": {
       "installer": {
         "url": "/downloads/WindowsAI-Setup-0.6.0.exe",
         "size": 160000000,
         "sha256": "abc123..."
       }
     },
     "changelog": { ... }
   }
   ```
5. **Upload installer** to downloads/ directory
6. **Test update**:
   ```bash
   curl http://localhost:8011/updates/check?current_version=0.5.0
   ```

## Monitoring

### Health Check

```bash
curl http://localhost:8011/health
```

### Statistics

```bash
curl http://localhost:8011/statistics
```

### Logs

```bash
# Docker
docker-compose logs -f update-server

# Direct
journalctl -u windows-ai-update -f
```

## Security

- **HTTPS Required**: Use SSL certificates in production
- **Rate Limiting**: Configure rate limits to prevent abuse
- **Authentication**: Optional for statistics endpoints
- **Firewall**: Only expose ports 80 and 443

## Troubleshooting

### Server not starting

```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip install -r requirements.txt

# Check logs
python server.py --log-level debug
```

### Manifest not found

```bash
# Verify manifest exists
ls -l manifest.json

# Check manifest syntax
python -m json.tool manifest.json
```

### Downloads failing

```bash
# Verify downloads directory
ls -l downloads/

# Check file permissions
chmod 644 downloads/*.exe

# Verify checksums in manifest match actual files
sha256sum downloads/WindowsAI-Setup-*.exe
```

## Performance

### Benchmarks

- **Response time**: < 100ms for manifest/check endpoints
- **Download speed**: Limited by network/CDN
- **Concurrent users**: 100+ per instance
- **Memory usage**: ~50-100 MB per instance

### Optimization

1. **Enable CDN** for installer downloads
2. **Use caching** for manifest responses
3. **Enable gzip** compression
4. **Scale horizontally** with load balancer

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/

# Run with coverage
pytest --cov=windows_ai/updater tests/
```

### Adding Features

1. Fork repository
2. Create feature branch
3. Add tests
4. Submit pull request

## Support

- **Documentation**: [deploy.md](deploy.md)
- **Issues**: https://github.com/yourorg/Windows-AI/issues
- **Discussions**: https://github.com/yourorg/Windows-AI/discussions

## License

See LICENSE file in root directory.

---

**Version**: 1.0.0
**Last Updated**: 2025-01-10
