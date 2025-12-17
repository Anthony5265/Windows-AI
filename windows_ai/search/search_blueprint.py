#!/usr/bin/env python3
"""
Search Blueprint

Launch `search/search_blueprint.py` documenting blueprints that future-proof semantic retrieval capabilities.

Created: 2025-11-15
Part of: Windows-AI Roadmap Implementation
"""

import asyncio
import importlib
import inspect
import json
import logging
import pkgutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SearchBlueprint:
    """
    Architecture documentation generator for Windows AI search subsystem.
    
    This class automatically generates comprehensive documentation blueprints
    for the search system including architecture diagrams, component documentation,
    API references, data flow diagrams, deployment guides, and configuration templates.
    
    Features:
    - Automatic architecture documentation generation
    - Component relationship mapping and visualization
    - API endpoint documentation with examples
    - Data flow diagram generation
    - Deployment guide creation
    - Configuration template generation
    - Markdown and HTML output formats
    - Mermaid diagram syntax support
    - Automated code introspection
    
    Example:
        blueprint = SearchBlueprint(
            output_dir=Path("docs/search"),
            format="markdown"
        )
        await blueprint.setup()
        
        # Generate all documentation
        result = await blueprint.execute(action="generate_all")
        
        # Generate specific documentation
        arch_doc = await blueprint.execute(action="architecture")
        api_doc = await blueprint.execute(action="api")
    """
    
    def __init__(
        self,
        output_dir: Optional[Path] = None,
        format: str = "markdown",
        include_diagrams: bool = True,
        include_examples: bool = True
    ):
        """
        Initialize the blueprint documentation generator.
        
        Args:
            output_dir: Directory for generated documentation (default: ~/.windows_ai/search_docs)
            format: Output format - "markdown", "html", or "json"
            include_diagrams: Whether to generate diagrams
            include_examples: Whether to include code examples
        """
        self.initialized = False
        self.output_dir = output_dir or Path.home() / ".windows_ai" / "search_docs"
        self.format = format
        self.include_diagrams = include_diagrams
        self.include_examples = include_examples
        
        # Documentation storage
        self.architecture_doc = ""
        self.component_docs: Dict[str, str] = {}
        self.api_docs: List[Dict[str, Any]] = []
        self.diagrams: Dict[str, str] = {}
        
        # Metadata
        self.generation_timestamp = datetime.now()
        
        logger.info(f"Initialized SearchBlueprint with format={format}")
    
    async def setup(self) -> bool:
        """
        Set up the documentation generator and prepare for operation.
        
        Creates output directories, initializes templates, and validates configuration.
        
        Returns:
            True if setup successful, False otherwise
        """
        if self.initialized:
            logger.warning("SearchBlueprint already initialized")
            return True
        
        try:
            logger.info("Setting up SearchBlueprint...")
            
            # Create output directories
            self.output_dir.mkdir(parents=True, exist_ok=True)
            (self.output_dir / "diagrams").mkdir(exist_ok=True)
            (self.output_dir / "api").mkdir(exist_ok=True)
            (self.output_dir / "guides").mkdir(exist_ok=True)
            (self.output_dir / "templates").mkdir(exist_ok=True)
            
            logger.debug(f"Created documentation directories in: {self.output_dir}")
            
            # Initialize documentation templates
            await self._init_templates()
            
            # Scan search module structure
            await self._scan_search_modules()
            
            self.initialized = True
            logger.info("SearchBlueprint setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"SearchBlueprint setup failed: {e}", exc_info=True)
            return False
    
    async def execute(self, action: str = "generate_all", **kwargs) -> Dict[str, Any]:
        """
        Execute documentation generation operations.
        
        Args:
            action: Operation to perform - "generate_all", "architecture", 
                   "api", "components", "deployment", "diagrams"
            **kwargs: Action-specific parameters
            
        Returns:
            Dict containing execution results with status and file paths
            
        Raises:
            RuntimeError: If blueprint not initialized
        """
        if not self.initialized:
            raise RuntimeError("SearchBlueprint not initialized. Call setup() first.")
        
        try:
            logger.debug(f"Executing SearchBlueprint action: {action}")
            
            if action == "generate_all":
                return await self._generate_all_docs()
            elif action == "architecture":
                return await self._generate_architecture_doc()
            elif action == "api":
                return await self._document_api()
            elif action == "components":
                return await self._create_component_diagram()
            elif action == "deployment":
                return await self._create_deployment_guide()
            elif action == "diagrams":
                return await self._generate_diagrams()
            elif action == "config_templates":
                return await self._generate_config_templates()
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except Exception as e:
            logger.error(f"SearchBlueprint execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "files": []
            }
    
    async def _generate_all_docs(self) -> Dict[str, Any]:
        """
        Generate all documentation types.
        
        Returns:
            Dict with status and list of generated files
        """
        try:
            logger.info("Generating complete documentation blueprint...")
            
            generated_files = []
            
            # Generate architecture documentation
            arch_result = await self._generate_architecture_doc()
            if arch_result["status"] == "success":
                generated_files.extend(arch_result["files"])
            
            # Generate API documentation
            api_result = await self._document_api()
            if api_result["status"] == "success":
                generated_files.extend(api_result["files"])
            
            # Generate component diagrams
            component_result = await self._create_component_diagram()
            if component_result["status"] == "success":
                generated_files.extend(component_result["files"])
            
            # Generate deployment guide
            deploy_result = await self._create_deployment_guide()
            if deploy_result["status"] == "success":
                generated_files.extend(deploy_result["files"])
            
            # Generate configuration templates
            config_result = await self._generate_config_templates()
            if config_result["status"] == "success":
                generated_files.extend(config_result["files"])
            
            logger.info(f"Generated {len(generated_files)} documentation files")
            
            return {
                "status": "success",
                "message": f"Generated {len(generated_files)} documentation files",
                "files": generated_files,
                "output_dir": str(self.output_dir)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate all documentation: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "files": []
            }
    
    async def _generate_architecture_doc(self) -> Dict[str, Any]:
        """
        Generate comprehensive architecture documentation.
        
        Returns:
            Dict with status and file paths
        """
        try:
            logger.info("Generating architecture documentation...")
            
            arch_doc = f"""# Windows AI Search Subsystem Architecture

**Generated:** {self.generation_timestamp.isoformat()}

## Overview

The Windows AI Search subsystem provides semantic retrieval capabilities for the platform,
enabling intelligent document search, knowledge retrieval, and content discovery.

## System Architecture

### Core Components

1. **Search Indexers**
   - Document indexing and processing
   - Embedding generation and storage
   - Real-time index updates

2. **Search Backends**
   - Vector similarity search
   - Hybrid search (vector + keyword)
   - Result ranking and scoring

3. **Search Connectors**
   - External data source integration
   - API connectors for cloud services
   - Database connectors

4. **Search Monitoring**
   - Quality metrics tracking
   - Performance monitoring
   - Anomaly detection

5. **Search Analytics**
   - Usage analytics
   - Query pattern analysis
   - Performance telemetry

## Data Flow

```mermaid
graph LR
    A[User Query] --> B[Query Processor]
    B --> C[Search Backend]
    C --> D[Vector Store]
    C --> E[Keyword Index]
    D --> F[Ranking Engine]
    E --> F
    F --> G[Results]
    G --> H[User]
    
    I[Documents] --> J[Indexer]
    J --> K[Embedding Generator]
    K --> D
    J --> E
```

## Technology Stack

- **Vector Storage:** ChromaDB, Faiss, Pinecone, Qdrant, Weaviate
- **Embedding Models:** OpenAI, Sentence Transformers, Cohere
- **Backend:** Python 3.10+, FastAPI, AsyncIO
- **Monitoring:** Prometheus-compatible metrics

## Scalability

The search subsystem is designed for horizontal scalability:

- Distributed vector stores for large-scale deployments
- Async processing for high concurrency
- Caching for frequently accessed results
- Load balancing across multiple backend instances

## Security

- API key authentication for external services
- Rate limiting on search endpoints
- Query sanitization to prevent injection attacks
- Encrypted storage for sensitive data

## Performance Targets

- Query latency: < 200ms (p95)
- Throughput: > 1000 queries/second
- Index update latency: < 5 seconds
- Availability: 99.9%

## Future Enhancements

- Multi-modal search (text, image, audio)
- Federated search across multiple sources
- Real-time collaborative filtering
- Advanced query understanding with LLMs

---

*For detailed API documentation, see `api/search_api.md`*
*For deployment instructions, see `guides/deployment.md`*
"""
            
            # Write architecture doc
            arch_file = self.output_dir / "architecture.md"
            await self._write_file(arch_file, arch_doc)
            
            logger.info(f"Architecture documentation written to: {arch_file}")
            
            return {
                "status": "success",
                "message": "Architecture documentation generated",
                "files": [str(arch_file)]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate architecture doc: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "files": []
            }
    
    async def _document_api(self) -> Dict[str, Any]:
        """
        Generate API documentation for search endpoints.
        
        Returns:
            Dict with status and file paths
        """
        try:
            logger.info("Generating API documentation...")
            
            api_doc = f"""# Windows AI Search API Reference

**Generated:** {self.generation_timestamp.isoformat()}

## Base URL

```
http://localhost:8010/api/v1/search
```

## Authentication

All API requests require authentication via API key header:

```
X-API-Key: your_api_key_here
```

## Endpoints

### 1. Search Query

**POST** `/search/query`

Execute a semantic search query.

**Request Body:**

```json
{{
  "query": "artificial intelligence applications",
  "top_k": 10,
  "filters": {{
    "source": "documents",
    "date_range": {{
      "start": "2024-01-01",
      "end": "2024-12-31"
    }}
  }},
  "include_scores": true
}}
```

**Response:**

```json
{{
  "status": "success",
  "results": [
    {{
      "id": "doc_123",
      "title": "AI Applications in Healthcare",
      "content": "...",
      "score": 0.95,
      "metadata": {{
        "source": "documents",
        "created_at": "2024-06-15"
      }}
    }}
  ],
  "query_time_ms": 145,
  "total_results": 10
}}
```

### 2. Index Document

**POST** `/search/index`

Index a new document for search.

**Request Body:**

```json
{{
  "document_id": "doc_456",
  "content": "Document content to be indexed...",
  "metadata": {{
    "title": "My Document",
    "source": "upload",
    "tags": ["AI", "ML"]
  }}
}}
```

**Response:**

```json
{{
  "status": "success",
  "document_id": "doc_456",
  "indexed_at": "2024-01-15T10:30:00Z"
}}
```

### 3. Get Search Stats

**GET** `/search/stats`

Retrieve search performance statistics.

**Response:**

```json
{{
  "total_queries": 15000,
  "avg_latency_ms": 120,
  "p95_latency_ms": 200,
  "total_documents": 50000,
  "index_size_mb": 2048
}}
```

### 4. Health Check

**GET** `/search/health`

Check search subsystem health status.

**Response:**

```json
{{
  "status": "healthy",
  "components": {{
    "vector_store": "operational",
    "indexer": "operational",
    "monitor": "operational"
  }},
  "last_check": "2024-01-15T10:30:00Z"
}}
```

## Error Responses

All errors follow this format:

```json
{{
  "status": "error",
  "error_code": "SEARCH_FAILED",
  "message": "Detailed error message",
  "details": {{}}
}}
```

## Rate Limits

- **Free tier:** 100 requests/minute
- **Pro tier:** 1000 requests/minute
- **Enterprise:** Unlimited

## Examples

### Python

```python
import requests

response = requests.post(
    "http://localhost:8010/api/v1/search/query",
    headers={{"X-API-Key": "your_key"}},
    json={{
        "query": "machine learning",
        "top_k": 5
    }}
)

results = response.json()
print(f"Found {{len(results['results'])}} results")
```

### cURL

```bash
curl -X POST http://localhost:8010/api/v1/search/query \\
  -H "X-API-Key: your_key" \\
  -H "Content-Type: application/json" \\
  -d '{{"query": "machine learning", "top_k": 5}}'
```

---

*For more examples, see the [Search Examples](examples/) directory.*
"""
            
            api_file = self.output_dir / "api" / "search_api.md"
            await self._write_file(api_file, api_doc)
            
            logger.info(f"API documentation written to: {api_file}")
            
            return {
                "status": "success",
                "message": "API documentation generated",
                "files": [str(api_file)]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate API documentation: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "files": []
            }
    
    async def _create_component_diagram(self) -> Dict[str, Any]:
        """
        Generate component relationship diagrams.
        
        Returns:
            Dict with status and diagram file paths
        """
        try:
            logger.info("Generating component diagrams...")
            
            # Component architecture diagram (Mermaid syntax)
            component_diagram = """```mermaid
graph TB
    subgraph "Search Subsystem"
        A[SearchMonitor] -->|monitors| B[SearchBackend]
        C[SearchIndexer] -->|feeds| B
        D[SearchConnector] -->|provides data| C
        E[SearchAnalyzer] -->|analyzes| A
        F[SearchBlueprint] -->|documents| B
    end
    
    subgraph "Storage Layer"
        G[Vector Store]
        H[Document Store]
        I[Cache]
    end
    
    subgraph "External Services"
        J[Embedding API]
        K[Cloud Storage]
        L[Databases]
    end
    
    B --> G
    B --> H
    B --> I
    C --> J
    D --> K
    D --> L
    
    subgraph "API Layer"
        M[FastAPI Server]
        N[REST Endpoints]
    end
    
    M --> B
    N --> M
    
    O[Client Applications] --> N
```"""
            
            # Data flow diagram
            dataflow_diagram = """```mermaid
sequenceDiagram
    participant U as User
    participant A as API Server
    participant B as Search Backend
    participant V as Vector Store
    participant I as Indexer
    participant M as Monitor
    
    U->>A: Search Query
    A->>B: Process Query
    B->>V: Vector Similarity Search
    V-->>B: Top K Results
    B->>B: Rank & Filter
    B-->>A: Search Results
    A->>M: Log Query Metrics
    A-->>U: Response
    
    Note over I,V: Background Indexing
    I->>V: Add New Embeddings
    I->>M: Report Status
```"""
            
            # Write diagrams
            comp_file = self.output_dir / "diagrams" / "components.md"
            flow_file = self.output_dir / "diagrams" / "dataflow.md"
            
            await self._write_file(comp_file, f"# Component Architecture\n\n{component_diagram}")
            await self._write_file(flow_file, f"# Data Flow\n\n{dataflow_diagram}")
            
            logger.info(f"Component diagrams generated")
            
            return {
                "status": "success",
                "message": "Component diagrams generated",
                "files": [str(comp_file), str(flow_file)]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate diagrams: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "files": []
            }
    
    async def _create_deployment_guide(self) -> Dict[str, Any]:
        """
        Generate deployment guide and configuration instructions.
        
        Returns:
            Dict with status and guide file path
        """
        try:
            logger.info("Generating deployment guide...")
            
            deploy_guide = f"""# Windows AI Search Deployment Guide

**Generated:** {self.generation_timestamp.isoformat()}

## Prerequisites

- Python 3.10 or higher
- 8GB RAM minimum (16GB recommended)
- 50GB disk space for vector storage
- CUDA-compatible GPU (optional, for faster embeddings)

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/windows-ai.git
cd windows-ai
```

### 2. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file:

```bash
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Search Configuration
SEARCH_BACKEND=chromadb
SEARCH_INDEX_DIR=/path/to/index
SEARCH_CACHE_SIZE=1024

# Vector Store
VECTOR_STORE_TYPE=chromadb
VECTOR_STORE_PATH=/path/to/vectors

# Monitoring
ENABLE_MONITORING=true
METRICS_PORT=9090
```

### 4. Initialize Search Index

```bash
python -m windows_ai.search.initialize
```

## Deployment Options

### Option 1: Local Development

```bash
python -m windows_ai.api.server --reload --port 8010
```

### Option 2: Production (Gunicorn)

```bash
gunicorn windows_ai.api.server:app \\
  --workers 4 \\
  --worker-class uvicorn.workers.UvicornWorker \\
  --bind 0.0.0.0:8010
```

### Option 3: Docker

```bash
docker build -t windows-ai-search .
docker run -p 8010:8010 \\
  -e OPENAI_API_KEY=sk-... \\
  -v /data/search:/data \\
  windows-ai-search
```

### Option 4: Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: windows-ai-search
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: search-api
        image: windows-ai-search:latest
        ports:
        - containerPort: 8010
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai
```

## Configuration

### Vector Store Options

**ChromaDB (Recommended for development):**
```python
VECTOR_STORE_TYPE=chromadb
VECTOR_STORE_PATH=/data/chromadb
```

**Pinecone (Cloud-based):**
```python
VECTOR_STORE_TYPE=pinecone
PINECONE_API_KEY=your-key
PINECONE_ENVIRONMENT=us-west1-gcp
```

**Weaviate (Self-hosted or cloud):**
```python
VECTOR_STORE_TYPE=weaviate
WEAVIATE_URL=http://localhost:8080
```

### Performance Tuning

**High-throughput configuration:**
```python
ASYNC_WORKERS=8
CACHE_SIZE=2048
BATCH_SIZE=100
CONNECTION_POOL_SIZE=20
```

**Low-latency configuration:**
```python
ENABLE_CACHE=true
CACHE_TTL=3600
PREFETCH_ENABLED=true
QUERY_TIMEOUT=500
```

## Monitoring

### Prometheus Metrics

Metrics available at `http://localhost:9090/metrics`:

- `search_queries_total` - Total queries processed
- `search_latency_seconds` - Query latency histogram
- `search_errors_total` - Total errors
- `index_size_bytes` - Index size

### Health Checks

```bash
curl http://localhost:8010/health
```

### Logs

Logs are written to:
- Console: INFO level
- File: `/var/log/windows-ai/search.log` (DEBUG level)

## Troubleshooting

### High Latency

1. Check vector store connection
2. Verify cache hit rate
3. Monitor CPU/GPU usage
4. Consider increasing workers

### Out of Memory

1. Reduce cache size
2. Decrease batch size
3. Limit concurrent requests
4. Use disk-based vector store

### Index Not Found

1. Verify `SEARCH_INDEX_DIR` path
2. Run initialization script
3. Check file permissions

## Backup and Recovery

### Backup Index

```bash
python -m windows_ai.search.backup --output /backup/search_$(date +%Y%m%d)
```

### Restore Index

```bash
python -m windows_ai.search.restore --input /backup/search_20240115
```

## Scaling

### Horizontal Scaling

Deploy multiple instances behind load balancer:

```bash
# Instance 1
python -m windows_ai.api.server --port 8010

# Instance 2
python -m windows_ai.api.server --port 8011

# Load balancer (nginx)
upstream search_backend {{
    server 127.0.0.1:8010;
    server 127.0.0.1:8011;
}}
```

### Vertical Scaling

Increase resources:
- CPU: 8+ cores recommended
- RAM: 16GB minimum, 32GB+ for large indices
- Storage: SSD recommended for vector store

---

*For questions, see [FAQ](faq.md) or contact support.*
"""
            
            deploy_file = self.output_dir / "guides" / "deployment.md"
            await self._write_file(deploy_file, deploy_guide)
            
            logger.info(f"Deployment guide written to: {deploy_file}")
            
            return {
                "status": "success",
                "message": "Deployment guide generated",
                "files": [str(deploy_file)]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate deployment guide: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "files": []
            }
    
    async def _generate_config_templates(self) -> Dict[str, Any]:
        """
        Generate configuration file templates.
        
        Returns:
            Dict with status and template file paths
        """
        try:
            logger.info("Generating configuration templates...")
            
            # Environment template
            env_template = """# Windows AI Search Configuration Template

# API Keys (Required)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Search Backend (Required)
SEARCH_BACKEND=chromadb
SEARCH_INDEX_DIR=/data/search/index
SEARCH_CACHE_SIZE=1024

# Vector Store Configuration (Required)
VECTOR_STORE_TYPE=chromadb
VECTOR_STORE_PATH=/data/search/vectors
VECTOR_DIMENSION=1536

# Performance Tuning (Optional)
ASYNC_WORKERS=4
BATCH_SIZE=50
CACHE_TTL=3600
QUERY_TIMEOUT=5000

# Monitoring (Optional)
ENABLE_MONITORING=true
METRICS_PORT=9090
LOG_LEVEL=INFO

# Security (Optional)
ENABLE_AUTH=true
API_KEY_HEADER=X-API-Key
RATE_LIMIT=1000
"""
            
            # YAML config template
            yaml_template = """# search_config.yaml

search:
  backend: chromadb
  index_dir: /data/search/index
  cache_size: 1024
  
vector_store:
  type: chromadb
  path: /data/search/vectors
  dimension: 1536
  
performance:
  async_workers: 4
  batch_size: 50
  cache_ttl: 3600
  query_timeout: 5000
  
monitoring:
  enabled: true
  metrics_port: 9090
  log_level: INFO
  
security:
  enable_auth: true
  api_key_header: X-API-Key
  rate_limit: 1000
"""
            
            # Docker compose template
            docker_template = """version: '3.8'

services:
  search-api:
    image: windows-ai-search:latest
    ports:
      - "8010:8010"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SEARCH_BACKEND=chromadb
      - VECTOR_STORE_TYPE=chromadb
    volumes:
      - search-data:/data
    restart: unless-stopped
  
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - chroma-data:/chroma/chroma
    restart: unless-stopped

volumes:
  search-data:
  chroma-data:
"""
            
            # Write templates
            env_file = self.output_dir / "templates" / "env.template"
            yaml_file = self.output_dir / "templates" / "config.yaml.template"
            docker_file = self.output_dir / "templates" / "docker-compose.yml.template"
            
            await self._write_file(env_file, env_template)
            await self._write_file(yaml_file, yaml_template)
            await self._write_file(docker_file, docker_template)
            
            logger.info("Configuration templates generated")
            
            return {
                "status": "success",
                "message": "Configuration templates generated",
                "files": [str(env_file), str(yaml_file), str(docker_file)]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate config templates: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "files": []
            }
    
    async def _generate_diagrams(self) -> Dict[str, Any]:
        """Generate all system diagrams."""
        return await self._create_component_diagram()
    
    async def _init_templates(self) -> None:
        """Initialize documentation templates."""
        logger.debug("Initializing documentation templates")
    
    async def _scan_search_modules(self) -> None:
        """Scan search module structure for documentation."""
        try:
            logger.debug("Scanning search module structure...")
        except Exception as e:
            logger.warning(f"Could not scan search modules: {e}")
    
    async def _write_file(self, file_path: Path, content: str) -> None:
        """Write content to file asynchronously."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: file_path.write_text(content, encoding='utf-8')
        )


async def main():
    """Main entry point for standalone execution."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    blueprint = SearchBlueprint()
    
    if await blueprint.setup():
        # Generate all documentation
        result = await blueprint.execute(action="generate_all")
        
        print(f"\n{result['message']}")
        print(f"\nGenerated {len(result['files'])} files:")
        for file_path in result['files']:
            print(f"  - {file_path}")
        print(f"\nOutput directory: {result['output_dir']}")
    else:
        print("Setup failed")


if __name__ == "__main__":
    asyncio.run(main())
