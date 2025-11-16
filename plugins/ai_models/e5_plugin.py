"""
E5 Embeddings Plugin
Text embeddings from Microsoft
"""

from typing import Dict, Any, Optional, List
import os


class E5Plugin:
    """Plugin for E5 embeddings"""

    name = "e5"
    version = "1.0.0"
    description = "Integration with E5 models (small, base, large) for embeddings"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the E5 plugin"""
        try:
            from transformers import AutoTokenizer, AutoModel

            model_name = config.get("model", "intfloat/e5-large-v2") if config else "intfloat/e5-large-v2"

            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self._initialized = True
            return True

        except ImportError:
            print("transformers package not installed. Install with: pip install transformers")
            return False
        except Exception as e:
            print(f"Error initializing E5 plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an E5 action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "embed":
                return self._embed(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _embed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Embed text(s) with E5"""
        import torch

        texts = params.get("texts", [])
        is_query = params.get("is_query", False)

        if isinstance(texts, str):
            texts = [texts]

        # Add E5 instruction prefix
        if is_query:
            texts = [f"query: {text}" for text in texts]
        else:
            texts = [f"passage: {text}" for text in texts]

        # Tokenize and encode
        inputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt")

        with torch.no_grad():
            outputs = self.model(**inputs)

        # Mean pooling
        embeddings = outputs.last_hidden_state.mean(dim=1)

        return {
            "success": True,
            "embeddings": embeddings.tolist()
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.model = None
        self.tokenizer = None
        return True
