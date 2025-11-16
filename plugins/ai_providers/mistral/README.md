# Mistral Provider

AI provider plugin for Mistral integration.

## Models

- mistral-tiny
- mistral-small
- mistral-medium
- mistral-large
- mixtral-8x7b

## Configuration

Set environment variable: `MISTRAL_API_KEY`

Or pass directly:
```python
provider = MistralProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.mistral import MistralProvider

# Initialize
provider = MistralProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="mistral-tiny",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="mistral-tiny"
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
