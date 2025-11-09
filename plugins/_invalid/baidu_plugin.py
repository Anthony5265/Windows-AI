"""
Baidu ERNIE Bot Model Provider Plugin
Supports ERNIE models via Qianfan API
"""

from typing import Dict, Any, Optional, List
import os


class BaiduPlugin:
    """Plugin for Baidu ERNIE models"""
    
    name = "baidu"
    version = "1.0.0"
    description = "Integration with Baidu ERNIE models"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Baidu plugin"""
        try:
            from openai import OpenAI
            
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("BAIDU_API_KEY")
            )
            
            if not self.api_key:
                return False
                
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://qianfan.baidubce.com/v2"
            )
            self._initialized = True
            return True
            
        except ImportError:
            print("openai package not installed. Install with: pip install openai")
            return False
        except Exception as e:
            print(f"Error initializing Baidu plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Baidu action"""
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
        messages = params.get("messages", [])
        model = params.get("model", "ernie-4.5-turbo-128k")  # Default ERNIE model
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", None)
        top_p = params.get("top_p", 1.0)
        
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
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
        messages = params.get("messages", [])
        model = params.get("model", "ernie-4.5-turbo-128k")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", None)
        
        # Collect streamed response
        full_response = ""
        for chunk in self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
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
        
        model = params.get("model", "embedding-v1")
        
        response = self.client.embeddings.create(
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
        # Return known ERNIE models based on Baidu documentation
        models = [
            # ERNIE Flagship models
            {"id": "ernie-4.5-turbo-128k", "owned_by": "baidu"},
            {"id": "ernie-4.5-turbo-32k", "owned_by": "baidu"},
            {"id": "ernie-4.5-turbo-latest", "owned_by": "baidu"},
            {"id": "ernie-4.5-turbo-vl", "owned_by": "baidu"},
            {"id": "ernie-4.5-turbo-vl-32k", "owned_by": "baidu"},
            {"id": "ernie-4.5-turbo-vl-latest", "owned_by": "baidu"},
            
            # ERNIE Mainstream models
            {"id": "ernie-speed-128k", "owned_by": "baidu"},
            {"id": "ernie-speed-8k", "owned_by": "baidu"},
            {"id": "ernie-speed-pro-128k", "owned_by": "baidu"},
            {"id": "ernie-lite-8k", "owned_by": "baidu"},
            {"id": "ernie-lite-pro-128k", "owned_by": "baidu"},
            
            # ERNIE Light models
            {"id": "ernie-tiny-8k", "owned_by": "baidu"},
            
            # ERNIE Vertical models
            {"id": "ernie-char-8k", "owned_by": "baidu"},
            {"id": "ernie-char-fiction-8k", "owned_by": "baidu"},
            {"id": "ernie-novel-8k", "owned_by": "baidu"},
            
            # ERNIE Open source models
            {"id": "ernie-4.5-8k-preview", "owned_by": "baidu"},
            {"id": "ernie-4.5-0.3b", "owned_by": "baidu"},
            {"id": "ernie-4.5-21b-a3b", "owned_by": "baidu"},
            {"id": "ernie-4.5-vl-28b-a3b", "owned_by": "baidu"},
            
            # Qianfan models
            {"id": "qianfan-chinese-llama-2-13b", "owned_by": "baidu"},
            
            # Embedding models
            {"id": "embedding-v1", "owned_by": "baidu"},
            {"id": "bge-large-zh", "owned_by": "baidu"},
            {"id": "bge-large-en", "owned_by": "baidu"},
        ]
        
        return {
            "models": models,
            "count": len(models)
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.client = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = BaiduPlugin
PLUGIN_NAME = "baidu"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Baidu ERNIE models"
PLUGIN_ACTIONS = ["chat", "stream_chat", "embed", "list_models"]