"""
Cohere AI Model Provider Plugin
Supports Command, Command-Light, Embed, and Rerank models
"""

from typing import Dict, Any, Optional, List
import os


class CoherePlugin:
    """Plugin for Cohere AI models"""
    
    name = "cohere"
    version = "1.0.0"
    description = "Integration with Cohere AI models (Command, Embed, Rerank)"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Cohere plugin"""
        try:
            import cohere
            
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("COHERE_API_KEY")
            )
            
            if not self.api_key:
                return False
                
            self.client = cohere.Client(self.api_key)
            self._initialized = True
            return True
            
        except ImportError:
            print("cohere package not installed. Install with: pip install cohere")
            return False
        except Exception as e:
            print(f"Error initializing Cohere plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Cohere action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}
        
        try:
            if action == "chat":
                return self._chat(params)
            elif action == "embed":
                return self._embed(params)
            elif action == "rerank":
                return self._rerank(params)
            elif action == "classify":
                return self._classify(params)
            elif action == "summarize":
                return self._summarize(params)
            elif action == "generate":
                return self._generate(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion using Command models"""
        message = params.get("message", "")
        model = params.get("model", "command")  # command, command-light, command-nightly
        chat_history = params.get("chat_history", [])
        temperature = params.get("temperature", 0.7)
        
        response = self.client.chat(
            message=message,
            model=model,
            chat_history=chat_history,
            temperature=temperature,
        )
        
        return {
            "response": response.text,
            "model": model,
            "conversation_id": response.conversation_id,
            "citations": response.citations if hasattr(response, 'citations') else []
        }
    
    def _embed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate embeddings"""
        texts = params.get("texts", [])
        if isinstance(texts, str):
            texts = [texts]
            
        model = params.get("model", "embed-english-v3.0")  # or embed-multilingual-v3.0
        input_type = params.get("input_type", "search_document")  # search_query, classification, clustering
        
        response = self.client.embed(
            texts=texts,
            model=model,
            input_type=input_type
        )
        
        return {
            "embeddings": response.embeddings,
            "model": model,
            "count": len(response.embeddings)
        }
    
    def _rerank(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Rerank documents"""
        query = params.get("query", "")
        documents = params.get("documents", [])
        top_n = params.get("top_n", 3)
        model = params.get("model", "rerank-english-v2.0")  # or rerank-multilingual-v2.0
        
        response = self.client.rerank(
            query=query,
            documents=documents,
            top_n=top_n,
            model=model
        )
        
        return {
            "results": [
                {
                    "index": result.index,
                    "relevance_score": result.relevance_score,
                    "document": documents[result.index]
                }
                for result in response.results
            ],
            "model": model
        }
    
    def _classify(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Classify text"""
        inputs = params.get("inputs", [])
        if isinstance(inputs, str):
            inputs = [inputs]
            
        examples = params.get("examples", [])
        model = params.get("model", "embed-english-v2.0")
        
        response = self.client.classify(
            inputs=inputs,
            examples=examples,
            model=model
        )
        
        return {
            "classifications": [
                {
                    "input": c.input,
                    "prediction": c.prediction,
                    "confidence": c.confidence
                }
                for c in response.classifications
            ]
        }
    
    def _summarize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize text"""
        text = params.get("text", "")
        length = params.get("length", "medium")  # short, medium, long
        format_type = params.get("format", "paragraph")  # paragraph, bullets
        model = params.get("model", "summarize-xlarge")
        extractiveness = params.get("extractiveness", "medium")  # low, medium, high
        temperature = params.get("temperature", 0.3)
        
        response = self.client.summarize(
            text=text,
            length=length,
            format=format_type,
            model=model,
            extractiveness=extractiveness,
            temperature=temperature
        )
        
        return {
            "summary": response.summary,
            "model": model
        }
    
    def _generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text"""
        prompt = params.get("prompt", "")
        model = params.get("model", "command")
        max_tokens = params.get("max_tokens", 300)
        temperature = params.get("temperature", 0.75)
        k = params.get("k", 0)  # Top-k sampling
        p = params.get("p", 0.75)  # Top-p sampling
        
        response = self.client.generate(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            k=k,
            p=p
        )
        
        return {
            "text": response.generations[0].text,
            "model": model,
            "likelihood": response.generations[0].likelihood if hasattr(response.generations[0], 'likelihood') else None
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.client = None
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = CoherePlugin
PLUGIN_NAME = "cohere"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Cohere AI models"
PLUGIN_ACTIONS = ["chat", "embed", "rerank", "classify", "summarize", "generate"]
