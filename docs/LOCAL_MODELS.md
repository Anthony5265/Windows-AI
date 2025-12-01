# Local Models Guide

Complete guide to using local AI models with Windows-AI through Ollama integration.

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Recommended Models](#recommended-models)
4. [Model Management](#model-management)
5. [Using Local Models](#using-local-models)
6. [System Requirements](#system-requirements)
7. [Troubleshooting](#troubleshooting)

## Overview

Windows-AI supports running AI models locally on your machine using [Ollama](https://ollama.ai). This provides:

- **Privacy**: All inference happens on your machine
- **Offline capability**: No internet required after model download
- **Cost savings**: No API costs
- **Low latency**: No network round trips
- **Full control**: Choose and customize your models

## Getting Started

### 1. Install Ollama

Download and install Ollama from [https://ollama.ai](https://ollama.ai):

- **Windows**: Download and run the installer
- **macOS**: `brew install ollama`
- **Linux**: `curl https://ollama.ai/install.sh | sh`

### 2. Verify Installation

Open a terminal and run:

```bash
ollama --version
```

Start the Ollama service:

```bash
ollama serve
```

### 3. Open Windows-AI

1. Launch Windows-AI
2. Navigate to the **Models** tab
3. Browse and download your first model

## Recommended Models

### Tier 1: Essential (Fastest Setup)

Perfect for getting started quickly with minimal system requirements:

#### **Llama 3.2 3B** ⭐ Recommended Default
- **Size**: 2.0 GB
- **RAM**: 4 GB
- **Best for**: General-purpose assistant, fast responses
- **Download**: `ollama pull llama3.2:3b`

#### **Llama 3.2 1B**
- **Size**: 1.3 GB
- **RAM**: 2 GB
- **Best for**: Ultra-fast tasks, minimal resource usage
- **Download**: `ollama pull llama3.2:1b`

#### **Nomic Embed Text**
- **Size**: 274 MB
- **RAM**: 1 GB
- **Best for**: Text embeddings, RAG applications
- **Download**: `ollama pull nomic-embed-text`

### Tier 2: Performance (Better Quality)

For users with more powerful hardware:

#### **Llama 3.1 8B**
- **Size**: 4.7 GB
- **RAM**: 8 GB
- **Best for**: High-quality chat, reasoning tasks
- **Download**: `ollama pull llama3.1:8b`

#### **Mistral 7B**
- **Size**: 4.1 GB
- **RAM**: 8 GB
- **Best for**: Balanced performance, excellent instruction following
- **Download**: `ollama pull mistral:7b`

#### **DeepSeek Coder 6.7B**
- **Size**: 3.8 GB
- **RAM**: 8 GB
- **Best for**: Code generation, programming assistance
- **Download**: `ollama pull deepseek-coder:6.7b`

### Tier 3: Advanced (Power Users)

Requires powerful hardware with significant RAM:

#### **Llama 3.1 70B**
- **Size**: 40 GB
- **RAM**: 64 GB
- **Best for**: Maximum quality responses
- **Download**: `ollama pull llama3.1:70b`

#### **Code Llama 34B**
- **Size**: 19 GB
- **RAM**: 32 GB
- **Best for**: Advanced coding tasks
- **Download**: `ollama pull codellama:34b`

## Model Management

### Using the GUI

1. **Browse Models**: Navigate to the **Models** tab
2. **View Details**: Click on any model card to see specifications
3. **Download**: Click the "Download" button
4. **Track Progress**: Real-time download progress with WebSocket updates
5. **Delete Models**: Remove unwanted models to free up disk space

### Using the API

#### List Available Models
```bash
curl http://localhost:8010/models/available
```

#### List Installed Models
```bash
curl http://localhost:8010/models/installed
```

#### Get Recommended Models
```bash
curl http://localhost:8010/models/recommended
```

#### Download a Model
```bash
curl -X POST http://localhost:8010/models/download?model_id=llama3.2:3b
```

#### Delete a Model
```bash
curl -X DELETE http://localhost:8010/models/llama3.2:3b
```

#### Get System Specifications
```bash
curl http://localhost:8010/system/specs
```

### Using Ollama CLI

```bash
# List installed models
ollama list

# Pull a model
ollama pull llama3.2:3b

# Run a model interactively
ollama run llama3.2:3b

# Remove a model
ollama rm llama3.2:3b

# Show model information
ollama show llama3.2:3b
```

## Using Local Models

### In the Chat Interface

1. Open Windows-AI
2. Click on the model selector dropdown
3. Choose a local model (shows "Local" badge)
4. Start chatting!

### Via the API

```python
import requests

response = requests.post('http://localhost:8010/chat/stream', json={
    'message': 'Hello! Explain quantum computing in simple terms.',
    'model': 'ollama/llama3.2:3b',
    'stream': True
})

for line in response.iter_lines():
    if line:
        print(line.decode())
```

### With Ollama Plugin

The Ollama plugin provides advanced features:

```python
# Using the plugin directly
plugin = OllamaPlugin()

# Chat with conversation history
result = await plugin.execute(
    action='chat',
    model='llama3.2:3b',
    message='What is machine learning?',
    conversation_id='my-conv-1'
)

# Generate embeddings
embeddings = await plugin.execute(
    action='embeddings',
    model='nomic-embed-text',
    text='This is a sample document'
)

# Batch embeddings
batch_result = await plugin.execute(
    action='batch_embeddings',
    model='nomic-embed-text',
    texts=['Doc 1', 'Doc 2', 'Doc 3']
)

# RAG query
rag_result = await plugin.execute(
    action='rag_query',
    query='What is the capital of France?',
    documents=['France is a country...', 'Paris is a city...'],
    model='llama3.2:3b',
    embed_model='nomic-embed-text'
)
```

## System Requirements

### Minimum Requirements

- **OS**: Windows 10/11, macOS 10.15+, or Linux
- **RAM**: 4 GB (for 3B models)
- **Disk**: 10 GB free space
- **CPU**: Any modern processor

### Recommended Requirements

- **RAM**: 16 GB or more
- **Disk**: 50 GB+ free space (SSD preferred)
- **GPU**:
  - NVIDIA (CUDA): 8GB+ VRAM
  - Apple Silicon: M1/M2/M3
  - AMD (ROCm): 8GB+ VRAM

### GPU Acceleration

Ollama automatically uses GPU acceleration when available:

- **NVIDIA**: CUDA support (automatic)
- **Apple Silicon**: Metal support (automatic)
- **AMD**: ROCm support (Linux only, automatic)

Check GPU usage:
```bash
# NVIDIA
nvidia-smi

# Apple Silicon
Activity Monitor > GPU tab
```

### Model Size vs RAM Guidelines

| Model Size | Minimum RAM | Recommended RAM | GPU VRAM |
|------------|-------------|-----------------|----------|
| 1B         | 2 GB        | 4 GB            | 2 GB     |
| 3B         | 4 GB        | 8 GB            | 4 GB     |
| 7B         | 8 GB        | 16 GB           | 8 GB     |
| 13B        | 16 GB       | 32 GB           | 12 GB    |
| 34B        | 32 GB       | 64 GB           | 24 GB    |
| 70B        | 64 GB       | 128 GB          | 48 GB    |

## Performance Optimization

### Tips for Better Performance

1. **Use Q4 quantized models** (default in catalog)
2. **Enable GPU acceleration** (automatic if available)
3. **Close other applications** to free up RAM
4. **Use SSD storage** for faster model loading
5. **Keep context length reasonable** (under 4K tokens)

### Model Selection by Use Case

- **Quick tasks, chat**: Llama 3.2 1B/3B
- **High-quality responses**: Llama 3.1 8B or Mistral 7B
- **Code generation**: DeepSeek Coder or Code Llama
- **Document search (RAG)**: Nomic Embed Text
- **Maximum quality**: Llama 3.1 70B (requires powerful hardware)

## Troubleshooting

### Ollama Not Running

**Error**: "Cannot connect to Ollama"

**Solution**:
```bash
# Start Ollama service
ollama serve

# Or on Windows, ensure Ollama Desktop is running
```

### Out of Memory

**Error**: Model fails to load or crashes

**Solution**:
- Choose a smaller model
- Close other applications
- Upgrade RAM
- Use GPU if available

### Slow Performance

**Symptoms**: Very slow response times

**Solutions**:
1. Check GPU acceleration is enabled
2. Use a smaller model
3. Reduce context window size
4. Check system resource usage

### Model Not Found

**Error**: "Model not found"

**Solution**:
```bash
# Pull the model first
ollama pull llama3.2:3b

# Or use the Windows-AI Models tab to download
```

### Download Interrupted

**Problem**: Model download stopped

**Solution**:
- Restart the download from Windows-AI
- Or manually: `ollama pull <model-name>`
- Check disk space availability

### Permission Errors

**Error**: Permission denied

**Solution** (Linux/macOS):
```bash
# Ensure proper permissions
sudo chown -R $USER ~/.ollama
```

## Additional Resources

- **Ollama Documentation**: https://github.com/ollama/ollama
- **Ollama Model Library**: https://ollama.ai/library
- **Windows-AI Documentation**: See `OLLAMA_INTEGRATION.md`
- **Community Support**: [Windows-AI GitHub Issues](https://github.com/yourorg/Windows-AI/issues)

## FAQ

**Q: Can I use multiple models at the same time?**
A: Yes, but each model consumes RAM. Ensure you have sufficient resources.

**Q: How do I update a model?**
A: Simply download it again. Ollama will pull the latest version.

**Q: Can I create custom models?**
A: Yes! See [Ollama Modelfile documentation](https://github.com/ollama/ollama/blob/main/docs/modelfile.md)

**Q: Do local models work offline?**
A: Yes, once downloaded, models work completely offline.

**Q: How much disk space do I need?**
A: Plan for 2-5GB per small model, 10GB+ for large models. The catalog shows exact sizes.

**Q: Can I use models from Hugging Face?**
A: Yes, convert them to GGUF format and use with Ollama. See Ollama documentation.

---

**Last Updated**: 2025-11-10
**Version**: 1.0
