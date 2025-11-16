# OpenAI Provider

AI provider plugin for OpenAI integration.

## Models

- gpt-3.5-turbo
- gpt-4
- gpt-4-turbo
- gpt-4-vision
- dall-e-3

## Configuration

Set environment variable: `OPENAI_API_KEY`

Or pass directly:
```python
provider = OpenAIProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.openai import OpenAIProvider

# Initialize
provider = OpenAIProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="gpt-3.5-turbo",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="gpt-3.5-turbo"
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
