"""
OpenAI Model Provider Plugin
Supports GPT-3.5, GPT-4, GPT-4-Turbo, GPT-4V, DALL-E 3
"""

from typing import Dict, Any, Optional, List
import os


class OpenAIPlugin:
    """Plugin for OpenAI models"""
    
    name = "openai"
    version = "1.0.0"
    description = "Integration with OpenAI models (GPT-3.5, GPT-4, GPT-4-Turbo, GPT-4V, DALL-E 3)"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the OpenAI plugin"""
        try:
            import openai
            
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("OPENAI_API_KEY")
            )
            
            if not self.api_key:
                return False
                
            openai.api_key = self.api_key
            self.client = openai
            self._initialized = True
            return True
            
        except ImportError:
            print("openai package not installed. Install with: pip install openai")
            return False
        except Exception as e:
            print(f"Error initializing OpenAI plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an OpenAI action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}
            
        try:
            if action == "chat":
                return self._chat(params)
            elif action == "completion":
                return self._completion(params)
            elif action == "image":
                return self._generate_image(params)
            elif action == "vision":
                return self._vision_analysis(params)
            elif action == "embeddings":
                return self._get_embeddings(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion"""
        model = params.get("model", "gpt-4")
        messages = params.get("messages", [])
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 2000)
        
        response = self.client.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "success": True,
            "response": response.choices[0].message.content,
            "usage": response.usage
        }
    
    def _completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text completion"""
        model = params.get("model", "gpt-3.5-turbo-instruct")
        prompt = params.get("prompt", "")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 1000)
        
        response = self.client.Completion.create(
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "success": True,
            "response": response.choices[0].text,
            "usage": response.usage
        }
    
    def _generate_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate image with DALL-E"""
        prompt = params.get("prompt", "")
        model = params.get("model", "dall-e-3")
        size = params.get("size", "1024x1024")
        quality = params.get("quality", "standard")
        n = params.get("n", 1)
        
        response = self.client.Image.create(
            model=model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=n
        )
        
        return {
            "success": True,
            "images": [img.url for img in response.data]
        }
    
    def _vision_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze image with GPT-4V"""
        messages = params.get("messages", [])
        model = params.get("model", "gpt-4-vision-preview")
        max_tokens = params.get("max_tokens", 500)
        
        response = self.client.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens
        )
        
        return {
            "success": True,
            "response": response.choices[0].message.content,
            "usage": response.usage
        }
    
    def _get_embeddings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get text embeddings"""
        text = params.get("text", "")
        model = params.get("model", "text-embedding-ada-002")
        
        response = self.client.Embedding.create(
            input=text,
            model=model
        )
        
        return {
            "success": True,
            "embedding": response.data[0].embedding,
            "usage": response.usage
        }
    
    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
