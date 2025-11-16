# Perplexity Provider

AI provider plugin for Perplexity integration.

## Models

- pplx-7b-online
- pplx-70b-online
- pplx-7b-chat
- pplx-70b-chat

## Configuration

Set environment variable: `PERPLEXITY_API_KEY`

Or pass directly:
```python
provider = PerplexityProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.perplexity import PerplexityProvider

# Initialize
provider = PerplexityProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="pplx-7b-online",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="pplx-7b-online"
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
