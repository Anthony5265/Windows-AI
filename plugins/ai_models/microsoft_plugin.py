"""
Microsoft AI Model Provider Plugin
Supports Azure OpenAI, Bing Chat, Copilot
"""

from typing import Dict, Any, Optional, List
import os


class MicrosoftPlugin:
    """Plugin for Microsoft AI models"""
    
    name = "microsoft"
    version = "1.0.0"
    description = "Integration with Microsoft AI (Azure OpenAI, Bing Chat, Copilot)"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.endpoint: Optional[str] = None
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Microsoft AI plugin"""
        try:
            from openai import AzureOpenAI
            
            # Get credentials from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("AZURE_OPENAI_API_KEY")
            )
            
            self.endpoint = (
                config.get("endpoint") if config 
                else os.getenv("AZURE_OPENAI_ENDPOINT")
            )
            
            if not self.api_key or not self.endpoint:
                return False
                
            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version="2024-02-01",
                azure_endpoint=self.endpoint
            )
            self._initialized = True
            return True
            
        except ImportError:
            print("openai package not installed. Install with: pip install openai")
            return False
        except Exception as e:
            print(f"Error initializing Microsoft AI plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Microsoft AI action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}
            
        try:
            if action == "chat":
                return self._chat(params)
            elif action == "completion":
                return self._completion(params)
            elif action == "embeddings":
                return self._get_embeddings(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion with Azure OpenAI"""
        deployment = params.get("deployment", "gpt-4")
        messages = params.get("messages", [])
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 2000)
        
        response = self.client.chat.completions.create(
            model=deployment,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "success": True,
            "response": response.choices[0].message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    def _completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text completion"""
        deployment = params.get("deployment", "gpt-35-turbo-instruct")
        prompt = params.get("prompt", "")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 1000)
        
        response = self.client.completions.create(
            model=deployment,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "success": True,
            "response": response.choices[0].text,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    def _get_embeddings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get text embeddings"""
        text = params.get("text", "")
        deployment = params.get("deployment", "text-embedding-ada-002")
        
        response = self.client.embeddings.create(
            input=text,
            model=deployment
        )
        
        return {
            "success": True,
            "embedding": response.data[0].embedding,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
