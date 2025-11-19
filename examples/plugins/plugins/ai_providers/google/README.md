# Google Provider

AI provider plugin for Google integration.

## Models

- gemini-pro
- gemini-pro-vision
- gemini-ultra
- palm-2

## Configuration

Set environment variable: `GOOGLE_API_KEY`

Or pass directly:
```python
provider = GoogleProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.google import GoogleProvider

# Initialize
provider = GoogleProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="gemini-pro",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="gemini-pro"
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
