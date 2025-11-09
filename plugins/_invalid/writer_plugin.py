"""
Writer AI Model Provider Plugin
Supports chat, paraphrase, and content generation
"""

from typing import Dict, Any, Optional, List
import os
import requests


class WriterPlugin:
    """Plugin for Writer AI models"""
    
    name = "writer"
    version = "1.0.0"
    description = "Integration with Writer AI for chat, paraphrase, and content generation"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.base_url = "https://api.writer.com"
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Writer plugin"""
        try:
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("WRITER_API_KEY")
            )
            
            if not self.api_key:
                return False
                
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing Writer plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Writer action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}
        
        try:
            if action == "chat":
                return self._chat(params)
            elif action == "paraphrase":
                return self._paraphrase(params)
            elif action == "content_generation":
                return self._content_generation(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion"""
        message = params.get("message", "")
        model = params.get("model", "palmyra-x-004")  # Default model, adjust as needed
        temperature = params.get("temperature", 0.7)
        
        url = f"{self.base_url}/chat"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "message": message,
            "model": model,
            "temperature": temperature
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        return {
            "response": result.get("response", ""),
            "model": model
        }
    
    def _paraphrase(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Paraphrase text"""
        text = params.get("text", "")
        style = params.get("style", "neutral")  # e.g., neutral, formal, casual
        
        url = f"{self.base_url}/paraphrase"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "style": style
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        return {
            "paraphrased_text": result.get("paraphrased_text", ""),
            "style": style
        }
    
    def _content_generation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content"""
        prompt = params.get("prompt", "")
        model = params.get("model", "palmyra-x-004")
        max_tokens = params.get("max_tokens", 500)
        temperature = params.get("temperature", 0.7)
        
        url = f"{self.base_url}/generate"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "prompt": prompt,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        return {
            "generated_content": result.get("generated_content", ""),
            "model": model
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = WriterPlugin
PLUGIN_NAME = "writer"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Writer AI for chat, paraphrase, and content generation"
PLUGIN_ACTIONS = ["chat", "paraphrase", "content_generation"]