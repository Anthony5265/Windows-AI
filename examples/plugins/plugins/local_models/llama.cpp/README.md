# llama.cpp Platform

Local model inference platform - no cloud required.

## Installation

```bash
# The platform will auto-install if not detected
# Or install manually from official source
```

## Usage

```python
from plugins.local_models.llama.cpp import llama.cppPlatform

# Initialize
platform = llama.cppPlatform()

# Start server
platform.start_server()

# List models
models = platform.list_models()

# Pull a model
platform.pull_model("llama2:7b")

# Generate
result = platform.generate(
    prompt="Explain AI",
    model="llama2:7b"
)

# Chat
response = platform.chat(
    messages=[{"role": "user", "content": "Hello!"}],
    model="llama2:7b"
)

# Cleanup
platform.stop_server()
```

## Features

- ✅ Fully local - no internet required after model download
- ✅ Privacy-focused - data never leaves your machine
- ✅ GPU acceleration supported
- ✅ Multiple model formats
- ✅ Easy model management

## Configuration

- **Port:** 8080
- **Models Directory:** ~/llama.cpp/models
- **Executable:** llama-server
