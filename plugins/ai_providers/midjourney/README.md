# Midjourney Provider

AI provider plugin for Midjourney integration.

## Models

- midjourney-v6
- midjourney-v5-2

## Configuration

Set environment variable: `MIDJOURNEY_API_KEY`

Or pass directly:
```python
provider = MidjourneyProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.midjourney import MidjourneyProvider

# Initialize
provider = MidjourneyProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="midjourney-v6",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="midjourney-v6"
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
