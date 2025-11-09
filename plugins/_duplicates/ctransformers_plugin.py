"""
CTransformers Plugin for Windows AI
Supports GGML models locally using CTransformers library
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

class CTransformersPlugin:
    """CTransformers integration plugin for local GGML models"""
    
    name = "ctransformers"
    version = "1.0.0"
    description = "Local GGML model support using CTransformers"
    author = "Windows AI Team"
    
    def __init__(self):
        self.model = None
        self.model_path = None
        self._initialized = False
        self.logger = logging.getLogger(__name__)
        
        # Default model settings
        self.default_settings = {
            "model_file": None,  # Path to GGML model file
            "model_type": "llama",  # Model type: llama, gpt2, gptj, etc.
            "gpu_layers": 0,  # Number of layers to offload to GPU
            "temperature": 0.7,
            "max_new_tokens": 256,
            "top_p": 0.9,
            "top_k": 50,
            "repetition_penalty": 1.1,
            "batch_size": 512,
            "context_length": 2048,
            "stream": False
        }
        
        self.settings = self.default_settings.copy()
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the CTransformers plugin"""
        try:
            from ctransformers import AutoModelForCausalLM
            
            # Update settings with config
            if config:
                self.settings.update(config.get("ctransformers", {}))
            
            # Check if model file is specified
            model_file = self.settings.get("model_file")
            if not model_file:
                self.logger.error("No model file specified in settings")
                return False
            
            # Check if model file exists
            if not os.path.exists(model_file):
                self.logger.error(f"Model file not found: {model_file}")
                return False
            
            # Load the model
            self.model = AutoModelForCausalLM.from_pretrained(
                model_file_or_path=model_file,
                model_type=self.settings.get("model_type", "llama"),
                gpu_layers=self.settings.get("gpu_layers", 0),
                batch_size=self.settings.get("batch_size", 512),
                context_length=self.settings.get("context_length", 2048)
            )
            
            self.model_path = model_file
            self._initialized = True
            self.logger.info(f"CTransformers plugin initialized with model: {model_file}")
            return True
            
        except ImportError:
            self.logger.error("ctransformers package not installed. Install with: pip install ctransformers")
            return False
        except Exception as e:
            self.logger.error(f"Error initializing CTransformers plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a CTransformers action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please load a model first."}
        
        try:
            if action == "text_generation":
                return self._text_generation(params)
            elif action == "chat":
                return self._chat(params)
            elif action == "stream_text":
                return self._stream_text(params)
            elif action == "get_model_info":
                return self._get_model_info()
            elif action == "list_models":
                return self._list_models()
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}")
            return {"error": str(e)}
    
    def _text_generation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text from prompt"""
        prompt = params.get("prompt", "")
        if not prompt:
            return {"error": "Prompt is required"}
        
        generation_params = {
            "temperature": params.get("temperature", self.settings["temperature"]),
            "max_new_tokens": params.get("max_new_tokens", self.settings["max_new_tokens"]),
            "top_p": params.get("top_p", self.settings["top_p"]),
            "top_k": params.get("top_k", self.settings["top_k"]),
            "repetition_penalty": params.get("repetition_penalty", self.settings["repetition_penalty"]),
            "stop": params.get("stop", [])
        }
        
        # Remove None values
        generation_params = {k: v for k, v in generation_params.items() if v is not None}
        
        generated_text = self.model(prompt, **generation_params)
        
        return {
            "text": generated_text,
            "prompt": prompt,
            "model": self.model_path,
            "parameters": generation_params
        }
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion with message history"""
        messages = params.get("messages", [])
        if not messages:
            return {"error": "Messages are required"}
        
        # Format messages into a prompt
        prompt = self._format_chat_messages(messages)
        
        generation_params = {
            "temperature": params.get("temperature", self.settings["temperature"]),
            "max_new_tokens": params.get("max_new_tokens", self.settings["max_new_tokens"]),
            "top_p": params.get("top_p", self.settings["top_p"]),
            "top_k": params.get("top_k", self.settings["top_k"]),
            "repetition_penalty": params.get("repetition_penalty", self.settings["repetition_penalty"]),
            "stop": ["\nuser:", "\nhuman:", "\nassistant:", "\n\n"]
        }
        
        # Remove None values
        generation_params = {k: v for k, v in generation_params.items() if v is not None}
        
        response = self.model(prompt, **generation_params)
        
        return {
            "response": response.strip(),
            "messages": messages + [{"role": "assistant", "content": response.strip()}],
            "model": self.model_path,
            "parameters": generation_params
        }
    
    def _stream_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stream text generation"""
        prompt = params.get("prompt", "")
        if not prompt:
            return {"error": "Prompt is required"}
        
        generation_params = {
            "temperature": params.get("temperature", self.settings["temperature"]),
            "max_new_tokens": params.get("max_new_tokens", self.settings["max_new_tokens"]),
            "top_p": params.get("top_p", self.settings["top_p"]),
            "top_k": params.get("top_k", self.settings["top_k"]),
            "repetition_penalty": params.get("repetition_penalty", self.settings["repetition_penalty"]),
            "stop": params.get("stop", []),
            "stream": True
        }
        
        # Remove None values
        generation_params = {k: v for k, v in generation_params.items() if v is not None}
        
        generated_text = ""
        for text in self.model(prompt, **generation_params):
            generated_text += text
            # In a real implementation, you would yield or stream this
            # For now, we'll collect it all and return
        
        return {
            "text": generated_text,
            "prompt": prompt,
            "model": self.model_path,
            "parameters": generation_params,
            "streamed": True
        }
    
    def _format_chat_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format chat messages into a prompt"""
        formatted = ""
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                formatted += f"System: {content}\n\n"
            elif role == "user":
                formatted += f"User: {content}\n"
            elif role == "assistant":
                formatted += f"Assistant: {content}\n"
            else:
                formatted += f"{role}: {content}\n"
        
        formatted += "Assistant: "
        return formatted
    
    def _get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        if not self._initialized:
            return {"error": "No model loaded"}
        
        return {
            "model_path": self.model_path,
            "model_type": self.settings.get("model_type", "unknown"),
            "gpu_layers": self.settings.get("gpu_layers", 0),
            "context_length": self.settings.get("context_length", 2048),
            "batch_size": self.settings.get("batch_size", 512),
            "provider": "CTransformers",
            "local": True,
            "capabilities": ["text-generation", "chat", "streaming"]
        }
    
    def _list_models(self) -> Dict[str, Any]:
        """List available GGML models in common directories"""
        model_dirs = [
            os.path.expanduser("~/models"),
            os.path.expanduser("~/.cache/ctransformers"),
            "./models",
            "../models"
        ]
        
        found_models = []
        
        for model_dir in model_dirs:
            if os.path.exists(model_dir):
                for file in os.listdir(model_dir):
                    if file.endswith(('.ggml', '.gguf', '.bin')):
                        file_path = os.path.join(model_dir, file)
                        found_models.append({
                            "path": file_path,
                            "name": file,
                            "size": os.path.getsize(file_path) if os.path.isfile(file_path) else 0
                        })
        
        return {
            "models": found_models,
            "searched_directories": model_dirs
        }
    
    def load_model(self, model_file: str, model_type: str = None, **kwargs) -> Dict[str, Any]:
        """Load a new model"""
        try:
            from ctransformers import AutoModelForCausalLM
            
            if not os.path.exists(model_file):
                return {"error": f"Model file not found: {model_file}"}
            
            # Update settings
            self.settings["model_file"] = model_file
            if model_type:
                self.settings["model_type"] = model_type
            self.settings.update(kwargs)
            
            # Load the model
            self.model = AutoModelForCausalLM.from_pretrained(
                model_file_or_path=model_file,
                model_type=self.settings.get("model_type", "llama"),
                gpu_layers=self.settings.get("gpu_layers", 0),
                batch_size=self.settings.get("batch_size", 512),
                context_length=self.settings.get("context_length", 2048)
            )
            
            self.model_path = model_file
            self._initialized = True
            
            return {
                "success": True,
                "model": model_file,
                "model_type": self.settings.get("model_type"),
                "message": "Model loaded successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            return {"error": str(e)}
    
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
    
    def cleanup(self):
        """Cleanup resources"""
        self.model = None
        self.model_path = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = CTransformersPlugin
PLUGIN_NAME = "ctransformers"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Local GGML model support using CTransformers"
PLUGIN_ACTIONS = [
    "text_generation", "chat", "stream_text", "get_model_info", "list_models"
]