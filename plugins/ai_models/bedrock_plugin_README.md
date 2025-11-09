# Amazon Bedrock Plugin

This plugin provides integration with Amazon Bedrock, allowing access to various foundation models including Claude, Titan, and Jurassic models.

## Supported Models

### Claude Models (Anthropic)
- `claude-3-opus` - Most powerful Claude model
- `claude-3-sonnet` - Balanced performance and speed
- `claude-3-haiku` - Fastest and most compact
- `claude-2.1` - Previous generation with 200K context
- `claude-2.0` - Previous generation
- `claude-instant-1.2` - Lightweight, fast responses

### Titan Models (Amazon)
- `titan-text-express` - General purpose text generation
- `titan-text-lite` - Lightweight text generation
- `titan-embed-text` - Text embeddings (English)
- `titan-embed-multilingual` - Text embeddings (Multilingual)

### Jurassic Models (AI21)
- `jurassic-2-mid` - Mid-sized model
- `jurassic-2-ultra` - Most powerful Jurassic model

### Embedding Models
- `titan-embed` - Amazon Titan embeddings
- `cohere-embed-english` - Cohere English embeddings
- `cohere-embed-multilingual` - Cohere multilingual embeddings

## Actions

### chat
Chat completion using conversational models.

**Parameters:**
- `message` (str): The user message
- `model` (str): Model name (default: "claude-3-sonnet")
- `system_prompt` (str, optional): System prompt for Claude models
- `temperature` (float, optional): 0.0-1.0 (default: 0.7)
- `max_tokens` (int, optional): Maximum tokens to generate (default: 4000)
- `top_p` (float, optional): Nucleus sampling (default: 0.999)
- `top_k` (int, optional): Top-k sampling (default: 250)

**Example:**
```python
result = plugin.execute("chat", {
    "message": "Explain quantum computing",
    "model": "claude-3-haiku",
    "temperature": 0.5
})
```

### complete
Text completion for various models.

**Parameters:**
- `prompt` (str): The input prompt
- `model` (str): Model name (default: "titan-text-express")
- `temperature` (float, optional): 0.0-1.0 (default: 0.7)
- `max_tokens` (int, optional): Maximum tokens (default: 4000)
- `top_p` (float, optional): Nucleus sampling (default: 0.999)

**Example:**
```python
result = plugin.execute("complete", {
    "prompt": "The future of artificial intelligence is",
    "model": "titan-text-express"
})
```

### embed
Generate embeddings for text inputs.

**Parameters:**
- `texts` (str or list): Text(s) to embed
- `model` (str): Embedding model (default: "titan-embed")

**Example:**
```python
result = plugin.execute("embed", {
    "texts": ["Hello world", "Machine learning"],
    "model": "titan-embed"
})
```

### list_models
List all available foundation models in your AWS account.

**Parameters:** None

**Example:**
```python
result = plugin.execute("list_models", {})
```

## Setup

### Prerequisites
1. AWS Account with Bedrock access
2. AWS credentials configured (environment variables, IAM role, or ~/.aws/credentials)
3. boto3 package installed

### AWS Credentials
Configure AWS credentials using one of these methods:

1. **Environment Variables:**
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_REGION=us-east-1
   ```

2. **AWS Credentials File:**
   ```ini
   [default]
   aws_access_key_id = your_access_key
   aws_secret_access_key = your_secret_key
   region = us-east-1
   ```

3. **IAM Role (EC2/ECS):**
   Ensure the instance/role has permissions for Bedrock operations.

### Required IAM Permissions
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:ListFoundationModels",
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": "*"
        }
    ]
}
```

## Installation

Install the required dependency:
```bash
pip install boto3
```

## Usage Example

```python
from plugins.ai_models.bedrock_plugin import BedrockPlugin

# Initialize plugin
plugin = BedrockPlugin()
success = plugin.initialize({
    "region": "us-east-1"  # Optional, defaults to us-east-1
})

if success:
    # Chat with Claude
    result = plugin.execute("chat", {
        "message": "What is machine learning?",
        "model": "claude-3-haiku"
    })
    print(result["response"])
    
    # Generate embeddings
    result = plugin.execute("embed", {
        "texts": ["Machine learning is a subset of AI"],
        "model": "titan-embed"
    })
    print(f"Embedding dimension: {result['dimension']}")
```

## Error Handling

The plugin includes comprehensive error handling for:
- Missing AWS credentials
- Invalid model names
- Network connectivity issues
- AWS service limits
- Model-specific errors

All errors are returned in the format:
```python
{
    "error": "Error description"
}
```

## Model-Specific Notes

### Claude Models
- Support system prompts
- Use Anthropic's message format
- Best for conversational AI and complex reasoning

### Titan Models
- Amazon's own models
- Good for general text generation
- Cost-effective option

### Jurassic Models
- AI21 Labs models
- Good for creative writing and analysis
- Support various text generation tasks

## Region Availability

Amazon Bedrock is available in multiple AWS regions. Check the AWS documentation for the latest region availability and model support.

## Rate Limits

Be aware of AWS service quotas and rate limits for Bedrock models. Implement appropriate retry logic and backoff strategies in production applications.