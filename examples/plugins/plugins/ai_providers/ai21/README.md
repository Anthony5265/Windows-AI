# AI21 Provider

AI provider plugin for AI21 integration.

## Models

- j2-ultra
- j2-mid
- j2-light

## Configuration

Set environment variable: `AI21_API_KEY`

Or pass directly:
```python
provider = AI21Provider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.ai21 import AI21Provider

# Initialize
provider = AI21Provider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="j2-ultra",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="j2-ultra"
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
