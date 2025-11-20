# Microsoft Provider

AI provider plugin for Microsoft integration.

## Models

- azure-gpt-4
- azure-gpt-35-turbo
- bing-chat

## Configuration

Set environment variable: `MICROSOFT_API_KEY`

Or pass directly:
```python
provider = MicrosoftProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.microsoft import MicrosoftProvider

# Initialize
provider = MicrosoftProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="azure-gpt-4",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="azure-gpt-4"
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
