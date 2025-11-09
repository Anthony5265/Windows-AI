"""
Mistral AI Model Provider Plugin
Supports Mistral 7B, Mixtral 8x7B, Mistral Medium, Mistral Large
"""

from typing import Dict, Any, Optional, List
import os


class MistralPlugin:
    """Plugin for Mistral AI models"""
    
    name = "mistral"
    version = "1.0.0"
    description = "Integration with Mistral AI models"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Mistral plugin"""
        try:
            from mistralai.client import MistralClient
            
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("MISTRAL_API_KEY")
            )
            
            if not self.api_key:
                return False
                
            self.client = MistralClient(api_key=self.api_key)
            self._initialized = True
            return True
            
        except ImportError:
            print("mistralai package not installed. Install with: pip install mistralai")
            return False
        except Exception as e:
            print(f"Error initializing Mistral plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Mistral action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}
        
        try:
            if action == "chat":
                return self._chat(params)
            elif action == "stream_chat":
                return self._stream_chat(params)
            elif action == "embed":
                return self._embed(params)
            elif action == "list_models":
                return self._list_models()
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion"""
        from mistralai.models.chat_completion import ChatMessage
        
        messages = params.get("messages", [])
        model = params.get("model", "mistral-medium")  # mistral-tiny, small, medium, large
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", None)
        top_p = params.get("top_p", 1.0)
        
        # Convert to Mistral format
        chat_messages = [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in messages
        ]
        
        response = self.client.chat(
            model=model,
            messages=chat_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )
        
        return {
            "response": response.choices[0].message.content,
            "model": response.model,
            "finish_reason": response.choices[0].finish_reason,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    def _stream_chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stream chat completion"""
        from mistralai.models.chat_completion import ChatMessage
        
        messages = params.get("messages", [])
        model = params.get("model", "mistral-medium")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", None)
        
        # Convert to Mistral format
        chat_messages = [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in messages
        ]
        
        # Collect streamed response
        full_response = ""
        for chunk in self.client.chat_stream(
            model=model,
            messages=chat_messages,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
        
        return {
            "response": full_response,
            "model": model,
            "streamed": True
        }
    
    def _embed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate embeddings"""
        input_texts = params.get("input", [])
        if isinstance(input_texts, str):
            input_texts = [input_texts]
        
        model = params.get("model", "mistral-embed")
        
        response = self.client.embeddings(
            model=model,
            input=input_texts
        )
        
        return {
            "embeddings": [item.embedding for item in response.data],
            "model": response.model,
            "count": len(response.data),
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    def _list_models(self) -> Dict[str, Any]:
        """List available models"""
        response = self.client.list_models()
        
        return {
            "models": [
                {
                    "id": model.id,
                    "created": model.created,
                    "owned_by": model.owned_by
                }
                for model in response.data
            ],
            "count": len(response.data)
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.client = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = MistralPlugin
PLUGIN_NAME = "mistral"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Mistral AI models"
PLUGIN_ACTIONS = ["chat", "stream_chat", "embed", "list_models"]
