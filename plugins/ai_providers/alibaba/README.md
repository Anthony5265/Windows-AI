# Alibaba Provider

AI provider plugin for Alibaba integration.

## Models

- qwen-turbo
- qwen-plus
- qwen-max

## Configuration

Set environment variable: `ALIBABA_API_KEY`

Or pass directly:
```python
provider = AlibabaProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.alibaba import AlibabaProvider

# Initialize
provider = AlibabaProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="qwen-turbo",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="qwen-turbo"
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
