"""
Fireworks AI Model Provider Plugin
Supports various Fireworks AI models for chat completions
"""

from typing import Dict, Any, Optional, List
import os
import json
import requests


class FireworksPlugin:
    """Plugin for Fireworks AI models"""
    
    name = "fireworks"
    version = "1.0.0"
    description = "Integration with Fireworks AI models"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.base_url = "https://api.fireworks.ai/inference/v1"
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Fireworks plugin"""
        try:
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("FIREWORKS_API_KEY")
            )
            
            if not self.api_key:
                return False
                
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing Fireworks plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Fireworks action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}
        
        try:
            if action == "chat":
                return self._chat(params)
            elif action == "stream_chat":
                return self._stream_chat(params)
            elif action == "list_models":
                return self._list_models()
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion"""
        messages = params.get("messages", [])
        model = params.get("model", "accounts/fireworks/models/llama-v2-7b-chat")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", None)
        top_p = params.get("top_p", 1.0)
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "response": data["choices"][0]["message"]["content"],
            "model": data["model"],
            "finish_reason": data["choices"][0]["finish_reason"],
            "usage": data.get("usage", {})
        }
    
    def _stream_chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stream chat completion"""
        messages = params.get("messages", [])
        model = params.get("model", "accounts/fireworks/models/llama-v2-7b-chat")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", None)
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Collect streamed response
        full_response = ""
        with requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers,
            stream=True
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            if chunk["choices"][0]["delta"].get("content"):
                                full_response += chunk["choices"][0]["delta"]["content"]
                        except:
                            pass
        
        return {
            "response": full_response,
            "model": model,
            "streamed": True
        }
    
    def _list_models(self) -> Dict[str, Any]:
        """List available models"""
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        response = requests.get(
            f"{self.base_url}/models",
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "models": [
                {
                    "id": model["id"],
                    "created": model.get("created"),
                    "owned_by": model.get("owned_by")
                }
                for model in data["data"]
            ],
            "count": len(data["data"])
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = FireworksPlugin
PLUGIN_NAME = "fireworks"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Fireworks AI models"
PLUGIN_ACTIONS = ["chat", "stream_chat", "list_models"]