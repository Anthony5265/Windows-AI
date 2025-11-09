"""
Inflection AI Model Provider Plugin
Supports Pi assistant for conversational chat
"""

from typing import Dict, Any, Optional, List
import os


class InflectionPlugin:
    """Plugin for Inflection AI models"""
    
    name = "inflection"
    version = "1.0.0"
    description = "Integration with Inflection AI (Pi assistant)"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.base_url = "https://api.inflection.ai"
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Inflection plugin"""
        try:
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("INFLECTION_API_KEY")
            )
            
            if not self.api_key:
                return False
                
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing Inflection plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Inflection action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}
        
        try:
            if action == "chat":
                return self._chat(params)
            elif action == "stream_chat":
                return self._stream_chat(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion with Pi assistant"""
        import requests
        
        messages = params.get("messages", [])
        model = params.get("model", "pi")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 2048)
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        
        result = {
            "response": data["choices"][0]["message"]["content"],
            "model": data["model"],
            "finish_reason": data["choices"][0]["finish_reason"],
            "usage": data.get("usage", {})
        }
        
        return result
    
    def _stream_chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stream chat completion"""
        import requests
        import json
        
        messages = params.get("messages", [])
        model = params.get("model", "pi")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 2048)
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }
        
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            stream=True,
            timeout=60
        )
        response.raise_for_status()
        
        # Collect streamed response
        full_response = ""
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith("data: "):
                    data_text = line_text[6:]  # Remove "data: " prefix
                    if data_text == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(data_text)
                        delta = chunk["choices"][0].get("delta", {})
                        
                        if "content" in delta:
                            full_response += delta["content"]
                    except json.JSONDecodeError:
                        continue
        
        result = {
            "response": full_response,
            "model": model,
            "streamed": True
        }
        
        return result
    
    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = InflectionPlugin
PLUGIN_NAME = "inflection"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Inflection AI (Pi assistant)"
PLUGIN_ACTIONS = ["chat", "stream_chat"]