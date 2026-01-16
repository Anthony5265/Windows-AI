# Windows AI REST API Documentation

## Base URL
\https://localhost:8000/api/v1
\
## Authentication
All requests require an Authorization header:
\Authorization: Bearer {token}
\
## Endpoints

### Health & Status
#### GET /health
Returns API health status
\\json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600
}
\
### Plugins
#### GET /plugins
List all available plugins
Response: \{ "plugins": [...] }
#### POST /plugins/load
Load a specific plugin
Request: \{ "name": "plugin_name" }
#### DELETE /plugins/{name}
Unload a plugin

### Queries
#### POST /query
Execute a query
Request:
\\json
{
  "query": "what is AI?",
  "context": "general",
  "timeout": 30
}
\
#### GET /query/{id}
Get query result status

### Configuration
#### GET /config
Get current configuration

#### PUT /config
Update configuration
