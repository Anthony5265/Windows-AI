#!/usr/bin/env python3
"""
AI Provider Plugin Generator
Creates standardized plugins for AI model providers
"""

from pathlib import Path
import json
from typing import Dict, List

class AIProviderGenerator:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.plugins_dir = repo_root / "plugins" / "ai_providers"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_provider_plugin(self, provider_name: str, models: List[str], 
                                 api_base: str, requires_key: bool = True):
        """Generate a complete AI provider plugin"""
        
        # Create provider directory
        provider_dir = self.plugins_dir / provider_name.lower().replace(" ", "_")
        provider_dir.mkdir(exist_ok=True)
        
        # Create __init__.py
        init_content = f'''"""
{provider_name} AI Provider Plugin
Integrates {provider_name} models with Windows-AI
"""

from .provider import {provider_name.replace(" ", "")}Provider

__version__ = "1.0.0"
__all__ = ["{provider_name.replace(" ", "")}Provider"]
'''
        (provider_dir / "__init__.py").write_text(init_content, encoding='utf-8')
        
        # Create main provider file
        provider_content = f'''"""
{provider_name} Provider Implementation
"""

import os
from typing import Dict, List, Optional, Any
import requests
import json
from pathlib import Path


class {provider_name.replace(" ", "")}Provider:
    """
    {provider_name} AI Provider
    
    Supported models: {", ".join(models[:5])}{"..." if len(models) > 5 else ""}
    """
    
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        Initialize {provider_name} provider
        
        Args:
            api_key: API key for {provider_name} ({("required" if requires_key else "optional")})
            api_base: Base URL for API (default: {api_base})
        """
        self.api_key = api_key or os.getenv("{provider_name.upper().replace(" ", "_")}_API_KEY")
        self.api_base = api_base or "{api_base}"
        self.available_models = {json.dumps(models, indent=12)}
        
        if {str(requires_key).lower()} and not self.api_key:
            raise ValueError("API key required for {provider_name}")
    
    def list_models(self) -> List[str]:
        """List available models"""
        return self.available_models
    
    def generate(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """
        Generate completion from {provider_name}
        
        Args:
            prompt: Input prompt
            model: Model to use
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Dict containing generated text and metadata
        """
        if model not in self.available_models:
            raise ValueError(f"Model {{model}} not available. Choose from: {{self.available_models}}")
        
        # Prepare request
        headers = {{
            "Content-Type": "application/json",
        }}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {{self.api_key}}"
        
        payload = {{
            "model": model,
            "prompt": prompt,
            **kwargs
        }}
        
        try:
            response = requests.post(
                f"{{self.api_base}}/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            return {{
                "text": result.get("text", result.get("choices", [{{}}])[0].get("text", "")),
                "model": model,
                "provider": "{provider_name}",
                "raw_response": result
            }}
            
        except requests.exceptions.RequestException as e:
            return {{
                "error": str(e),
                "provider": "{provider_name}",
                "model": model
            }}
    
    def chat(self, messages: List[Dict[str, str]], model: str, **kwargs) -> Dict[str, Any]:
        """
        Chat completion
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use
            **kwargs: Additional parameters
            
        Returns:
            Dict containing response and metadata
        """
        if model not in self.available_models:
            raise ValueError(f"Model {{model}} not available")
        
        headers = {{
            "Content-Type": "application/json",
        }}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {{self.api_key}}"
        
        payload = {{
            "model": model,
            "messages": messages,
            **kwargs
        }}
        
        try:
            response = requests.post(
                f"{{self.api_base}}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            return {{
                "message": result.get("choices", [{{}}])[0].get("message", {{}}).get("content", ""),
                "model": model,
                "provider": "{provider_name}",
                "raw_response": result
            }}
            
        except requests.exceptions.RequestException as e:
            return {{
                "error": str(e),
                "provider": "{provider_name}",
                "model": model
            }}
    
    def embed(self, text: str, model: str = None) -> Dict[str, Any]:
        """
        Generate embeddings
        
        Args:
            text: Text to embed
            model: Embedding model to use
            
        Returns:
            Dict containing embedding vector and metadata
        """
        # Use first available model if not specified
        if not model:
            model = self.available_models[0] if self.available_models else "default"
        
        headers = {{
            "Content-Type": "application/json",
        }}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {{self.api_key}}"
        
        payload = {{
            "model": model,
            "input": text
        }}
        
        try:
            response = requests.post(
                f"{{self.api_base}}/embeddings",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            return {{
                "embedding": result.get("data", [{{}}])[0].get("embedding", []),
                "model": model,
                "provider": "{provider_name}",
                "raw_response": result
            }}
            
        except requests.exceptions.RequestException as e:
            return {{
                "error": str(e),
                "provider": "{provider_name}",
                "model": model
            }}


# Example usage
if __name__ == "__main__":
    # Initialize provider
    provider = {provider_name.replace(" ", "")}Provider()
    
    # List models
    print("Available models:")
    for model in provider.list_models():
        print(f"  - {{model}}")
    
    # Test generation (if API key available)
    if provider.api_key:
        result = provider.generate(
            prompt="Hello, how are you?",
            model=provider.available_models[0],
            max_tokens=50
        )
        print(f"\\nGeneration result: {{result}}")
'''
        
        (provider_dir / "provider.py").write_text(provider_content, encoding='utf-8')
        
        # Create config file
        config = {
            "name": provider_name,
            "version": "1.0.0",
            "api_base": api_base,
            "requires_key": requires_key,
            "models": models,
            "capabilities": ["text-generation", "chat"],
            "settings": {
                "default_model": models[0] if models else None,
                "timeout": 60,
                "max_retries": 3
            }
        }
        
        (provider_dir / "config.json").write_text(
            json.dumps(config, indent=2), encoding='utf-8'
        )
        
        # Create README
        readme = f'''# {provider_name} Provider

AI provider plugin for {provider_name} integration.

## Models

{chr(10).join(f"- {model}" for model in models)}

## Configuration

Set environment variable: `{provider_name.upper().replace(" ", "_")}_API_KEY`

Or pass directly:
```python
provider = {provider_name.replace(" ", "")}Provider(api_key="your-key")
```

## Usage

```python
from plugins.ai_providers.{provider_name.lower().replace(" ", "_")} import {provider_name.replace(" ", "")}Provider

# Initialize
provider = {provider_name.replace(" ", "")}Provider()

# List models
models = provider.list_models()

# Generate text
result = provider.generate(
    prompt="Explain quantum computing",
    model="{models[0] if models else "default"}",
    max_tokens=100
)

# Chat
response = provider.chat(
    messages=[
        {{"role": "user", "content": "Hello!"}}
    ],
    model="{models[0] if models else "default"}"
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
'''
        
        (provider_dir / "README.md").write_text(readme, encoding='utf-8')
        
        print(f"✅ Created {provider_name} provider plugin at: {provider_dir}")
        return provider_dir


