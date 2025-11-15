# Stability Provider

AI provider plugin for Stability integration.

## Models

- stable-diffusion-xl
- stable-diffusion-2-1
- stable-code

## Configuration

Set environment variable: `STABILITY_API_KEY`

Or pass directly:
```python
provider = StabilityProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.stability import StabilityProvider

# Initialize
provider = StabilityProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="stable-diffusion-xl",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="stable-diffusion-xl"
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
