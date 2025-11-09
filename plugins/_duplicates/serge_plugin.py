"""
Serge Plugin for Windows AI
Supports self-hosted LLM chat interface via Serge API
"""

import json
import requests
import asyncio
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging
import os

class SergePlugin:
    """Serge integration plugin"""

    def __init__(self):
        self.name = "serge"
        self.version = "1.0.0"
        self.description = "Serge self-hosted LLM chat interface integration"
        self.logger = logging.getLogger(__name__)

        # Default Serge settings
        self.default_settings = {
            "api_url": "http://localhost:8008",
            "default_model": "7B",
            "temperature": 0.1,
            "top_k": 50,
            "top_p": 0.95,
            "max_tokens": 2048,
            "context_window": 2048,
            "gpu_layers": None,
            "repeat_last_n": 64,
            "repeat_penalty": 1.3,
            "n_threads": 4,
            "init_prompt": "Below is an instruction that describes a task. Write a response that appropriately completes the request.",
        }

        self.settings = self.default_settings.copy()
        self.session = requests.Session()
        self.current_chat_id = None

    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin with configuration"""
        try:
            self.settings.update(config.get("serge", {}))

            # Test connection to Serge
            if self._test_connection():
                self.logger.info("Serge plugin initialized successfully")
                return True
            else:
                self.logger.warning("Could not connect to Serge server")
                return False

        except Exception as e:
            self.logger.error(f"Failed to initialize Serge plugin: {e}")
            return False

    def _test_connection(self) -> bool:
        """Test connection to Serge server"""
        try:
            response = self.session.get(f"{self.settings['api_url']}/api/model/installed", timeout=5)
            return response.status_code == 200
        except:
            return False

    def list_models(self) -> Dict[str, Any]:
        """List available models"""
        try:
            response = self.session.get(f"{self.settings['api_url']}/api/model/all", timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model["name"] for model in models_data if model["available"]]
                return {
                    "success": True,
                    "models": available_models,
                    "provider": "Serge",
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
        """Load a specific model by creating a chat with it"""
        try:
            # Check if model is available
            models_response = self.list_models()
            if not models_response["success"]:
                return models_response

            if model_name not in models_response["models"]:
                return {
                    "success": False,
                    "error": f"Model {model_name} not available"
                }

            # Create a new chat with the specified model
            chat_data = {
                "model": model_name,
                "temperature": self.settings["temperature"],
                "top_k": self.settings["top_k"],
                "top_p": self.settings["top_p"],
                "max_length": self.settings["max_tokens"],
                "context_window": self.settings["context_window"],
                "gpu_layers": self.settings["gpu_layers"],
                "repeat_last_n": self.settings["repeat_last_n"],
                "repeat_penalty": self.settings["repeat_penalty"],
                "init_prompt": self.settings["init_prompt"],
                "n_threads": self.settings["n_threads"],
            }

            response = self.session.post(
                f"{self.settings['api_url']}/api/chat/",
                data=chat_data,
                timeout=30
            )

            if response.status_code == 200:
                self.current_chat_id = response.json()
                return {
                    "success": True,
                    "model": model_name,
                    "chat_id": self.current_chat_id,
                    "message": f"Model {model_name} loaded successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to load model: {response.status_code} - {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using Serge"""
        try:
            # Ensure we have a chat loaded
            if not self.current_chat_id:
                load_result = self.load_model(self.settings["default_model"])
                if not load_result["success"]:
                    return load_result

            # Send the prompt
            params = {
                "prompt": prompt
            }

            response = self.session.post(
                f"{self.settings['api_url']}/api/chat/{self.current_chat_id}/question",
                data=params,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "text": result,
                    "model": self.settings["default_model"],
                    "chat_id": self.current_chat_id
                }
            else:
                return {
                    "success": False,
                    "error": f"Serge API error: {response.status_code}"
                }

        except Exception as e:
            self.logger.error(f"Text generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Chat with Serge model"""
        try:
            # Ensure we have a chat loaded
            if not self.current_chat_id:
                load_result = self.load_model(self.settings["default_model"])
                if not load_result["success"]:
                    return load_result

            # Extract the last user message as the prompt
            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            if not user_messages:
                return {
                    "success": False,
                    "error": "No user message found in messages"
                }

            prompt = user_messages[-1]["content"]

            # Send the prompt
            params = {
                "prompt": prompt
            }

            response = self.session.post(
                f"{self.settings['api_url']}/api/chat/{self.current_chat_id}/question",
                data=params,
                timeout=120
            )

            if response.status_code == 200:
                assistant_response = response.json()

                return {
                    "success": True,
                    "response": assistant_response,
                    "messages": messages + [{"role": "assistant", "content": assistant_response}],
                    "model": self.settings["default_model"],
                    "chat_id": self.current_chat_id
                }
            else:
                return {
                    "success": False,
                    "error": f"Serge API error: {response.status_code}"
                }

        except Exception as e:
            self.logger.error(f"Chat failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs):
        """Stream chat responses from Serge"""
        try:
            # Ensure we have a chat loaded
            if not self.current_chat_id:
                load_result = self.load_model(self.settings["default_model"])
                if not load_result["success"]:
                    yield f"Error: {load_result['error']}"
                    return

            # Extract the last user message as the prompt
            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            if not user_messages:
                yield "Error: No user message found in messages"
                return

            prompt = user_messages[-1]["content"]

            # Use streaming endpoint
            params = {
                "prompt": prompt
            }

            response = self.session.get(
                f"{self.settings['api_url']}/api/chat/{self.current_chat_id}/question",
                params=params,
                stream=True,
                timeout=120
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
                                    if chunk.get("event") == "message":
                                        yield chunk.get("data", "")
                                    elif chunk.get("event") == "error":
                                        yield f"Error: {chunk}"
                                        break
                                    elif chunk.get("event") == "close":
                                        break
                                except json.JSONDecodeError:
                                    continue
            else:
                yield f"Error: Serge API error {response.status_code}"

        except Exception as e:
            yield f"Error: {str(e)}"

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        try:
            models_response = self.list_models()
            if not models_response["success"]:
                return models_response

            return {
                "success": True,
                "model_name": self.settings["default_model"],
                "provider": "Serge",
                "local": True,
                "capabilities": ["text-generation", "chat", "completion", "streaming"],
                "models_available": len(models_response["models"]),
                "current_model": self.settings["default_model"],
                "current_chat_id": self.current_chat_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status"""
        try:
            models_response = self.list_models()
            if not models_response["success"]:
                return {
                    "success": False,
                    "server_running": False,
                    "error": "Could not retrieve models"
                }

            return {
                "success": True,
                "loaded": self.current_chat_id is not None,
                "current_model": self.settings["default_model"],
                "available_models": models_response["models"],
                "server_running": True,
                "current_chat_id": self.current_chat_id
            }
        except Exception as e:
            return {
                "success": False,
                "server_running": False,
                "error": str(e)
            }

    def unload_model(self) -> Dict[str, Any]:
        """Unload the current model by clearing the chat"""
        try:
            self.current_chat_id = None
            return {
                "success": True,
                "message": "Model unloaded successfully"
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
        """Execute a Serge action"""
        if action == "list_models":
            return self.list_models()
        elif action == "load_model":
            return self.load_model(params.get("model_name", self.settings["default_model"]))
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
        self.current_chat_id = None

# Plugin registration
plugin = SergePlugin()

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
PLUGIN_CLASS = SergePlugin
PLUGIN_NAME = "serge"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Serge self-hosted LLM chat interface integration"
PLUGIN_ACTIONS = [
    "list_models", "load_model", "unload_model", "get_model_info",
    "get_model_status", "generate_text", "chat"
]