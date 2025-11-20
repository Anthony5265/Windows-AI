# HuggingFace Provider

AI provider plugin for HuggingFace integration.

## Models

- gpt2
- facebook/opt-350m
- bigscience/bloom-560m

## Configuration

Set environment variable: `HUGGINGFACE_API_KEY`

Or pass directly:
```python
provider = HuggingFaceProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.huggingface import HuggingFaceProvider

# Initialize
provider = HuggingFaceProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="gpt2",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="gpt2"
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
