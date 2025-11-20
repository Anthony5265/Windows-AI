"""
Ollama Local Model Platform Plugin
Supports 100+ local models
"""

from typing import Dict, Any, Optional, List
import os


class OllamaPlugin:
    """Plugin for Ollama local models"""
    
    name = "ollama"
    version = "1.0.0"
    description = "Integration with Ollama local model platform (100+ models)"
    author = "Windows AI Team"
    
    def __init__(self):
        self.base_url: str = "http://localhost:11434"
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Ollama plugin"""
        try:
            import requests
            
            # Get base URL from config or use default
            self.base_url = (
                config.get("base_url") if config 
                else os.getenv("OLLAMA_HOST", "http://localhost:11434")
            )
            
            self.client = requests
            
            # Test connection
            response = self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                self._initialized = True
                return True
            return False
            
        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing Ollama plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Ollama action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}
            
        try:
            if action == "chat":
                return self._chat(params)
            elif action == "generate":
                return self._generate(params)
            elif action == "embeddings":
                return self._get_embeddings(params)
            elif action == "list":
                return self._list_models()
            elif action == "pull":
                return self._pull_model(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion"""
        model = params.get("model", "llama2")
        messages = params.get("messages", [])
        stream = params.get("stream", False)
        
        response = self.client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": stream
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result.get("message", {}).get("content", ""),
                "model": result.get("model"),
                "done": result.get("done", True)
            }
        return {"success": False, "error": response.text}
    
    def _generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text completion"""
        model = params.get("model", "llama2")
        prompt = params.get("prompt", "")
        stream = params.get("stream", False)
        
        response = self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": stream
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result.get("response", ""),
                "model": result.get("model"),
                "done": result.get("done", True)
            }
        return {"success": False, "error": response.text}
    
    def _get_embeddings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get text embeddings"""
        model = params.get("model", "llama2")
        prompt = params.get("prompt", "")
        
        response = self.client.post(
            f"{self.base_url}/api/embeddings",
            json={
                "model": model,
                "prompt": prompt
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "embedding": result.get("embedding", [])
            }
        return {"success": False, "error": response.text}
    
    def _list_models(self) -> Dict[str, Any]:
        """List available models"""
        response = self.client.get(f"{self.base_url}/api/tags")
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "models": result.get("models", [])
            }
        return {"success": False, "error": response.text}
    
    def _pull_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Pull/download a model"""
        name = params.get("name", "")
        
        response = self.client.post(
            f"{self.base_url}/api/pull",
            json={"name": name}
        )
        
        if response.status_code == 200:
            return {"success": True, "status": "Model pulled successfully"}
        return {"success": False, "error": response.text}
    
    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        return True
