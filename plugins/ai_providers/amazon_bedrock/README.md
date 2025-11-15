# Amazon Bedrock Provider

AI provider plugin for Amazon Bedrock integration.

## Models

- anthropic.claude-v2
- amazon.titan-text
- ai21.j2-ultra

## Configuration

Set environment variable: `AMAZON_BEDROCK_API_KEY`

Or pass directly:
```python
provider = AmazonBedrockProvider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.amazon_bedrock import AmazonBedrockProvider

# Initialize
provider = AmazonBedrockProvider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="anthropic.claude-v2",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    model="anthropic.claude-v2"
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
