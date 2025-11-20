# Cohere Provider

AI provider plugin for Cohere integration.

## Models

- command
- command-light
- command-nightly
- embed-english
- embed-multilingual

## Configuration

Set environment variable: `COHERE_API_KEY`

Or pass directly:
```python
provider = CohereProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.cohere import CohereProvider

# Initialize
provider = CohereProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="command",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="command"
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
