"""
Microsoft Provider Implementation
"""

import os
from typing import Dict, List, Optional, Any
import requests
import json
from pathlib import Path


class MicrosoftProvider:
    """
    Microsoft AI Provider
    
    Supported models: azure-gpt-4, azure-gpt-35-turbo, bing-chat
    """
    
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        Initialize Microsoft provider
        
        Args:
            api_key: API key for Microsoft (required)
            api_base: Base URL for API (default: https://api.cognitive.microsoft.com)
        """
        self.api_key = api_key or os.getenv("MICROSOFT_API_KEY")
        self.api_base = api_base or "https://api.cognitive.microsoft.com"
        self.available_models = [
            "azure-gpt-4",
            "azure-gpt-35-turbo",
            "bing-chat"
]
        
        if true and not self.api_key:
            raise ValueError("API key required for Microsoft")
    
    def list_models(self) -> List[str]:
        """List available models"""
        return self.available_models
    
    def generate(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """
        Generate completion from Microsoft
        
        Args:
            prompt: Input prompt
            model: Model to use
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Dict containing generated text and metadata
        """
        if model not in self.available_models:
            raise ValueError(f"Model {model} not available. Choose from: {self.available_models}")
        
        # Prepare request
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": model,
            "prompt": prompt,
            **kwargs
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            return {
                "text": result.get("text", result.get("choices", [{}])[0].get("text", "")),
                "model": model,
                "provider": "Microsoft",
                "raw_response": result
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "provider": "Microsoft",
                "model": model
            }
    
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
            raise ValueError(f"Model {model} not available")
        
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            return {
                "message": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
                "model": model,
                "provider": "Microsoft",
                "raw_response": result
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "provider": "Microsoft",
                "model": model
            }
    
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
        
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": model,
            "input": text
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/embeddings",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            return {
                "embedding": result.get("data", [{}])[0].get("embedding", []),
                "model": model,
                "provider": "Microsoft",
                "raw_response": result
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "provider": "Microsoft",
                "model": model
            }


# Example usage
if __name__ == "__main__":
    # Initialize provider
    provider = MicrosoftProvider()
    
    # List models
    print("Available models:")
    for model in provider.list_models():
        print(f"  - {model}")
    
    # Test generation (if API key available)
    if provider.api_key:
        result = provider.generate(
            prompt="Hello, how are you?",
            model=provider.available_models[0],
            max_tokens=50
        )
        print(f"\nGeneration result: {result}")
