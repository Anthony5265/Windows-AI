# Ollama Integration Technical Documentation

Comprehensive technical documentation for Windows-AI's Ollama integration, covering architecture, API reference, and advanced features.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Plugin System](#plugin-system)
3. [Model Manager](#model-manager)
4. [API Reference](#api-reference)
5. [WebSocket Protocol](#websocket-protocol)
6. [RAG Implementation](#rag-implementation)
7. [Advanced Usage](#advanced-usage)
8. [Development Guide](#development-guide)

## Architecture Overview

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Windows-AI Frontend                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Chat UI     │  │  Models Tab  │  │  Settings    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │ HTTP/WebSocket
          ┌──────────────────┼──────────────────┐
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────────┐
│              Windows-AI Backend (FastAPI)                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   FastAPI Endpoints                     │ │
│  │  /models/* | /chat | /plugins | /ws/models/download   │ │
│  └──────┬──────────────┬──────────────┬───────────────────┘ │
│         │              │              │                      │
│  ┌──────▼──────┐ ┌─────▼──────┐ ┌────▼──────────────────┐  │
│  │   Model     │ │   Ollama   │ │   Plugin Registry     │  │
│  │   Manager   │ │   Plugin   │ │                       │  │
│  └──────┬──────┘ └─────┬──────┘ └───────────────────────┘  │
└─────────┼──────────────┼──────────────────────────────────┘
          │              │
          │              │ HTTP (localhost:11434)
          │              │
          │    ┌─────────▼─────────┐
          │    │   Ollama Service   │
          │    │   (Local Server)   │
          │    └─────────┬─────────┘
          │              │
          │    ┌─────────▼─────────┐
          │    │   Local Models     │
          │    │  (~/.ollama/...)   │
          │    └───────────────────┘
          │
    ┌─────▼──────┐
    │ System Specs│
    │ Detection   │
    └────────────┘
```

### Data Flow

1. **Model Discovery**: Frontend → Backend → Model Manager → Catalog
2. **Model Download**: Frontend → WebSocket → Model Manager → Ollama API
3. **Inference**: Frontend → Backend → Ollama Plugin → Ollama Service → Model
4. **System Detection**: Model Manager → psutil/subprocess → Hardware Info

## Plugin System

### Ollama Plugin Architecture

**File**: `windows_ai/plugins/builtin/ollama_plugin.py`

```python
class Plugin:
    """Production-grade Ollama plugin"""

    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.conversation_history = {}
        self.available_models = []

    async def execute(self, action: str, **kwargs):
        """Route actions to handlers"""
        pass
```

### Available Actions

| Action | Description | Parameters |
|--------|-------------|------------|
| `list_models` | List installed models | None |
| `pull_model` | Download a model | `model` |
| `delete_model` | Remove a model | `model` |
| `show_model` | Get model info | `model` |
| `chat` | Chat with history | `model`, `message`, `conversation_id`, `stream`, `temperature`, `system_prompt` |
| `generate` | Text completion | `model`, `prompt`, `stream`, `temperature` |
| `embeddings` | Generate embeddings | `model`, `text` |
| `batch_embeddings` | Batch embeddings | `model`, `texts[]`, `batch_size` |
| `rag_query` | RAG-based query | `query`, `documents[]`, `model`, `embed_model`, `top_k` |
| `check_status` | Health check | None |

### Plugin Usage Examples

#### Basic Chat
```python
from windows_ai.plugins.builtin.ollama_plugin import Plugin

plugin = Plugin()

# Simple chat
result = await plugin.execute(
    action='chat',
    model='llama3.2:3b',
    message='Explain photosynthesis'
)

print(result['response'])
```

#### Chat with Conversation History
```python
# Multi-turn conversation
conversation_id = 'conv-123'

# First message
result1 = await plugin.execute(
    action='chat',
    model='llama3.2:3b',
    message='What is Python?',
    conversation_id=conversation_id
)

# Follow-up (remembers context)
result2 = await plugin.execute(
    action='chat',
    model='llama3.2:3b',
    message='What are its main features?',
    conversation_id=conversation_id
)

# Clear history
plugin.clear_conversation(conversation_id)
```

#### Streaming Response
```python
result = await plugin.execute(
    action='chat',
    model='llama3.2:3b',
    message='Write a story about a robot',
    stream=True
)
```

#### Custom System Prompt
```python
result = await plugin.execute(
    action='chat',
    model='llama3.2:3b',
    message='Explain recursion',
    system_prompt='You are a computer science professor. Explain concepts clearly with examples.'
)
```

## Model Manager

### ModelManager Class

**File**: `windows_ai/model_manager.py`

```python
class ModelManager:
    """Manages AI model downloads and installations"""

    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or Path.home() / ".windows-ai" / "models"
        self.ollama_url = "http://localhost:11434"
        self.model_catalog = self._load_model_catalog()
        self._system_specs = None
```

### Key Methods

#### System Specs Detection
```python
specs = model_manager.get_system_specs()

# Returns:
{
    "platform": "Linux",
    "ram_total_gb": 16.0,
    "ram_available_gb": 8.5,
    "cpu_count": 8,
    "cpu_physical_cores": 4,
    "gpu": {
        "available": True,
        "type": "nvidia",
        "name": "NVIDIA GeForce RTX 3060",
        "memory_gb": 12.0,
        "cuda": True
    },
    "disk_free_gb": 250.0
}
```

#### Model Recommendations
```python
recommended = model_manager.get_recommended_models_for_system()

# Returns models suitable for your hardware with suitability scores
[
    {
        "id": "llama3.2:3b",
        "name": "Llama 3.2 3B",
        "suitability": "excellent",  # or "good" / "minimum"
        "gpu_optimized": True,
        ...
    }
]
```

#### List Models
```python
# All available models
available = await model_manager.list_available_models()

# Filter by category
coding = await model_manager.list_available_models(category='coding')

# Recommended only
recommended = await model_manager.list_available_models(recommended_only=True)

# Installed models
installed = await model_manager.list_installed_models()
```

#### Download Model
```python
# Simple download
result = await model_manager.download_model('llama3.2:3b')

# With progress callback
async def progress_handler(percent, downloaded, total):
    print(f"Progress: {percent}% ({downloaded}/{total} bytes)")

result = await model_manager.download_model(
    'llama3.2:3b',
    progress_callback=progress_handler
)
```

#### Model Info
```python
info = await model_manager.get_model_info('llama3.2:3b')

# Returns:
{
    "id": "llama3.2:3b",
    "name": "Llama 3.2 3B",
    "size": "2.0 GB",
    "ram_required": "4 GB",
    "installed": True,
    "category": "general",
    "capabilities": ["chat", "generation"],
    ...
}
```

## API Reference

### REST Endpoints

#### GET /models
List all models (cloud + local)

**Response**:
```json
{
  "models": [
    {
      "id": "gpt-3.5-turbo",
      "name": "GPT-3.5 Turbo",
      "provider": "OpenAI",
      "type": "cloud"
    },
    {
      "id": "ollama/llama3.2:3b",
      "name": "Llama 3.2 3B (Local)",
      "provider": "Ollama",
      "type": "local",
      "size": "2.0 GB"
    }
  ]
}
```

#### GET /models/available
List available models from catalog

**Query Parameters**:
- `category`: Filter by category (optional)
- `recommended_only`: Boolean (optional)

**Response**:
```json
{
  "status": "success",
  "models": [...],
  "count": 12
}
```

#### GET /models/installed
List installed local models

**Response**:
```json
{
  "status": "success",
  "models": [
    {
      "id": "llama3.2:3b",
      "name": "llama3.2:3b",
      "provider": "ollama",
      "size": 2147483648,
      "modified": "2025-11-10T12:00:00Z"
    }
  ],
  "count": 1
}
```

#### GET /models/recommended
Get recommended models for current system

**Response**:
```json
{
  "status": "success",
  "models": [...],
  "count": 5,
  "system_specs": {
    "ram_total_gb": 16.0,
    "gpu": {...}
  }
}
```

#### GET /models/{model_id}
Get detailed model information

**Response**:
```json
{
  "status": "success",
  "model": {
    "id": "llama3.2:3b",
    "name": "Llama 3.2 3B",
    "description": "Fast, general-purpose model...",
    "size": "2.0 GB",
    "ram_required": "4 GB",
    "installed": true,
    ...
  }
}
```

#### POST /models/download
Start model download

**Query Parameters**:
- `model_id`: Model identifier (required)

**Response**:
```json
{
  "status": "success",
  "message": "Started downloading model llama3.2:3b",
  "model_id": "llama3.2:3b"
}
```

#### DELETE /models/{model_id}
Delete an installed model

**Response**:
```json
{
  "status": "success",
  "message": "Model llama3.2:3b deleted successfully"
}
```

#### GET /models/download/{model_id}/status
Get download status

**Response**:
```json
{
  "status": "success",
  "download": {
    "status": "downloading",
    "progress": 45,
    "model": {...}
  }
}
```

#### GET /system/specs
Get system specifications

**Response**:
```json
{
  "status": "success",
  "specs": {
    "platform": "Linux",
    "ram_total_gb": 16.0,
    "cpu_count": 8,
    "gpu": {...}
  }
}
```

## WebSocket Protocol

### Connection URL
```
ws://localhost:8010/ws/models/download
```

### Message Types

#### Client → Server

**Request Download**:
```json
{
  "type": "download",
  "model_id": "llama3.2:3b"
}
```

**Request Status**:
```json
{
  "type": "status",
  "model_id": "llama3.2:3b"
}
```

**Ping**:
```json
{
  "type": "ping"
}
```

#### Server → Client

**Progress Update**:
```json
{
  "type": "progress",
  "model_id": "llama3.2:3b",
  "percent": 45,
  "downloaded": 943718400,
  "total": 2097152000,
  "downloaded_mb": 900.0,
  "total_mb": 2000.0
}
```

**Download Complete**:
```json
{
  "type": "complete",
  "model_id": "llama3.2:3b",
  "status": "success",
  "message": "Download completed"
}
```

**Error**:
```json
{
  "type": "error",
  "model_id": "llama3.2:3b",
  "message": "Download failed: Connection timeout"
}
```

**Pong**:
```json
{
  "type": "pong"
}
```

### JavaScript Example
```javascript
const ws = new WebSocket('ws://localhost:8010/ws/models/download');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'download',
    model_id: 'llama3.2:3b'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'progress') {
    console.log(`Download: ${data.percent}%`);
    updateProgressBar(data.percent);
  } else if (data.type === 'complete') {
    console.log('Download complete!');
    ws.close();
  } else if (data.type === 'error') {
    console.error('Error:', data.message);
  }
};
```

## RAG Implementation

### Architecture

```
User Query → Embedding → Similarity Search → Context Retrieval → LLM with Context → Answer
```

### Basic RAG Query

```python
plugin = Plugin()

documents = [
    "The Eiffel Tower is in Paris, France.",
    "Paris is the capital of France.",
    "France is a country in Europe."
]

result = await plugin.execute(
    action='rag_query',
    query='What is the capital of France?',
    documents=documents,
    model='llama3.2:3b',
    embed_model='nomic-embed-text',
    top_k=2
)

print(result['answer'])
print(result['context'])  # Retrieved chunks
print(result['relevant_chunks'])  # Similarity scores
```

### Advanced RAG with Custom Chunking

```python
# Step 1: Embed documents with custom chunking
embed_result = await plugin.embed_documents_for_rag(
    documents=long_documents,
    model='nomic-embed-text',
    chunk_size=512,  # characters
    overlap=50       # character overlap
)

embeddings = embed_result['embeddings']
chunks = embed_result['chunks']

# Step 2: Embed query
query_result = await plugin.execute(
    action='embeddings',
    model='nomic-embed-text',
    text='My search query'
)

query_embedding = query_result['embeddings']

# Step 3: Find similar chunks
search_result = await plugin.similarity_search(
    query_embedding=query_embedding,
    document_embeddings=embeddings,
    top_k=5
)

# Step 4: Get relevant chunks
relevant_indices = [r['index'] for r in search_result['results']]
relevant_chunks = [chunks[i] for i in relevant_indices]

# Step 5: Generate answer with context
context = '\n\n'.join(relevant_chunks)
prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"

answer = await plugin.execute(
    action='generate',
    model='llama3.2:3b',
    prompt=prompt
)
```

### Batch Embeddings

```python
# Efficient batch processing
texts = ['Document 1', 'Document 2', ..., 'Document 100']

result = await plugin.execute(
    action='batch_embeddings',
    model='nomic-embed-text',
    texts=texts,
    batch_size=10  # Process 10 at a time
)

embeddings = result['embeddings']
print(f"Generated {result['success_count']}/{result['total']} embeddings")
```

## Advanced Usage

### Performance Tuning

#### Context Window Management
```python
# Limit context to prevent slowdowns
MAX_HISTORY = 10
history = conversation_history[-MAX_HISTORY:]
```

#### Temperature Control
```python
# Creative tasks: higher temperature
result = await plugin.execute(
    action='chat',
    model='llama3.2:3b',
    message='Write a creative story',
    temperature=0.9
)

# Factual tasks: lower temperature
result = await plugin.execute(
    action='chat',
    model='llama3.2:3b',
    message='What is 2+2?',
    temperature=0.1
)
```

### Multi-Model Workflows

```python
# Use coding model for code, general model for explanation
async def code_and_explain(task):
    # Generate code
    code = await plugin.execute(
        action='generate',
        model='deepseek-coder:6.7b',
        prompt=f'Write Python code to: {task}'
    )

    # Explain code
    explanation = await plugin.execute(
        action='chat',
        model='llama3.2:3b',
        message=f'Explain this code:\n{code["generated_text"]}'
    )

    return {
        'code': code['generated_text'],
        'explanation': explanation['response']
    }
```

## Development Guide

### Running Tests

```bash
# Run Ollama plugin tests
pytest tests/plugins/test_ollama.py -v

# Run model manager tests
pytest tests/test_model_manager.py -v

# Run all tests
pytest tests/ -v
```

### Adding New Models to Catalog

Edit `windows_ai/model_manager.py`:

```python
{
    "id": "your-model:tag",
    "name": "Your Model Name",
    "provider": "ollama",
    "size": "X.X GB",
    "ram_required": "Y GB",
    "description": "Model description",
    "capabilities": ["chat", "generation"],
    "recommended": False,
    "tier": 2,
    "category": "general",
    "quantization": "Q4"
}
```

### Custom Ollama Actions

Extend the plugin:

```python
class CustomOllamaPlugin(Plugin):
    async def _custom_action(self, **kwargs):
        # Your custom logic
        pass

    async def execute(self, action: str, **kwargs):
        if action == 'custom_action':
            return await self._custom_action(**kwargs)
        return await super().execute(action, **kwargs)
```

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check Ollama logs:
```bash
# Linux/macOS
journalctl -u ollama -f

# Windows
# Check Ollama Desktop logs
```

## Best Practices

1. **Always check Ollama status** before operations
2. **Handle network errors gracefully** (Ollama might not be running)
3. **Implement progress callbacks** for long-running operations
4. **Cache embeddings** for repeated queries
5. **Use appropriate models** for tasks (don't use 70B for simple tasks)
6. **Monitor system resources** during inference
7. **Implement request timeouts** to prevent hangs
8. **Clean up conversations** to prevent memory leaks

---

**Last Updated**: 2025-11-10
**Version**: 1.0
