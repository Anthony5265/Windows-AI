# Anthropic Provider

AI provider plugin for Anthropic integration.

## Models

- claude-3-opus
- claude-3-sonnet
- claude-3-haiku
- claude-2.1
- claude-instant

## Configuration

Set environment variable: `ANTHROPIC_API_KEY`

Or pass directly:
```python
provider = AnthropicProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.anthropic import AnthropicProvider

# Initialize
provider = AnthropicProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="claude-3-opus",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="claude-3-opus"
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
