"""
Text Generation WebUI (oobabooga) Plugin
"""

from typing import Dict, Any, Optional, List
import os


class TextGenWebUIPlugin:
    """Plugin for Text Generation WebUI (oobabooga)"""
    
    name = "textgen_webui"
    version = "1.0.0"
    description = "Integration with Text Generation WebUI (oobabooga)"
    author = "Windows AI Team"
    
    def __init__(self):
        self.base_url: str = "http://localhost:5000"
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Text Generation WebUI plugin"""
        try:
            import requests
            
            self.base_url = (
                config.get("base_url") if config 
                else os.getenv("TEXTGEN_HOST", "http://localhost:5000")
            )
            
            self.client = requests
            self._initialized = True
            return True
            
        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing Text Generation WebUI plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Text Generation WebUI action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}
            
        try:
            if action == "generate":
                return self._generate(params)
            elif action == "chat":
                return self._chat(params)
            elif action == "model":
                return self._get_model_info()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text"""
        prompt = params.get("prompt", "")
        max_new_tokens = params.get("max_new_tokens", 200)
        temperature = params.get("temperature", 0.7)
        top_p = params.get("top_p", 0.9)
        
        response = self.client.post(
            f"{self.base_url}/api/v1/generate",
            json={
                "prompt": prompt,
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "do_sample": True
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result["results"][0]["text"]
            }
        return {"success": False, "error": response.text}
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion"""
        user_input = params.get("user_input", "")
        history = params.get("history", {"internal": [], "visible": []})
        
        response = self.client.post(
            f"{self.base_url}/api/v1/chat",
            json={
                "user_input": user_input,
                "history": history
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result["results"][0]["history"]["visible"][-1][1],
                "history": result["results"][0]["history"]
            }
        return {"success": False, "error": response.text}
    
    def _get_model_info(self) -> Dict[str, Any]:
        """Get current model information"""
        response = self.client.get(f"{self.base_url}/api/v1/model")
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "model": result.get("result", "")
            }
        return {"success": False, "error": response.text}
    
    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        return True
