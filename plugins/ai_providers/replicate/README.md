# Replicate Provider

AI provider plugin for Replicate integration.

## Models

- stability-ai/sdxl
- meta/llama-2-70b-chat
- mistralai/mixtral-8x7b

## Configuration

Set environment variable: `REPLICATE_API_KEY`

Or pass directly:
```python
provider = ReplicateProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.replicate import ReplicateProvider

# Initialize
provider = ReplicateProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="stability-ai/sdxl",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="stability-ai/sdxl"
)
```

## API Reference

### `list_models()`
Returns list of available models.

### `generate(prompt, model, **kwargs)`
Generate text completion.

### `chat(messages, model, **kwargs)`
Chat completion with conversation history.

### `embed(text, model)`
Generate embeddings for text.
