"""
KoboldAI Plugin for Windows AI
Supports story generation and chat functionality
"""

import json
import requests
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

class KoboldAIPlugin:
    """KoboldAI integration plugin"""
    
    def __init__(self):
        self.name = "koboldai"
        self.version = "1.0.0"
        self.description = "KoboldAI local model integration for story generation and chat"
        self.logger = logging.getLogger(__name__)
        
        # Default KoboldAI settings
        self.default_settings = {
            "api_url": "http://localhost:5000",
            "max_tokens": 256,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 100,
            "repetition_penalty": 1.1,
            "story_mode": True,
            "chat_mode": False
        }
        
        self.settings = self.default_settings.copy()
        self.session = requests.Session()
        
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin with configuration"""
        try:
            self.settings.update(config.get("koboldai", {}))
            
            # Test connection to KoboldAI
            if self._test_connection():
                self.logger.info("KoboldAI plugin initialized successfully")
                return True
            else:
                self.logger.warning("Could not connect to KoboldAI server")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize KoboldAI plugin: {e}")
            return False
    
    def _test_connection(self) -> bool:
        """Test connection to KoboldAI server"""
        try:
            response = self.session.get(f"{self.settings['api_url']}/api/v1/model", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    async def generate_story(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate story content using KoboldAI"""
        try:
            # Merge kwargs with settings
            params = {
                "prompt": prompt,
                "max_length": kwargs.get("max_tokens", self.settings["max_tokens"]),
                "temperature": kwargs.get("temperature", self.settings["temperature"]),
                "top_p": kwargs.get("top_p", self.settings["top_p"]),
                "top_k": kwargs.get("top_k", self.settings["top_k"]),
                "rep_pen": kwargs.get("repetition_penalty", self.settings["repetition_penalty"]),
                "use_story": kwargs.get("use_story", self.settings["story_mode"]),
                "use_memory": False,
                "use_authors_note": False,
                "use_world_info": False,
                "stop_sequence": ["\n\n", "###", "---"]
            }
            
            response = self.session.post(
                f"{self.settings['api_url']}/api/v1/generate",
                json=params,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "text": result.get("results", [{}])[0].get("text", ""),
                    "tokens_used": len(result.get("results", [{}])[0].get("text", "").split()),
                    "model": "koboldai_local"
                }
            else:
                return {
                    "success": False,
                    "error": f"KoboldAI API error: {response.status_code}"
                }
                
        except Exception as e:
            self.logger.error(f"Story generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Chat with KoboldAI model"""
        try:
            # Format messages for KoboldAI
            if self.settings["chat_mode"]:
                # Chat mode format
                formatted_prompt = self._format_chat_messages(messages)
            else:
                # Simple prompt format
                formatted_prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
                formatted_prompt += "\nassistant:"
            
            params = {
                "prompt": formatted_prompt,
                "max_length": kwargs.get("max_tokens", self.settings["max_tokens"]),
                "temperature": kwargs.get("temperature", self.settings["temperature"]),
                "top_p": kwargs.get("top_p", self.settings["top_p"]),
                "top_k": kwargs.get("top_k", self.settings["top_k"]),
                "rep_pen": kwargs.get("repetition_penalty", self.settings["repetition_penalty"]),
                "use_story": False,
                "use_memory": False,
                "use_authors_note": False,
                "use_world_info": False,
                "stop_sequence": ["\nuser:", "\nhuman:", "\nassistant:", "\n\n"]
            }
            
            response = self.session.post(
                f"{self.settings['api_url']}/api/v1/generate",
                json=params,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("results", [{}])[0].get("text", "").strip()
                
                return {
                    "success": True,
                    "response": generated_text,
                    "messages": messages + [{"role": "assistant", "content": generated_text}],
                    "tokens_used": len(generated_text.split()),
                    "model": "koboldai_local"
                }
            else:
                return {
                    "success": False,
                    "error": f"KoboldAI API error: {response.status_code}"
                }
                
        except Exception as e:
            self.logger.error(f"Chat failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_chat_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for chat mode"""
        chat_formats = {
            "system": "System: {content}\n\n",
            "user": "User: {content}\n",
            "assistant": "Assistant: {content}\n"
        }
        
        formatted = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted += chat_formats.get(role, f"{role}: {content}\n")
        
        formatted += "Assistant:"
        return formatted
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        try:
            response = self.session.get(f"{self.settings['api_url']}/api/v1/model", timeout=5)
            if response.status_code == 200:
                model_info = response.json()
                return {
                    "success": True,
                    "model_name": model_info.get("result", "Unknown"),
                    "provider": "KoboldAI",
                    "local": True,
                    "capabilities": ["text-generation", "story", "chat"]
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
        if self.session:
            self.session.close()

# Plugin registration
plugin = KoboldAIPlugin()

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
        "capabilities": ["story_generation", "chat"],
        "settings": plugin.default_settings
    }