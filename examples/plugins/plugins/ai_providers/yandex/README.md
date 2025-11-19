# Yandex Provider

AI provider plugin for Yandex integration.

## Models

- yandexgpt-lite
- yandexgpt

## Configuration

Set environment variable: `YANDEX_API_KEY`

Or pass directly:
```python
provider = YandexProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.yandex import YandexProvider

# Initialize
provider = YandexProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="yandexgpt-lite",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="yandexgpt-lite"
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
