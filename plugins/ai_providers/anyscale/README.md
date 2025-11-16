# Anyscale Provider

AI provider plugin for Anyscale integration.

## Models

- meta-llama/Llama-2-7b
- meta-llama/Llama-2-70b
- mistralai/Mistral-7B

## Configuration

Set environment variable: `ANYSCALE_API_KEY`

Or pass directly:
```python
provider = AnyscaleProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.anyscale import AnyscaleProvider

# Initialize
provider = AnyscaleProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="meta-llama/Llama-2-7b",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="meta-llama/Llama-2-7b"
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
