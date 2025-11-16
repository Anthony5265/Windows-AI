# Runway Provider

AI provider plugin for Runway integration.

## Models

- gen-2
- gen-3-alpha

## Configuration

Set environment variable: `RUNWAY_API_KEY`

Or pass directly:
```python
provider = RunwayProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.runway import RunwayProvider

# Initialize
provider = RunwayProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="gen-2",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="gen-2"
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
