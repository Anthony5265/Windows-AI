"""
Perplexity AI Model Provider Plugin
Supports pplx-7b-online, pplx-70b-online models with web search
"""

from typing import Dict, Any, Optional, List
import os


class PerplexityPlugin:
    """Plugin for Perplexity AI models"""
    
    name = "perplexity"
    version = "1.0.0"
    description = "Integration with Perplexity AI (online LLMs with search)"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.base_url = "https://api.perplexity.ai"
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Perplexity plugin"""
        try:
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("PERPLEXITY_API_KEY")
            )
            
            if not self.api_key:
                return False
                
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing Perplexity plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Perplexity action"""
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
        """Chat completion with optional web search"""
        import requests
        
        messages = params.get("messages", [])
        model = params.get("model", "pplx-70b-online")  # pplx-7b-online, pplx-70b-online, pplx-7b-chat, pplx-70b-chat
        temperature = params.get("temperature", 0.2)
        max_tokens = params.get("max_tokens", None)
        top_p = params.get("top_p", 0.9)
        top_k = params.get("top_k", 0)
        presence_penalty = params.get("presence_penalty", 0)
        frequency_penalty = params.get("frequency_penalty", 1)
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "stream": False
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
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
        
        # Include citations if model is an "online" variant
        if "online" in model:
            result["citations"] = data["choices"][0]["message"].get("citations", [])
        
        return result
    
    def _stream_chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stream chat completion"""
        import requests
        import json
        
        messages = params.get("messages", [])
        model = params.get("model", "pplx-70b-online")
        temperature = params.get("temperature", 0.2)
        max_tokens = params.get("max_tokens", None)
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
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
        citations = []
        
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
                        
                        # Collect citations from final message
                        if "citations" in chunk["choices"][0].get("message", {}):
                            citations = chunk["choices"][0]["message"]["citations"]
                    except json.JSONDecodeError:
                        continue
        
        result = {
            "response": full_response,
            "model": model,
            "streamed": True
        }
        
        if citations:
            result["citations"] = citations
        
        return result
    
    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = PerplexityPlugin
PLUGIN_NAME = "perplexity"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Perplexity AI (online models with web search)"
PLUGIN_ACTIONS = ["chat", "stream_chat"]
