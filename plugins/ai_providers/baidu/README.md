# Baidu Provider

AI provider plugin for Baidu integration.

## Models

- ernie-bot
- ernie-bot-turbo
- ernie-3.5

## Configuration

Set environment variable: `BAIDU_API_KEY`

Or pass directly:
```python
provider = BaiduProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.baidu import BaiduProvider

# Initialize
provider = BaiduProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="ernie-bot",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="ernie-bot"
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
