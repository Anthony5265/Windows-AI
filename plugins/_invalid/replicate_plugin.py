"""
Replicate Model Provider Plugin
Supports 100+ models including Llama, Stable Diffusion, SDXL, and more
"""

from typing import Dict, Any, Optional, List
import os


class ReplicatePlugin:
    """Plugin for Replicate models"""
    
    name = "replicate"
    version = "1.0.0"
    description = "Integration with Replicate (100+ AI models)"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Replicate plugin"""
        try:
            import replicate
            
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("REPLICATE_API_TOKEN")
            )
            
            if not self.api_key:
                return False
            
            # Set API token for replicate library
            os.environ["REPLICATE_API_TOKEN"] = self.api_key
            self.client = replicate
            self._initialized = True
            return True
            
        except ImportError:
            print("replicate package not installed. Install with: pip install replicate")
            return False
        except Exception as e:
            print(f"Error initializing Replicate plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Replicate action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}
        
        try:
            if action == "run":
                return self._run(params)
            elif action == "predict":
                return self._predict(params)
            elif action == "list_models":
                return self._list_models(params)
            elif action == "get_model":
                return self._get_model(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a model (simplified interface)"""
        model_version = params.get("model")  # e.g., "meta/llama-2-70b-chat"
        input_data = params.get("input", {})
        
        if not model_version:
            return {"error": "model parameter required"}
        
        output = self.client.run(model_version, input=input_data)
        
        return {
            "output": output,
            "model": model_version
        }
    
    def _predict(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a prediction (more control)"""
        model_version = params.get("model")
        input_data = params.get("input", {})
        webhook = params.get("webhook")
        
        if not model_version:
            return {"error": "model parameter required"}
        
        # Create prediction
        prediction = self.client.predictions.create(
            version=model_version,
            input=input_data,
            webhook=webhook
        )
        
        # Wait for prediction to complete
        prediction.wait()
        
        return {
            "id": prediction.id,
            "status": prediction.status,
            "output": prediction.output,
            "model": model_version,
            "metrics": prediction.metrics if hasattr(prediction, 'metrics') else {}
        }
    
    def _list_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List public models"""
        cursor = params.get("cursor")
        
        models = self.client.models.list(cursor=cursor)
        
        model_list = []
        for model in models:
            model_list.append({
                "owner": model.owner,
                "name": model.name,
                "description": model.description,
                "latest_version": model.latest_version.id if model.latest_version else None
            })
        
        return {
            "models": model_list,
            "count": len(model_list)
        }
    
    def _get_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get model details"""
        model_name = params.get("model")  # e.g., "stability-ai/sdxl"
        
        if not model_name:
            return {"error": "model parameter required"}
        
        model = self.client.models.get(model_name)
        
        return {
            "owner": model.owner,
            "name": model.name,
            "description": model.description,
            "visibility": model.visibility,
            "github_url": model.github_url,
            "paper_url": model.paper_url,
            "license_url": model.license_url,
            "latest_version": {
                "id": model.latest_version.id,
                "created_at": str(model.latest_version.created_at)
            } if model.latest_version else None
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.client = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = ReplicatePlugin
PLUGIN_NAME = "replicate"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Replicate (100+ models)"
PLUGIN_ACTIONS = ["run", "predict", "list_models", "get_model"]

# Popular model examples:
# - meta/llama-2-70b-chat
# - stability-ai/sdxl
# - stability-ai/stable-diffusion
# - openai/whisper
# - salesforce/blip
# - pharmapsychotic/clip-interrogator
