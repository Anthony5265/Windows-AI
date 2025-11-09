"""
Jan AI Local Model Platform Plugin
"""

from typing import Dict, Any, Optional, List
import os


class JanAIPlugin:
    """Plugin for Jan AI local models"""
    
    name = "janai"
    version = "1.0.0"
    description = "Integration with Jan AI local model platform"
    author = "Windows AI Team"
    
    def __init__(self):
        self.base_url: str = "http://localhost:1337"
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Jan AI plugin"""
        try:
            import requests
            
            self.base_url = (
                config.get("base_url") if config 
                else os.getenv("JANAI_HOST", "http://localhost:1337")
            )
            
            self.client = requests
            self._initialized = True
            return True
            
        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing Jan AI plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Jan AI action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}
            
        try:
            if action == "chat":
                return self._chat(params)
            elif action == "models":
                return self._list_models()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion"""
        model = params.get("model", "llama2-7b")
        messages = params.get("messages", [])
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 500)
        
        response = self.client.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result["choices"][0]["message"]["content"],
                "usage": result.get("usage", {})
            }
        return {"success": False, "error": response.text}
    
    def _list_models(self) -> Dict[str, Any]:
        """List available models"""
        response = self.client.get(f"{self.base_url}/v1/models")
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "models": result.get("data", [])
            }
        return {"success": False, "error": response.text}
    
    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        return True
