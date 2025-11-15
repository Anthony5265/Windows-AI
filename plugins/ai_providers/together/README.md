# Together Provider

AI provider plugin for Together integration.

## Models

- togethercomputer/RedPajama-INCITE-7B
- togethercomputer/falcon-40b
- togethercomputer/mpt-30b

## Configuration

Set environment variable: `TOGETHER_API_KEY`

Or pass directly:
```python
provider = TogetherProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.together import TogetherProvider

# Initialize
provider = TogetherProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="togethercomputer/RedPajama-INCITE-7B",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="togethercomputer/RedPajama-INCITE-7B"
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
