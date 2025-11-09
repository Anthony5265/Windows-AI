"""
Anyscale Endpoints Model Provider Plugin
Supports various open source models via Anyscale Endpoints API
"""

from typing import Dict, Any, Optional, List
import os


class AnyscalePlugin:
    """Plugin for Anyscale Endpoints models"""
    
    name = "anyscale"
    version = "1.0.0"
    description = "Integration with Anyscale Endpoints (various open source models)"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.base_url = "https://api.endpoints.anyscale.com/v1"
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Anyscale Endpoints plugin"""
        try:
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("ANYSCALE_API_KEY")
            )
            
            if not self.api_key:
                return False
                
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing Anyscale Endpoints plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Anyscale Endpoints action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}
        
        try:
            if action == "chat":
                return self._chat(params)
            elif action == "complete":
                return self._complete(params)
            elif action == "list_models":
                return self._list_models()
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion"""
        import requests
        
        messages = params.get("messages", [])
        model = params.get("model", "meta-llama/Llama-2-7b-chat-hf")
        # Popular models:
        # - meta-llama/Llama-2-7b-chat-hf
        # - meta-llama/Llama-2-13b-chat-hf
        # - meta-llama/Llama-2-70b-chat-hf
        # - codellama/CodeLlama-34b-Instruct-hf
        # - mistralai/Mistral-7B-Instruct-v0.1
        
        max_tokens = params.get("max_tokens", 512)
        temperature = params.get("temperature", 0.7)
        top_p = params.get("top_p", 0.7)
        top_k = params.get("top_k", 50)
        repetition_penalty = params.get("repetition_penalty", 1)
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "repetition_penalty": repetition_penalty
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "response": data["choices"][0]["message"]["content"],
            "model": data["model"],
            "finish_reason": data["choices"][0]["finish_reason"],
            "usage": data.get("usage", {})
        }
    
    def _complete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Text completion"""
        import requests
        
        prompt = params.get("prompt", "")
        model = params.get("model", "meta-llama/Llama-2-7b-hf")
        # Popular completion models:
        # - meta-llama/Llama-2-7b-hf
        # - meta-llama/Llama-2-13b-hf
        # - meta-llama/Llama-2-70b-hf
        # - codellama/CodeLlama-7b-hf
        # - codellama/CodeLlama-13b-hf
        
        max_tokens = params.get("max_tokens", 512)
        temperature = params.get("temperature", 0.7)
        top_p = params.get("top_p", 0.7)
        top_k = params.get("top_k", 50)
        
        response = requests.post(
            f"{self.base_url}/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "text": data["choices"][0]["text"],
            "model": data["model"],
            "finish_reason": data["choices"][0]["finish_reason"],
            "usage": data.get("usage", {})
        }
    
    def _list_models(self) -> Dict[str, Any]:
        """List available models"""
        import requests
        
        response = requests.get(
            f"{self.base_url}/models",
            headers={
                "Authorization": f"Bearer {self.api_key}"
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "models": [
                {
                    "id": model["id"],
                    "created": model.get("created"),
                    "type": model.get("type")
                }
                for model in data.get("data", [])
            ],
            "count": len(data.get("data", []))
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = AnyscalePlugin
PLUGIN_NAME = "anyscale"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Anyscale Endpoints models"
PLUGIN_ACTIONS = ["chat", "complete", "list_models"]