def main():
    """Generate all Tier 1 AI provider plugins"""
    repo_root = Path.cwd()
    generator = AIProviderGenerator(repo_root)
    
    print("=" * 80)
    print("GENERATING TIER 1 AI PROVIDER PLUGINS")
    print("=" * 80)
    print()
    
    # Define all providers
    providers = [
        {
            "name": "OpenAI",
            "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4-vision", "dall-e-3"],
            "api_base": "https://api.openai.com/v1",
            "requires_key": True
        },
        {
            "name": "Anthropic",
            "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-2.1", "claude-instant"],
            "api_base": "https://api.anthropic.com/v1",
            "requires_key": True
        },
        {
            "name": "Google",
            "models": ["gemini-pro", "gemini-pro-vision", "gemini-ultra", "palm-2"],
            "api_base": "https://generativelanguage.googleapis.com/v1",
            "requires_key": True
        },
        {
            "name": "Microsoft",
            "models": ["azure-gpt-4", "azure-gpt-35-turbo", "bing-chat"],
            "api_base": "https://api.cognitive.microsoft.com",
            "requires_key": True
        },
        {
            "name": "Meta",
            "models": ["llama-2-7b", "llama-2-13b", "llama-2-70b", "code-llama-7b", "code-llama-34b"],
            "api_base": "https://api.together.xyz/v1",
            "requires_key": True
        },
        {
            "name": "Cohere",
            "models": ["command", "command-light", "command-nightly", "embed-english", "embed-multilingual"],
            "api_base": "https://api.cohere.ai/v1",
            "requires_key": True
        },
        {
            "name": "AI21",
            "models": ["j2-ultra", "j2-mid", "j2-light"],
            "api_base": "https://api.ai21.com/studio/v1",
            "requires_key": True
        },
        {
            "name": "Mistral",
            "models": ["mistral-tiny", "mistral-small", "mistral-medium", "mistral-large", "mixtral-8x7b"],
            "api_base": "https://api.mistral.ai/v1",
            "requires_key": True
        },
        {
            "name": "Perplexity",
            "models": ["pplx-7b-online", "pplx-70b-online", "pplx-7b-chat", "pplx-70b-chat"],
            "api_base": "https://api.perplexity.ai",
            "requires_key": True
        },
        {
            "name": "Together",
            "models": ["togethercomputer/RedPajama-INCITE-7B", "togethercomputer/falcon-40b", "togethercomputer/mpt-30b"],
            "api_base": "https://api.together.xyz/v1",
            "requires_key": True
        },
    ]
    
    created_count = 0
    for provider_info in providers:
        try:
            generator.generate_provider_plugin(
                provider_name=provider_info["name"],
                models=provider_info["models"],
                api_base=provider_info["api_base"],
                requires_key=provider_info.get("requires_key", True)
            )
            created_count += 1
        except Exception as e:
            print(f"❌ Error creating {provider_info['name']}: {e}")
    
    print()
    print("=" * 80)
    print(f"COMPLETE: Created {created_count}/{len(providers)} provider plugins")
    print("=" * 80)


if __name__ == "__main__":
    main()
