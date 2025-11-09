"""
FastChat Plugin
Supports multi-model serving via FastChat API
"""

from typing import Dict, Any, Optional, List
import os


class FastChatPlugin:
    """Plugin for FastChat multi-model serving"""
    
    name = "fastchat"
    version = "1.0.0"
    description = "Integration with FastChat for local multi-model serving"
    author = "Windows AI Team"
    
    def __init__(self):
        self.base_url: Optional[str] = None
        self.client = None
        self._initialized = False
        self.available_models: List[str] = []
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the FastChat plugin"""
        try:
            import openai
            
            # Get base URL from config or environment
            self.base_url = (
                config.get("base_url") if config 
                else os.getenv("FASTCHAT_BASE_URL", "http://localhost:8000")
            )
            
            # Initialize OpenAI client with custom base URL
            self.client = openai.OpenAI(
                api_key="dummy",  # FastChat doesn't require API key
                base_url=self.base_url + "/v1"
            )
            
            # Test connection and get available models
            try:
                models_response = self.client.models.list()
                self.available_models = [model.id for model in models_response.data]
            except Exception:
                # If models endpoint fails, assume basic models
                self.available_models = ["default"]
            
            self._initialized = True
            return True
            
        except ImportError:
            print("openai package not installed. Install with: pip install openai")
            return False
        except Exception as e:
            print(f"Error initializing FastChat plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a FastChat action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please check FastChat server."}
        
        try:
            if action == "chat":
                return self._chat(params)
            elif action == "text_generation":
                return self._text_generation(params)
            elif action == "list_models":
                return self._list_models(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion"""
        messages = params.get("messages", [])
        model = params.get("model", self.available_models[0] if self.available_models else "default")
        max_tokens = params.get("max_tokens", 500)
        temperature = params.get("temperature", 0.7)
        
        if model not in self.available_models and self.available_models != ["default"]:
            return {"error": f"Model {model} not available. Available models: {self.available_models}"}
        
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return {
            "response": response.choices[0].message.content,
            "model": model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    def _text_generation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Text generation"""
        prompt = params.get("prompt", "")
        model = params.get("model", self.available_models[0] if self.available_models else "default")
        max_tokens = params.get("max_tokens", 500)
        temperature = params.get("temperature", 0.7)
        
        if model not in self.available_models and self.available_models != ["default"]:
            return {"error": f"Model {model} not available. Available models: {self.available_models}"}
        
        response = self.client.completions.create(
            model=model,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return {
            "text": response.choices[0].text,
            "model": model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    def _list_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available models"""
        return {
            "models": self.available_models,
            "count": len(self.available_models)
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.client = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = FastChatPlugin
PLUGIN_NAME = "fastchat"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with FastChat for local multi-model serving"
PLUGIN_ACTIONS = [
    "chat", "text_generation", "list_models"
]