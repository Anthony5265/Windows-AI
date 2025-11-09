# GPT4All Plugin for Windows AI

This plugin provides integration with GPT4All, allowing you to use local AI models for chat and text generation within Windows AI.

## Features

- **Local Model Support**: Run AI models locally on your machine
- **Chat Completion**: Conversational AI with message history
- **Text Generation**: Generate text from prompts
- **Model Management**: List, load, and unload models
- **Streaming Support**: Stream responses in real-time
- **Configurable Parameters**: Temperature, top_p, top_k, repeat penalty, etc.

## Prerequisites

1. Install GPT4All on your system
2. Start the GPT4All server with API enabled
3. Default server URL: `http://localhost:4891`

## Installation

The plugin is included in Windows AI. No additional installation required.

## Configuration

Configure the plugin in your Windows AI settings:

```json
{
  "gpt4all": {
    "api_url": "http://localhost:4891",
    "max_tokens": 500,
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "repeat_penalty": 1.1,
    "repeat_last_n": 64,
    "n_batch": 512,
    "stream": false,
    "models_path": "~/.local/share/nomic.ai/GPT4All/"
  }
}
```

## Usage

### Basic Chat

```python
from plugins.local_models.gpt4all_plugin import GPT4AllPlugin

# Initialize plugin
plugin = GPT4AllPlugin()
plugin.initialize({"gpt4all": {"api_url": "http://localhost:4891"}})

# Load a model
plugin.execute("load_model", {"model_name": "ggml-gpt4all-j-v1.3-groovy.bin"})

# Chat with the model
messages = [
    {"role": "user", "content": "Hello! How are you?"}
]
result = plugin.execute("chat", {
    "messages": messages,
    "max_tokens": 100,
    "temperature": 0.7
})

print(result["response"])
```

### Text Generation

```python
# Generate text from a prompt
result = plugin.execute("generate_text", {
    "prompt": "The future of artificial intelligence is",
    "max_tokens": 100,
    "temperature": 0.8
})

print(result["text"])
```

### Model Management

```python
# List available models
models = plugin.execute("list_models", {})
print(models["models"])

# Get current model status
status = plugin.execute("get_model_status", {})
print(f"Model loaded: {status['loaded']}")
print(f"Current model: {status['current_model']}")

# Get model information
info = plugin.execute("get_model_info", {})
print(f"Provider: {info['provider']}")
print(f"Capabilities: {info['capabilities']}")
```

## Available Actions

- `list_models`: List all available models
- `load_model`: Load a specific model
- `unload_model`: Unload the current model
- `get_model_info`: Get information about the loaded model
- `get_model_status`: Get current model status
- `generate_text`: Generate text from a prompt
- `chat`: Chat with the model using message history

## Parameters

### Generation Parameters

- `max_tokens`: Maximum number of tokens to generate (default: 500)
- `temperature`: Sampling temperature (0.0-1.0, default: 0.7)
- `top_p`: Nucleus sampling parameter (0.0-1.0, default: 0.9)
- `top_k`: Top-k sampling parameter (default: 40)
- `repeat_penalty`: Penalty for repetition (default: 1.1)
- `repeat_last_n`: Number of tokens to consider for repetition penalty (default: 64)
- `n_batch`: Batch size for processing (default: 512)
- `stream`: Whether to stream responses (default: false)

### Chat Parameters

- `messages`: Array of message objects with `role` and `content`
- All generation parameters are also supported

## Troubleshooting

### Server Connection Issues

1. Ensure GPT4All is running with the API server enabled
2. Check that the server is running on the correct port (default: 4891)
3. Verify the API URL in your configuration

### Model Loading Issues

1. Ensure you have downloaded models through GPT4All
2. Check that the model name matches exactly
3. Verify sufficient RAM is available for the model

### Performance Issues

1. Adjust `n_batch` based on your system capabilities
2. Use smaller models for faster responses
3. Consider reducing `max_tokens` for quicker generation

## Supported Models

GPT4All supports various models including:

- GPT4All-J series
- Llama 2/3 variants
- Mistral models
- And many more available through GPT4All

## Security Notes

- All processing happens locally on your machine
- No data is sent to external servers
- Models run in a sandboxed environment
- Ensure you download models from trusted sources

## License

This plugin is part of Windows AI and follows the same license terms.