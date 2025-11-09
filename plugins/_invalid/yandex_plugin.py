"""
Yandex AI Model Provider Plugin
Supports Yandex YaLM models for chat completions
"""

from typing import Dict, Any, Optional, List
import os
import requests
import json


class YandexPlugin:
    """Plugin for Yandex YaLM models"""
    
    name = "yandex"
    version = "1.0.0"
    description = "Integration with Yandex YaLM models"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.folder_id: Optional[str] = None
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1"
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Yandex plugin"""
        try:
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("YANDEX_API_KEY")
            )
            
            # Get folder ID from config or environment
            self.folder_id = (
                config.get("folder_id") if config 
                else os.getenv("YANDEX_FOLDER_ID")
            )
            
            if not self.api_key:
                return False
                
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing Yandex plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Yandex action"""
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
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }
        if self.folder_id:
            headers["x-folder-id"] = self.folder_id
        return headers
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion"""
        messages = params.get("messages", [])
        model = params.get("model", "yandexgpt-lite")  # yandexgpt-lite, yandexgpt-pro, yandexgpt
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 2000)
        
        # Convert to Yandex format
        yandex_messages = []
        for msg in messages:
            yandex_messages.append({
                "role": msg["role"],
                "text": msg["content"]
            })
        
        request_data = {
            "modelUri": f"gpt://{self.folder_id or 'default'}/{model}",
            "completionOptions": {
                "temperature": temperature,
                "maxTokens": max_tokens
            },
            "messages": yandex_messages
        }
        
        response = requests.post(
            f"{self.base_url}/completion",
            headers=self._get_headers(),
            json=request_data
        )
        
        if response.status_code != 200:
            return {"error": f"API request failed: {response.status_code} - {response.text}"}
        
        result = response.json()
        
        return {
            "response": result["result"]["alternatives"][0]["message"]["text"],
            "model": model,
            "finish_reason": result["result"]["alternatives"][0]["status"],
            "usage": {
                "prompt_tokens": result["result"]["usage"]["inputTextTokens"],
                "completion_tokens": result["result"]["usage"]["completionTokens"],
                "total_tokens": result["result"]["usage"]["totalTokens"]
            }
        }
    
    def _stream_chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stream chat completion"""
        messages = params.get("messages", [])
        model = params.get("model", "yandexgpt-lite")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 2000)
        
        # Convert to Yandex format
        yandex_messages = []
        for msg in messages:
            yandex_messages.append({
                "role": msg["role"],
                "text": msg["content"]
            })
        
        request_data = {
            "modelUri": f"gpt://{self.folder_id or 'default'}/{model}",
            "completionOptions": {
                "temperature": temperature,
                "maxTokens": max_tokens,
                "stream": True
            },
            "messages": yandex_messages
        }
        
        response = requests.post(
            f"{self.base_url}/completion",
            headers=self._get_headers(),
            json=request_data,
            stream=True
        )
        
        if response.status_code != 200:
            return {"error": f"API request failed: {response.status_code} - {response.text}"}
        
        # Collect streamed response
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    if "result" in data and "alternatives" in data["result"]:
                        alternative = data["result"]["alternatives"][0]
                        if "message" in alternative and "text" in alternative["message"]:
                            full_response += alternative["message"]["text"]
                except json.JSONDecodeError:
                    continue
        
        return {
            "response": full_response,
            "model": model,
            "streamed": True
        }
    
    def _list_models(self) -> Dict[str, Any]:
        """List available models"""
        # Yandex doesn't have a dedicated list models endpoint, so we return known models
        models = [
            {
                "id": "yandexgpt-lite",
                "name": "YandexGPT Lite",
                "description": "Lightweight model for fast responses"
            },
            {
                "id": "yandexgpt-pro",
                "name": "YandexGPT Pro", 
                "description": "Professional model for complex tasks"
            },
            {
                "id": "yandexgpt",
                "name": "YandexGPT",
                "description": "General purpose model"
            }
        ]
        
        return {
            "models": models,
            "count": len(models)
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = YandexPlugin
PLUGIN_NAME = "yandex"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Yandex YaLM models"
PLUGIN_ACTIONS = ["chat", "stream_chat", "list_models"]