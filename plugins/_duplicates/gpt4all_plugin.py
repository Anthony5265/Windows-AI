"""
GPT4All Plugin for Windows AI
Supports local model loading and chat functionality
"""

import json
import requests
import asyncio
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging
import os

class GPT4AllPlugin:
    """GPT4All integration plugin"""
    
    def __init__(self):
        self.name = "gpt4all"
        self.version = "1.0.0"
        self.description = "GPT4All local model integration for chat and text generation"
        self.logger = logging.getLogger(__name__)
        
        # Default GPT4All settings
        self.default_settings = {
            "api_url": "http://localhost:4891",
            "max_tokens": 500,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "repeat_last_n": 64,
            "n_batch": 512,
            "n_predict": None,
            "stream": False,
            "models_path": os.path.expanduser("~/.local/share/nomic.ai/GPT4All/")
        }
        
        self.settings = self.default_settings.copy()
        self.session = requests.Session()
        self.current_model = None
        
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin with configuration"""
        try:
            self.settings.update(config.get("gpt4all", {}))
            
            # Test connection to GPT4All
            if self._test_connection():
                self.logger.info("GPT4All plugin initialized successfully")
                return True
            else:
                self.logger.warning("Could not connect to GPT4All server")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize GPT4All plugin: {e}")
            return False
    
    def _test_connection(self) -> bool:
        """Test connection to GPT4All server"""
        try:
            response = self.session.get(f"{self.settings['api_url']}/v1/models", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> Dict[str, Any]:
        """List available models"""
        try:
            response = self.session.get(f"{self.settings['api_url']}/v1/models", timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                return {
                    "success": True,
                    "models": models_data.get("models", []),
                    "provider": "GPT4All",
                    "local": True
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to list models: {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def load_model(self, model_name: str) -> Dict[str, Any]:
        """Load a specific model"""
        try:
            data = {"model": model_name}
            response = self.session.post(
                f"{self.settings['api_url']}/v1/models/load",
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                self.current_model = model_name
                return {
                    "success": True,
                    "model": model_name,
                    "message": f"Model {model_name} loaded successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to load model: {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using GPT4All"""
        try:
            # Merge kwargs with settings
            params = {
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", self.settings["max_tokens"]),
                "temperature": kwargs.get("temperature", self.settings["temperature"]),
                "top_p": kwargs.get("top_p", self.settings["top_p"]),
                "top_k": kwargs.get("top_k", self.settings["top_k"]),
                "repeat_penalty": kwargs.get("repeat_penalty", self.settings["repeat_penalty"]),
                "repeat_last_n": kwargs.get("repeat_last_n", self.settings["repeat_last_n"]),
                "n_batch": kwargs.get("n_batch", self.settings["n_batch"]),
                "stream": kwargs.get("stream", self.settings["stream"])
            }
            
            # Add n_predict if specified
            if kwargs.get("n_predict") or self.settings["n_predict"]:
                params["n_predict"] = kwargs.get("n_predict", self.settings["n_predict"])
            
            response = self.session.post(
                f"{self.settings['api_url']}/v1/completions",
                json=params,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "text": result.get("choices", [{}])[0].get("text", ""),
                    "model": result.get("model", self.current_model or "gpt4all"),
                    "usage": result.get("usage", {}),
                    "finish_reason": result.get("choices", [{}])[0].get("finish_reason")
                }
            else:
                return {
                    "success": False,
                    "error": f"GPT4All API error: {response.status_code}"
                }
                
        except Exception as e:
            self.logger.error(f"Text generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Chat with GPT4All model"""
        try:
            # Format messages for GPT4All chat completion
            params = {
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.settings["max_tokens"]),
                "temperature": kwargs.get("temperature", self.settings["temperature"]),
                "top_p": kwargs.get("top_p", self.settings["top_p"]),
                "top_k": kwargs.get("top_k", self.settings["top_k"]),
                "repeat_penalty": kwargs.get("repeat_penalty", self.settings["repeat_penalty"]),
                "repeat_last_n": kwargs.get("repeat_last_n", self.settings["repeat_last_n"]),
                "n_batch": kwargs.get("n_batch", self.settings["n_batch"]),
                "stream": kwargs.get("stream", self.settings["stream"])
            }
            
            # Add n_predict if specified
            if kwargs.get("n_predict") or self.settings["n_predict"]:
                params["n_predict"] = kwargs.get("n_predict", self.settings["n_predict"])
            
            response = self.session.post(
                f"{self.settings['api_url']}/v1/chat/completions",
                json=params,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                return {
                    "success": True,
                    "response": assistant_message,
                    "messages": messages + [{"role": "assistant", "content": assistant_message}],
                    "model": result.get("model", self.current_model or "gpt4all"),
                    "usage": result.get("usage", {}),
                    "finish_reason": result.get("choices", [{}])[0].get("finish_reason")
                }
            else:
                return {
                    "success": False,
                    "error": f"GPT4All API error: {response.status_code}"
                }
                
        except Exception as e:
            self.logger.error(f"Chat failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs):
        """Stream chat responses from GPT4All"""
        try:
            params = {
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.settings["max_tokens"]),
                "temperature": kwargs.get("temperature", self.settings["temperature"]),
                "top_p": kwargs.get("top_p", self.settings["top_p"]),
                "top_k": kwargs.get("top_k", self.settings["top_k"]),
                "repeat_penalty": kwargs.get("repeat_penalty", self.settings["repeat_penalty"]),
                "repeat_last_n": kwargs.get("repeat_last_n", self.settings["repeat_last_n"]),
                "n_batch": kwargs.get("n_batch", self.settings["n_batch"]),
                "stream": True
            }
            
            response = self.session.post(
                f"{self.settings['api_url']}/v1/chat/completions",
                json=params,
                stream=True,
                timeout=60
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:]
                            if data != '[DONE]':
                                try:
                                    chunk = json.loads(data)
                                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                                except json.JSONDecodeError:
                                    continue
            else:
                yield f"Error: GPT4All API error {response.status_code}"
                
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        try:
            response = self.session.get(f"{self.settings['api_url']}/v1/models", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                models = models_data.get("models", [])
                current = models[0] if models else {}
                
                return {
                    "success": True,
                    "model_name": current.get("id", self.current_model or "Unknown"),
                    "provider": "GPT4All",
                    "local": True,
                    "capabilities": ["text-generation", "chat", "completion"],
                    "models_available": len(models),
                    "current_model": self.current_model
                }
            else:
                return {
                    "success": False,
                    "error": "Could not retrieve model info"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status"""
        try:
            response = self.session.get(f"{self.settings['api_url']}/v1/models", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                models = models_data.get("models", [])
                
                return {
                    "success": True,
                    "loaded": len(models) > 0,
                    "current_model": self.current_model,
                    "available_models": [model.get("id") for model in models],
                    "server_running": True
                }
            else:
                return {
                    "success": False,
                    "server_running": False,
                    "error": "Server not responding"
                }
        except Exception as e:
            return {
                "success": False,
                "server_running": False,
                "error": str(e)
            }
    
    def unload_model(self) -> Dict[str, Any]:
        """Unload the current model"""
        try:
            response = self.session.delete(f"{self.settings['api_url']}/v1/models", timeout=10)
            if response.status_code == 200:
                self.current_model = None
                return {
                    "success": True,
                    "message": "Model unloaded successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to unload model: {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_settings(self, new_settings: Dict[str, Any]) -> bool:
        """Update plugin settings"""
        try:
            self.settings.update(new_settings)
            return True
        except Exception as e:
            self.logger.error(f"Failed to update settings: {e}")
            return False
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current plugin settings"""
        return self.settings.copy()
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GPT4All action"""
        if action == "list_models":
            return self.list_models()
        elif action == "load_model":
            return self.load_model(params.get("model_name", ""))
        elif action == "unload_model":
            return self.unload_model()
        elif action == "get_model_info":
            return self.get_model_info()
        elif action == "get_model_status":
            return self.get_model_status()
        elif action == "generate_text":
            return asyncio.run(self.generate_text(**params))
        elif action == "chat":
            return asyncio.run(self.chat(**params))
        else:
            return {"error": f"Unknown action: {action}"}
    
    def cleanup(self):
        """Cleanup resources"""
        if self.session:
            self.session.close()
        self.current_model = None

# Plugin registration
plugin = GPT4AllPlugin()

def get_plugin():
    """Return plugin instance"""
    return plugin

def get_plugin_info():
    """Return plugin information"""
    return {
        "name": plugin.name,
        "version": plugin.version,
        "description": plugin.description,
        "type": "local_model",
        "capabilities": ["text_generation", "chat", "completion", "streaming"],
        "settings": plugin.default_settings
    }

# Plugin metadata for dynamic loading
PLUGIN_CLASS = GPT4AllPlugin
PLUGIN_NAME = "gpt4all"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "GPT4All local model integration for chat and text generation"
PLUGIN_ACTIONS = [
    "list_models", "load_model", "unload_model", "get_model_info", 
    "get_model_status", "generate_text", "chat"
]