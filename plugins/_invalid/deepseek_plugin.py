"""
DeepSeek Model Provider Plugin
Supports DeepSeek chat and code completion models
"""

from typing import Dict, Any, Optional, List
import os


class DeepSeekPlugin:
    """Plugin for DeepSeek models"""
    
    name = "deepseek"
    version = "1.0.0"
    description = "Integration with DeepSeek AI (deepseek-chat, deepseek-coder)"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.base_url = "https://api.deepseek.com"
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the DeepSeek plugin"""
        try:
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("DEEPSEEK_API_KEY")
            )
            
            if not self.api_key:
                return False
                
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing DeepSeek plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a DeepSeek action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}
        
        try:
            if action == "chat":
                return self._chat(params)
            elif action == "complete":
                return self._complete(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion"""
        import requests
        
        messages = params.get("messages", [])
        model = params.get("model", "deepseek-chat")
        
        max_tokens = params.get("max_tokens", 512)
        temperature = params.get("temperature", 0.7)
        top_p = params.get("top_p", 0.7)
        
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
                "top_p": top_p
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
        """Code completion"""
        import requests
        
        prompt = params.get("prompt", "")
        model = params.get("model", "deepseek-coder")
        
        max_tokens = params.get("max_tokens", 512)
        temperature = params.get("temperature", 0.7)
        top_p = params.get("top_p", 0.7)
        
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
                "top_p": top_p
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
    
    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = DeepSeekPlugin
PLUGIN_NAME = "deepseek"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with DeepSeek AI models"
PLUGIN_ACTIONS = ["chat", "complete"]