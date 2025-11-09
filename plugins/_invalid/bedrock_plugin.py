"""
Amazon Bedrock AI Model Provider Plugin
Supports Claude, Titan, and Jurassic models for chat, completion, and embedding
"""

from typing import Dict, Any, Optional, List
import os
import json


class BedrockPlugin:
    """Plugin for Amazon Bedrock AI models"""
    
    name = "bedrock"
    version = "1.0.0"
    description = "Integration with Amazon Bedrock models (Claude, Titan, Jurassic)"
    author = "Windows AI Team"
    
    def __init__(self):
        self.client = None
        self.runtime_client = None
        self._initialized = False
        self.region = None
        
        # Model mappings for different providers
        self.claude_models = {
            "claude-3-opus": "anthropic.claude-3-opus-20240229-v1:0",
            "claude-3-sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
            "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
            "claude-2.1": "anthropic.claude-v2:1",
            "claude-2.0": "anthropic.claude-v2",
            "claude-instant-1.2": "anthropic.claude-instant-v1"
        }
        
        self.titan_models = {
            "titan-text-express": "amazon.titan-text-express-v1",
            "titan-text-lite": "amazon.titan-text-lite-v1",
            "titan-embed-text": "amazon.titan-embed-text-v1",
            "titan-embed-multilingual": "amazon.titan-embed-text-v1"  # Same model, multilingual support
        }
        
        self.jurassic_models = {
            "jurassic-2-mid": "ai21.j2-mid-v1",
            "jurassic-2-ultra": "ai21.j2-ultra-v1"
        }
        
        self.embedding_models = {
            "titan-embed": "amazon.titan-embed-text-v1",
            "cohere-embed-english": "cohere.embed-english-v3",
            "cohere-embed-multilingual": "cohere.embed-multilingual-v3"
        }
    
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Bedrock plugin"""
        try:
            import boto3
            
            # Get configuration
            self.region = (
                config.get("region") if config 
                else os.getenv("AWS_REGION", "us-east-1")
            )
            
            # Initialize boto3 clients
            self.client = boto3.client('bedrock', region_name=self.region)
            self.runtime_client = boto3.client('bedrock-runtime', region_name=self.region)
            
            # Test connection by listing available models
            try:
                self.client.list_foundation_models()
            except Exception as e:
                print(f"Warning: Could not verify Bedrock access: {e}")
            
            self._initialized = True
            return True
            
        except ImportError:
            print("boto3 package not installed. Install with: pip install boto3")
            return False
        except Exception as e:
            print(f"Error initializing Bedrock plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Bedrock action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please ensure AWS credentials are configured."}
        
        try:
            if action == "chat":
                return self._chat(params)
            elif action == "complete":
                return self._complete(params)
            elif action == "embed":
                return self._embed(params)
            elif action == "list_models":
                return self._list_models(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion using Claude models"""
        message = params.get("message", "")
        model = params.get("model", "claude-3-sonnet")
        system_prompt = params.get("system_prompt", "")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 4000)
        top_p = params.get("top_p", 0.999)
        top_k = params.get("top_k", 250)
        
        # Get the actual model ID
        model_id = self._get_model_id(model)
        if not model_id:
            return {"error": f"Unknown model: {model}"}
        
        # Prepare request body based on model provider
        if model.startswith("claude"):
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            }
            
            if system_prompt:
                request_body["system"] = system_prompt
                
        elif model.startswith("titan"):
            request_body = {
                "inputText": message,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": temperature,
                    "topP": top_p
                }
            }
            
        elif model.startswith("jurassic"):
            request_body = {
                "prompt": message,
                "maxTokens": max_tokens,
                "temperature": temperature,
                "topP": top_p
            }
            
        else:
            return {"error": f"Chat not supported for model: {model}"}
        
        # Invoke the model
        response = self.runtime_client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        # Extract response text based on model provider
        if model.startswith("claude"):
            response_text = response_body.get('content', [{}])[0].get('text', '')
        elif model.startswith("titan"):
            response_text = response_body.get('results', [{}])[0].get('outputText', '')
        elif model.startswith("jurassic"):
            response_text = response_body.get('completions', [{}])[0].get('data', {}).get('text', '')
        else:
            response_text = str(response_body)
        
        return {
            "response": response_text,
            "model": model,
            "model_id": model_id,
            "usage": response_body.get('usage', {}),
            "finish_reason": response_body.get('stop_reason', 'unknown')
        }
    
    def _complete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Text completion using various models"""
        prompt = params.get("prompt", "")
        model = params.get("model", "titan-text-express")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 4000)
        top_p = params.get("top_p", 0.999)
        
        # Get the actual model ID
        model_id = self._get_model_id(model)
        if not model_id:
            return {"error": f"Unknown model: {model}"}
        
        # Prepare request body based on model provider
        if model.startswith("claude"):
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
        elif model.startswith("titan"):
            request_body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": temperature,
                    "topP": top_p
                }
            }
            
        elif model.startswith("jurassic"):
            request_body = {
                "prompt": prompt,
                "maxTokens": max_tokens,
                "temperature": temperature,
                "topP": top_p
            }
            
        else:
            return {"error": f"Completion not supported for model: {model}"}
        
        # Invoke the model
        response = self.runtime_client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        # Extract completion text based on model provider
        if model.startswith("claude"):
            completion_text = response_body.get('content', [{}])[0].get('text', '')
        elif model.startswith("titan"):
            completion_text = response_body.get('results', [{}])[0].get('outputText', '')
        elif model.startswith("jurassic"):
            completion_text = response_body.get('completions', [{}])[0].get('data', {}).get('text', '')
        else:
            completion_text = str(response_body)
        
        return {
            "completion": completion_text,
            "model": model,
            "model_id": model_id,
            "usage": response_body.get('usage', {}),
            "finish_reason": response_body.get('stop_reason', 'unknown')
        }
    
    def _embed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate embeddings using embedding models"""
        texts = params.get("texts", [])
        if isinstance(texts, str):
            texts = [texts]
        
        model = params.get("model", "titan-embed")
        
        # Get the actual model ID
        model_id = self._get_model_id(model, embedding=True)
        if not model_id:
            return {"error": f"Unknown embedding model: {model}"}
        
        embeddings = []
        
        # Process each text (batch processing varies by model)
        for text in texts:
            if model.startswith("titan"):
                request_body = {
                    "inputText": text
                }
            elif model.startswith("cohere"):
                request_body = {
                    "texts": [text],
                    "input_type": "search_document"
                }
            else:
                return {"error": f"Embeddings not supported for model: {model}"}
            
            # Invoke the model
            response = self.runtime_client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Extract embedding based on model provider
            if model.startswith("titan"):
                embedding = response_body.get('embedding', [])
            elif model.startswith("cohere"):
                embedding = response_body.get('embeddings', [[]])[0]
            else:
                embedding = []
            
            embeddings.append(embedding)
        
        return {
            "embeddings": embeddings,
            "model": model,
            "model_id": model_id,
            "count": len(embeddings),
            "dimension": len(embeddings[0]) if embeddings else 0
        }
    
    def _list_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available foundation models"""
        try:
            response = self.client.list_foundation_models()
            
            models = []
            for model in response.get('modelSummaries', []):
                models.append({
                    "model_id": model.get('modelId'),
                    "name": model.get('modelName'),
                    "provider": model.get('providerName'),
                    "input_modalities": model.get('inputModalities', []),
                    "output_modalities": model.get('outputModalities', []),
                    "lifecycle": model.get('modelLifecycle', {}).get('status')
                })
            
            return {
                "models": models,
                "count": len(models)
            }
            
        except Exception as e:
            return {"error": f"Failed to list models: {str(e)}"}
    
    def _get_model_id(self, model_name: str, embedding: bool = False) -> Optional[str]:
        """Get the full model ID from the short name"""
        if embedding:
            return self.embedding_models.get(model_name)
        
        # Check all model mappings
        if model_name in self.claude_models:
            return self.claude_models[model_name]
        elif model_name in self.titan_models:
            return self.titan_models[model_name]
        elif model_name in self.jurassic_models:
            return self.jurassic_models[model_name]
        
        # If it's already a full model ID, return it
        if "." in model_name:
            return model_name
        
        return None
    
    def cleanup(self):
        """Cleanup resources"""
        self.client = None
        self.runtime_client = None
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = BedrockPlugin
PLUGIN_NAME = "bedrock"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Amazon Bedrock models"
PLUGIN_ACTIONS = ["chat", "complete", "embed", "list_models"]