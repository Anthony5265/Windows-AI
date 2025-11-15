# Meta Provider

AI provider plugin for Meta integration.

## Models

- llama-2-7b
- llama-2-13b
- llama-2-70b
- code-llama-7b
- code-llama-34b

## Configuration

Set environment variable: `META_API_KEY`

Or pass directly:
```python
provider = MetaProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.meta import MetaProvider

# Initialize
provider = MetaProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="llama-2-7b",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="llama-2-7b"
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
