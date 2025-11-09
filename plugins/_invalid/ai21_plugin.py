"""
AI21 Labs Model Provider Plugin
Supports Jurassic-2, J2-Ultra, J2-Mid models
"""

from typing import Dict, Any, Optional
import os


class AI21Plugin:
    """Plugin for AI21 Labs models"""
    
    name = "ai21"
    version = "1.0.0"
    description = "Integration with AI21 Labs (Jurassic-2, Contextual Answers)"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.base_url = "https://api.ai21.com/studio/v1"
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the AI21 plugin"""
        try:
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("AI21_API_KEY")
            )
            
            if not self.api_key:
                return False
                
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing AI21 plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an AI21 action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}
        
        try:
            if action == "complete":
                return self._complete(params)
            elif action == "chat":
                return self._chat(params)
            elif action == "paraphrase":
                return self._paraphrase(params)
            elif action == "summarize":
                return self._summarize(params)
            elif action == "improvements":
                return self._improvements(params)
            elif action == "contextual_answers":
                return self._contextual_answers(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _complete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Text completion using Jurassic models"""
        import requests
        
        prompt = params.get("prompt", "")
        model = params.get("model", "j2-mid")  # j2-ultra, j2-mid, j2-light
        max_tokens = params.get("max_tokens", 200)
        temperature = params.get("temperature", 0.7)
        top_p = params.get("top_p", 1.0)
        
        response = requests.post(
            f"{self.base_url}/{model}/complete",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": prompt,
                "maxTokens": max_tokens,
                "temperature": temperature,
                "topP": top_p
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "text": data["completions"][0]["data"]["text"],
            "model": model,
            "tokens": data["completions"][0]["data"].get("tokens", [])
        }
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion"""
        import requests
        
        messages = params.get("messages", [])
        model = params.get("model", "j2-ultra")
        max_tokens = params.get("max_tokens", 200)
        temperature = params.get("temperature", 0.7)
        
        # Convert messages to AI21 format
        system = ""
        formatted_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                formatted_messages.append({
                    "role": msg["role"],
                    "text": msg["content"]
                })
        
        payload = {
            "messages": formatted_messages,
            "maxTokens": max_tokens,
            "temperature": temperature
        }
        
        if system:
            payload["system"] = system
        
        response = requests.post(
            f"{self.base_url}/{model}/chat",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "response": data["outputs"][0]["text"],
            "model": model,
            "role": data["outputs"][0]["role"]
        }
    
    def _paraphrase(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Paraphrase text"""
        import requests
        
        text = params.get("text", "")
        style = params.get("style", "general")  # general, formal, casual
        
        response = requests.post(
            f"{self.base_url}/paraphrase",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "text": text,
                "style": style
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "suggestions": data.get("suggestions", []),
            "count": len(data.get("suggestions", []))
        }
    
    def _summarize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize text"""
        import requests
        
        source = params.get("text", "")
        source_type = params.get("source_type", "TEXT")  # TEXT or URL
        
        response = requests.post(
            f"{self.base_url}/summarize",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "source": source,
                "sourceType": source_type
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "summary": data.get("summary", ""),
            "id": data.get("id")
        }
    
    def _improvements(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get text improvements"""
        import requests
        
        text = params.get("text", "")
        types = params.get("types", ["fluency", "vocabulary", "clarity", "conciseness"])
        
        response = requests.post(
            f"{self.base_url}/improvements",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "text": text,
                "types": types
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "improvements": data.get("improvements", []),
            "count": len(data.get("improvements", []))
        }
    
    def _contextual_answers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get contextual answers"""
        import requests
        
        context = params.get("context", "")
        question = params.get("question", "")
        
        response = requests.post(
            f"{self.base_url}/answer",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "context": context,
                "question": question
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "answer": data.get("answer", ""),
            "id": data.get("id")
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = AI21Plugin
PLUGIN_NAME = "ai21"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with AI21 Labs models"
PLUGIN_ACTIONS = ["complete", "chat", "paraphrase", "summarize", "improvements", "contextual_answers"]
