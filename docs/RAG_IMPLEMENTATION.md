# RAG Implementation Documentation

Complete documentation for the Windows-AI Retrieval-Augmented Generation (RAG) system.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Vector Databases](#vector-databases)
4. [Embedding Generation](#embedding-generation)
5. [Document Processing](#document-processing)
6. [RAG Query Engine](#rag-query-engine)
7. [API Endpoints](#api-endpoints)
8. [Configuration](#configuration)
9. [Usage Examples](#usage-examples)
10. [Performance](#performance)
11. [Troubleshooting](#troubleshooting)

## Overview

The Windows-AI RAG system provides production-ready semantic search and document retrieval capabilities with support for multiple vector databases, embedding providers, and intelligent document processing.

### Key Features

- **Multiple Vector Databases**: Pinecone, Chroma, FAISS, Weaviate
- **Flexible Embeddings**: OpenAI, Ollama, SentenceTransformers
- **Smart Document Processing**: PDF, DOCX, TXT, MD, JSON, CSV, HTML
- **Advanced Retrieval**: Re-ranking with MMR and cross-encoders
- **REST API**: Complete FastAPI integration
- **Streaming Support**: Real-time query responses
- **Production Ready**: Async, caching, error handling

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       RAG API Layer                          │
│  POST /rag/index  |  POST /rag/query  |  GET /rag/stream   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    RAG Engine                                │
│  • Query Processing    • Context Building                    │
│  • Retrieval Logic     • Re-ranking                          │
└────────┬──────────────────────────┬──────────────────────────┘
         │                          │
┌────────▼───────────┐   ┌─────────▼──────────┐
│  Embedding Models  │   │  Vector Databases  │
│  • OpenAI          │   │  • Pinecone        │
│  • Ollama          │   │  • Chroma          │
│  • SentenceTransf  │   │  • FAISS           │
│  • Caching         │   │  • Weaviate        │
└────────────────────┘   └────────────────────┘
         │
┌────────▼──────────────────────────────────────┐
│         Document Processor                    │
│  • Multi-format readers                       │
│  • Intelligent chunking                       │
│  • Metadata extraction                        │
└───────────────────────────────────────────────┘
```

## Vector Databases

### Supported Providers

#### 1. Pinecone (Cloud)

**Best for**: Production cloud deployments, serverless applications

```python
from windows_ai.vector_db import VectorDBManager, VectorDBConfig, VectorDBType

config = VectorDBConfig(
    db_type=VectorDBType.PINECONE,
    dimension=1536,
    api_key="your-api-key",
    url="us-east-1-aws"
)

manager = VectorDBManager()
pinecone = manager.get_provider("pinecone", config)
await pinecone.connect()
```

**Features**:
- Fully managed cloud service
- Auto-scaling
- Serverless and pod-based options
- Multi-region support
- High availability

**Configuration**:
```bash
export PINECONE_API_KEY="your-key"
export PINECONE_ENVIRONMENT="us-east-1-aws"
```

#### 2. ChromaDB (Local/Cloud)

**Best for**: Development, local-first applications, self-hosted

```python
config = VectorDBConfig(
    db_type=VectorDBType.CHROMA,
    dimension=1536,
    persist_directory="./chroma_db"
)

chroma = manager.get_provider("chroma", config)
await chroma.connect()
```

**Features**:
- Local persistent storage
- No external dependencies
- Fast development iteration
- Optional cloud hosting
- Built-in embedding functions

**Configuration**:
```bash
export CHROMA_PERSIST_DIR="./chroma_db"
```

#### 3. FAISS (Local)

**Best for**: High-performance local search, research, prototyping

```python
config = VectorDBConfig(
    db_type=VectorDBType.FAISS,
    dimension=1536,
    persist_directory="./faiss_db"
)

faiss_db = manager.get_provider("faiss", config)
await faiss_db.connect()
```

**Features**:
- Facebook's similarity search library
- Multiple index types (Flat, IVF, HNSW)
- GPU acceleration support
- Extremely fast search
- Complete offline operation

**Index Types**:
- `Flat`: Exact search, best for <1M vectors
- `IVF`: Inverted file index, 10-100x faster
- `HNSW`: Hierarchical graphs, best quality/speed trade-off

#### 4. Weaviate (Cloud/Self-hosted)

**Best for**: Production scale, hybrid search, GraphQL queries

```python
config = VectorDBConfig(
    db_type=VectorDBType.WEAVIATE,
    dimension=1536,
    url="http://localhost:8080",
    api_key="your-key"  # Optional for cloud
)

weaviate = manager.get_provider("weaviate", config)
await weaviate.connect()
```

**Features**:
- GraphQL API
- Hybrid search (vector + keyword)
- Auto-schema generation
- Multi-tenancy support
- RESTful and GraphQL interfaces

**Configuration**:
```bash
export WEAVIATE_URL="http://localhost:8080"
export WEAVIATE_API_KEY="your-key"
```

### Comparison Matrix

| Feature | Pinecone | Chroma | FAISS | Weaviate |
|---------|----------|--------|-------|----------|
| **Deployment** | Cloud | Local/Cloud | Local | Cloud/Self-hosted |
| **Setup Complexity** | Low | Very Low | Low | Medium |
| **Cost** | Paid | Free | Free | Free/Paid |
| **Scale** | Millions+ | Hundreds of thousands | Millions+ | Millions+ |
| **Hybrid Search** | No | Limited | No | Yes |
| **Metadata Filtering** | Yes | Yes | Limited | Yes |
| **Performance** | Very High | High | Extreme | Very High |
| **Persistence** | Built-in | Built-in | Manual | Built-in |
| **Best Use Case** | Production SaaS | Development | Research | Production |

## Embedding Generation

### Supported Providers

#### 1. OpenAI Embeddings

**Models**:
- `text-embedding-3-small` (1536d) - Fast and cost-effective
- `text-embedding-3-large` (3072d) - Highest quality
- `text-embedding-ada-002` (1536d) - Previous generation

```python
from windows_ai.embeddings import get_embedding_model

# Get OpenAI model
model = get_embedding_model("openai")

# Generate embeddings
texts = ["Document 1", "Document 2"]
embeddings = await model.embed(texts)

# Single text
single_embedding = await model.embed("Single document")
```

**Configuration**:
```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_EMBEDDING_MODEL="text-embedding-3-small"
```

**Pros**:
- Highest quality embeddings
- Excellent multilingual support
- Large context window (8191 tokens)
- Production-grade reliability

**Cons**:
- API costs
- Network latency
- Rate limits

#### 2. Ollama Embeddings (Local)

**Models**:
- `nomic-embed-text` (768d) - Best open-source model
- `mxbai-embed-large` (1024d) - High quality
- `all-minilm` (384d) - Lightweight

```python
from windows_ai.embeddings import OllamaEmbedding, EmbeddingConfig

config = EmbeddingConfig(
    provider="ollama",
    model_name="nomic-embed-text",
    dimension=768,
    base_url="http://localhost:11434"
)

model = OllamaEmbedding(config)
embeddings = await model.embed(texts)
```

**Configuration**:
```bash
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_EMBEDDING_MODEL="nomic-embed-text"

# Install model
ollama pull nomic-embed-text
```

**Pros**:
- No API costs
- Complete privacy
- No rate limits
- Fast local inference

**Cons**:
- Lower quality than OpenAI
- Requires local resources
- Smaller context window

#### 3. SentenceTransformers (Local)

**Models**:
- `all-MiniLM-L6-v2` (384d) - Fastest
- `all-mpnet-base-v2` (768d) - Best quality
- `paraphrase-multilingual-MiniLM-L12-v2` (384d) - Multilingual

```python
from windows_ai.embeddings import SentenceTransformerEmbedding

model = SentenceTransformerEmbedding()
embeddings = await model.embed(texts)
```

**Pros**:
- Completely offline
- Wide model selection
- Fine-tuning support
- Multilingual models

**Cons**:
- Lower quality than OpenAI
- CPU/GPU requirements
- Model download required

### Embedding Caching

All embedding models include intelligent caching:

```python
from windows_ai.embeddings import EmbeddingCache

# Cache configuration
cache = EmbeddingCache(
    cache_directory="./embedding_cache",
    enabled=True
)

# Cache statistics
stats = cache.get_stats()
print(f"Memory cache: {stats['memory_cache_size']} entries")
print(f"Disk cache: {stats['disk_cache_files']} files")

# Clear cache
cache.clear()
```

**Features**:
- Two-tier caching (memory + disk)
- SHA-256 content-based keys
- Automatic expiration
- Per-model caching
- Significant cost savings

## Document Processing

### Supported File Formats

#### Text Formats
- **TXT**: Plain text files (UTF-8, Latin-1)
- **MD/Markdown**: Markdown documents

#### Office Formats
- **PDF**: Adobe PDF documents
- **DOCX**: Microsoft Word documents

#### Data Formats
- **JSON**: Structured JSON data
- **CSV**: Comma-separated values
- **HTML**: Web pages and HTML documents

### Chunking Strategies

#### 1. Fixed Size (Default)

Best for: General purpose, consistent chunk sizes

```python
from windows_ai.document_processor import DocumentProcessor, ChunkConfig, ChunkStrategy

config = ChunkConfig(
    strategy=ChunkStrategy.FIXED_SIZE,
    chunk_size=512,
    chunk_overlap=50,
    respect_sentences=True
)

processor = DocumentProcessor(config)
document, chunks = processor.process_file("document.pdf")
```

**Parameters**:
- `chunk_size`: Target size in characters (default: 512)
- `chunk_overlap`: Overlap between chunks (default: 50)
- `respect_sentences`: End at sentence boundaries (default: True)

#### 2. Semantic Chunking

Best for: Maintaining context, narrative documents

```python
config = ChunkConfig(
    strategy=ChunkStrategy.SEMANTIC,
    max_chunk_size=2000,
    min_chunk_size=100
)
```

**Features**:
- Respects paragraph boundaries
- Groups related content
- Maintains semantic coherence
- Variable chunk sizes

#### 3. Sentence-based

Best for: Question answering, precise retrieval

```python
config = ChunkConfig(
    strategy=ChunkStrategy.SENTENCE,
    chunk_size=512
)
```

#### 4. Paragraph-based

Best for: Long-form content, articles

```python
config = ChunkConfig(
    strategy=ChunkStrategy.PARAGRAPH,
    max_chunk_size=2000
)
```

#### 5. Sliding Window

Best for: Dense content, overlapping context

```python
config = ChunkConfig(
    strategy=ChunkStrategy.SLIDING_WINDOW,
    chunk_size=512,
    chunk_overlap=100
)
```

### Processing Files

#### Single File

```python
processor = DocumentProcessor()

# Process single file
document, chunks = processor.process_file("document.pdf")

print(f"File: {document.file_path}")
print(f"Type: {document.file_type}")
print(f"Chunks: {len(chunks)}")
print(f"Content length: {document.metadata['content_length']}")
```

#### Directory Processing

```python
# Process entire directory
results = processor.process_directory(
    directory_path="./documents",
    recursive=True,
    file_patterns=["*.pdf", "*.docx", "*.txt"]
)

for document, chunks in results:
    print(f"Processed: {document.file_path} -> {len(chunks)} chunks")
```

### Metadata Extraction

Automatic metadata extraction includes:

```python
metadata = document.metadata
# {
#     "file_name": "document.pdf",
#     "file_path": "/path/to/document.pdf",
#     "file_type": "pdf",
#     "file_size": 102400,
#     "created_at": "2024-01-15T10:30:00",
#     "modified_at": "2024-01-15T14:22:00",
#     "content_length": 5000,
#     "word_count": 850,
#     "line_count": 120,
#     "has_code": false,
#     "has_urls": true,
#     "has_emails": false,
#     "language": "english"
# }
```

## RAG Query Engine

### Basic Setup

```python
from windows_ai.rag import RAGEngine, RAGConfig, RerankStrategy
from windows_ai.embeddings import get_embedding_model
from windows_ai.vector_db import VectorDBManager

# Setup components
embedding_model = get_embedding_model("openai")
vector_db = VectorDBManager().get_provider("chroma")

# Configure RAG
config = RAGConfig(
    index_name="my_docs",
    top_k=10,
    rerank_top_k=5,
    rerank_strategy=RerankStrategy.MMR,
    mmr_lambda=0.7
)

# Create engine
engine = RAGEngine(
    vector_db=vector_db,
    embedding_model=embedding_model,
    config=config
)
```

### Indexing Documents

```python
# Prepare documents
documents = [
    {
        "content": "Document 1 content...",
        "metadata": {"source": "file1.pdf", "page": 1}
    },
    {
        "content": "Document 2 content...",
        "metadata": {"source": "file2.pdf", "page": 1}
    }
]

# Index documents
result = await engine.index_documents(documents, batch_size=100)
print(f"Indexed {result['upserted']} documents")
```

### Querying

#### Simple Retrieval

```python
# Retrieve relevant documents
results = await engine.retrieve(
    query="What is machine learning?",
    top_k=5,
    rerank=True
)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Content: {result.content[:200]}...")
    print(f"Source: {result.metadata.get('source')}")
    print()
```

#### Full RAG Query

```python
# Query with generation
response = await engine.query(
    query="Explain machine learning",
    system_prompt="You are a helpful AI assistant."
)

print(f"Question: {response.query}")
print(f"Answer: {response.answer}")
print(f"Sources used: {len(response.sources)}")
print(f"Retrieval time: {response.retrieval_time:.2f}s")
print(f"Generation time: {response.generation_time:.2f}s")
```

#### Streaming Queries

```python
# Stream response
async for chunk in engine.query_stream(query="What is AI?"):
    if chunk["type"] == "sources":
        print(f"Found {len(chunk['sources'])} sources")
    elif chunk["type"] == "content":
        print(chunk["content"], end="", flush=True)
    elif chunk["type"] == "done":
        print("\n\nDone!")
```

### Re-ranking Strategies

#### MMR (Maximal Marginal Relevance)

Balances relevance with diversity:

```python
config = RAGConfig(
    rerank_strategy=RerankStrategy.MMR,
    mmr_lambda=0.7  # 1.0 = pure relevance, 0.0 = pure diversity
)
```

#### Cross-Encoder

Uses transformer models for re-ranking:

```python
config = RAGConfig(
    rerank_strategy=RerankStrategy.CROSS_ENCODER
)
```

### Hybrid Search

Combine vector and keyword search:

```python
config = RAGConfig(
    use_hybrid_search=True,
    hybrid_alpha=0.7  # 1.0 = pure vector, 0.0 = pure keyword
)
```

## API Endpoints

### Document Indexing

#### Index Text Documents

```bash
POST /rag/index
Content-Type: application/json

{
  "collection_name": "my_docs",
  "documents": [
    "Document 1 content",
    "Document 2 content"
  ],
  "metadata": [
    {"source": "doc1.txt"},
    {"source": "doc2.txt"}
  ],
  "chunk_strategy": "semantic",
  "chunk_size": 512,
  "embedding_provider": "openai",
  "vector_db_provider": "chroma"
}
```

#### Index Files from Directory

```bash
POST /rag/index/files
Content-Type: application/json

{
  "collection_name": "documents",
  "directory_path": "/path/to/docs",
  "recursive": true,
  "file_patterns": ["*.pdf", "*.docx"],
  "chunk_strategy": "semantic",
  "embedding_provider": "openai",
  "vector_db_provider": "faiss"
}
```

#### Upload Single File

```bash
POST /rag/upload?collection_name=docs
Content-Type: multipart/form-data

file: @document.pdf
```

### Querying

#### Standard Query

```bash
POST /rag/query
Content-Type: application/json

{
  "collection_name": "my_docs",
  "query": "What is machine learning?",
  "top_k": 5,
  "rerank": true,
  "rerank_strategy": "mmr",
  "use_hybrid_search": false
}
```

Response:
```json
{
  "query": "What is machine learning?",
  "answer": "Machine learning is...",
  "sources": [
    {
      "content": "Machine learning is a subset of AI...",
      "score": 0.89,
      "metadata": {"source": "ml_intro.pdf", "page": 1}
    }
  ],
  "retrieval_time": 0.15,
  "generation_time": 1.2
}
```

#### Streaming Query

```bash
GET /rag/query/stream?collection_name=docs&query=What+is+AI&top_k=5
```

Response (Server-Sent Events):
```
data: {"type": "sources", "sources": [...]}

data: {"type": "content", "content": "AI is"}

data: {"type": "content", "content": " a field"}

data: {"type": "done"}
```

### Collection Management

#### List Collections

```bash
GET /rag/collections?vector_db_provider=chroma
```

Response:
```json
[
  {
    "name": "my_docs",
    "vector_count": 1500,
    "dimension": 1536,
    "metadata": {}
  }
]
```

#### Delete Collection

```bash
DELETE /rag/collections/my_docs?vector_db_provider=chroma
```

### Health Check

```bash
GET /rag/health
```

Response:
```json
{
  "status": "healthy",
  "active_engines": 2,
  "available_providers": ["chroma", "faiss", "pinecone"]
}
```

## Configuration

### Environment Variables

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."
export OPENAI_EMBEDDING_MODEL="text-embedding-3-small"

# Ollama
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_EMBEDDING_MODEL="nomic-embed-text"

# Vector Databases
export PINECONE_API_KEY="..."
export PINECONE_ENVIRONMENT="us-east-1-aws"
export CHROMA_PERSIST_DIR="./chroma_db"
export FAISS_PERSIST_DIR="./faiss_db"
export WEAVIATE_URL="http://localhost:8080"
export WEAVIATE_API_KEY="..."
```

### Programmatic Configuration

```python
from windows_ai.vector_db import VectorDBConfig, VectorDBType, MetricType
from windows_ai.embeddings import EmbeddingConfig, EmbeddingProvider
from windows_ai.rag import RAGConfig, RerankStrategy

# Vector DB configuration
vdb_config = VectorDBConfig(
    db_type=VectorDBType.FAISS,
    dimension=1536,
    metric=MetricType.COSINE,
    persist_directory="./my_faiss_db",
    batch_size=100,
    timeout=30
)

# Embedding configuration
emb_config = EmbeddingConfig(
    provider=EmbeddingProvider.OPENAI,
    model_name="text-embedding-3-small",
    dimension=1536,
    batch_size=100,
    cache_enabled=True,
    cache_directory="./embedding_cache"
)

# RAG configuration
rag_config = RAGConfig(
    index_name="my_index",
    top_k=10,
    rerank_top_k=5,
    rerank_strategy=RerankStrategy.MMR,
    mmr_lambda=0.7,
    use_hybrid_search=False,
    hybrid_alpha=0.7,
    context_window=3
)
```

## Usage Examples

### Example 1: Index Local Documents

```python
import asyncio
from windows_ai.rag import RAGEngine, RAGConfig
from windows_ai.embeddings import get_embedding_model
from windows_ai.vector_db import VectorDBManager
from windows_ai.document_processor import DocumentProcessor

async def index_documents():
    # Setup
    embedding_model = get_embedding_model("openai")
    vector_db = VectorDBManager().get_provider("chroma")
    await vector_db.connect()

    config = RAGConfig(index_name="local_docs")
    engine = RAGEngine(vector_db, embedding_model, config=config)

    # Process documents
    processor = DocumentProcessor()
    results = processor.process_directory("./documents", recursive=True)

    # Prepare for indexing
    documents = []
    for doc, chunks in results:
        for chunk in chunks:
            documents.append({
                "content": chunk.content,
                "metadata": chunk.metadata
            })

    # Index
    result = await engine.index_documents(documents)
    print(f"Indexed {result['upserted']} chunks")

asyncio.run(index_documents())
```

### Example 2: Query with Custom Prompt

```python
async def query_with_custom_prompt():
    # Setup engine
    engine = get_rag_engine("local_docs")

    # Custom system prompt
    system_prompt = """You are a technical documentation assistant.
    Answer questions based on the provided context.
    Be precise and cite sources when possible."""

    # Query
    response = await engine.query(
        query="How do I configure the RAG system?",
        system_prompt=system_prompt
    )

    print(response.answer)
    print(f"\nSources ({len(response.sources)}):")
    for i, source in enumerate(response.sources, 1):
        print(f"{i}. {source.metadata.get('file_name')} (score: {source.score:.3f})")

asyncio.run(query_with_custom_prompt())
```

### Example 3: FastAPI Integration

```python
from fastapi import FastAPI
from windows_ai.rag.api import router as rag_router

app = FastAPI(title="My RAG API")

# Include RAG routes
app.include_router(rag_router)

# Custom route
@app.get("/")
async def root():
    return {"message": "RAG API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Performance

### Benchmarks

Tested on: Intel i7, 16GB RAM, without GPU

| Operation | Provider | Time | Notes |
|-----------|----------|------|-------|
| Embed 100 docs | OpenAI | ~2.5s | API latency |
| Embed 100 docs | Ollama | ~8s | Local CPU |
| Embed 100 docs | SentenceTransformers | ~3s | Local CPU |
| Search 10k vectors | FAISS | ~5ms | Exact search |
| Search 10k vectors | Chroma | ~15ms | Persistent |
| Search 1M vectors | FAISS (IVF) | ~50ms | Approximate |
| Index 1000 chunks | Chroma | ~45s | Including embeddings |
| Query + Generate | End-to-end | ~3s | With OpenAI |

### Optimization Tips

1. **Use FAISS for Large Collections**
   - 10x faster than Chroma for 100k+ vectors
   - Use IVF or HNSW indexes
   - Consider GPU acceleration

2. **Enable Embedding Caching**
   - Saves API costs
   - Reduces latency for repeated texts
   - Configure cache directory on fast storage

3. **Batch Processing**
   - Use batch_size=100 for indexing
   - Parallel processing for multiple files
   - Async operations throughout

4. **Choose Right Chunking Strategy**
   - Semantic for quality (slower)
   - Fixed-size for speed (faster)
   - Balance chunk_size: 512 is sweet spot

5. **Use Local Embeddings for Dev**
   - Ollama for development
   - OpenAI for production
   - SentenceTransformers for offline

## Troubleshooting

### Common Issues

#### 1. "Pinecone not configured"

**Cause**: Missing API key

**Solution**:
```bash
export PINECONE_API_KEY="your-key"
```

#### 2. "Dimension mismatch"

**Cause**: Index dimension doesn't match embedding dimension

**Solution**:
```python
# Ensure matching dimensions
embedding_dimension = 1536  # For text-embedding-3-small
config = VectorDBConfig(dimension=embedding_dimension)
```

#### 3. "FAISS not available"

**Cause**: FAISS not installed

**Solution**:
```bash
pip install faiss-cpu  # or faiss-gpu
```

#### 4. "PDF reading error"

**Cause**: PyPDF2 not installed

**Solution**:
```bash
pip install PyPDF2
```

#### 5. "Slow query performance"

**Solutions**:
- Reduce top_k parameter
- Use FAISS with IVF index
- Disable re-ranking for speed
- Enable embedding caching

#### 6. "Out of memory"

**Solutions**:
- Reduce batch_size
- Process files in smaller batches
- Use streaming queries
- Increase system RAM

### Debug Mode

Enable detailed logging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Health Checks

```python
# Check vector database
await vector_db.health_check()

# Check embedding cache
cache_stats = embedding_model.cache.get_stats()
print(cache_stats)

# Check RAG engine
results = await engine.retrieve("test query", top_k=1)
assert len(results) > 0
```

## Dependencies

### Required

```bash
pip install fastapi pydantic
pip install httpx  # For Ollama
```

### Vector Databases

```bash
pip install pinecone-client  # Pinecone
pip install chromadb          # Chroma
pip install faiss-cpu         # FAISS (CPU)
pip install faiss-gpu         # FAISS (GPU)
pip install weaviate-client   # Weaviate
```

### Embeddings

```bash
pip install openai                  # OpenAI
pip install sentence-transformers   # SentenceTransformers & CrossEncoder
```

### Document Processing

```bash
pip install PyPDF2              # PDF support
pip install python-docx         # DOCX support
pip install beautifulsoup4      # HTML support
```

### All Dependencies

```bash
pip install fastapi pydantic httpx \
    pinecone-client chromadb faiss-cpu weaviate-client \
    openai sentence-transformers \
    PyPDF2 python-docx beautifulsoup4
```

## Conclusion

The Windows-AI RAG system provides a complete, production-ready solution for semantic search and document retrieval. With support for multiple providers, intelligent processing, and comprehensive APIs, it's suitable for both development and production deployments.

For issues or questions, please refer to the troubleshooting section or open an issue on GitHub.
