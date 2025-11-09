"""
Together AI Model Provider Plugin
Supports RedPajama, Falcon, MPT, Llama-2, Mistral models
"""

from typing import Dict, Any, Optional, List
import os


class TogetherPlugin:
    """Plugin for Together AI models"""
    
    name = "together"
    version = "1.0.0"
    description = "Integration with Together AI (RedPajama, Falcon, MPT, Llama, Mistral)"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.base_url = "https://api.together.xyz/v1"
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Together AI plugin"""
        try:
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("TOGETHER_API_KEY")
            )
            
            if not self.api_key:
                return False
                
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing Together AI plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Together AI action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}
        
        try:
            if action == "chat":
                return self._chat(params)
            elif action == "complete":
                return self._complete(params)
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
        import requests
        
        messages = params.get("messages", [])
        model = params.get("model", "mistralai/Mixtral-8x7B-Instruct-v0.1")
        # Popular models:
        # - mistralai/Mixtral-8x7B-Instruct-v0.1
        # - togethercomputer/llama-2-7b-chat
        # - togethercomputer/llama-2-70b-chat
        # - togethercomputer/CodeLlama-34b-Instruct
        # - teknium/OpenHermes-2p5-Mistral-7B
        
        max_tokens = params.get("max_tokens", 512)
        temperature = params.get("temperature", 0.7)
        top_p = params.get("top_p", 0.7)
        top_k = params.get("top_k", 50)
        repetition_penalty = params.get("repetition_penalty", 1)
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "repetition_penalty": repetition_penalty
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "response": data["choices"][0]["message"]["content"],
            "model": data["model"],
            "finish_reason": data["choices"][0]["finish_reason"],
            "usage": data.get("usage", {})
        }
    
    def _complete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Text completion"""
        import requests
        
        prompt = params.get("prompt", "")
        model = params.get("model", "togethercomputer/RedPajama-INCITE-7B-Instruct")
        # Popular completion models:
        # - togethercomputer/RedPajama-INCITE-7B-Instruct
        # - togethercomputer/RedPajama-INCITE-Base-3B-v1
        # - EleutherAI/pythia-12b-v0
        # - togethercomputer/GPT-NeoXT-Chat-Base-20B
        
        max_tokens = params.get("max_tokens", 512)
        temperature = params.get("temperature", 0.7)
        top_p = params.get("top_p", 0.7)
        top_k = params.get("top_k", 50)
        
        response = requests.post(
            f"{self.base_url}/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "text": data["choices"][0]["text"],
            "model": data["model"],
            "finish_reason": data["choices"][0]["finish_reason"],
            "usage": data.get("usage", {})
        }
    
    def _embed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate embeddings"""
        import requests
        
        input_texts = params.get("input", [])
        if isinstance(input_texts, str):
            input_texts = [input_texts]
        
        model = params.get("model", "togethercomputer/m2-bert-80M-8k-retrieval")
        # Embedding models:
        # - togethercomputer/m2-bert-80M-8k-retrieval
        # - togethercomputer/m2-bert-80M-32k-retrieval
        # - WhereIsAI/UAE-Large-V1
        # - BAAI/bge-large-en-v1.5
        
        response = requests.post(
            f"{self.base_url}/embeddings",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "input": input_texts
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "embeddings": [item["embedding"] for item in data["data"]],
            "model": data["model"],
            "count": len(data["data"]),
            "usage": data.get("usage", {})
        }
    
    def _list_models(self) -> Dict[str, Any]:
        """List available models"""
        import requests
        
        response = requests.get(
            f"{self.base_url}/models",
            headers={
                "Authorization": f"Bearer {self.api_key}"
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "models": [
                {
                    "id": model["id"],
                    "created": model.get("created"),
                    "type": model.get("type")
                }
                for model in data.get("data", [])
            ],
            "count": len(data.get("data", []))
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = TogetherPlugin
PLUGIN_NAME = "together"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Together AI models"
PLUGIN_ACTIONS = ["chat", "complete", "embed", "list_models"]
