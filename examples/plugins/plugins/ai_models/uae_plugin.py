"""
UAE (Universal AnglE Embeddings) Plugin
Angle-optimized text embeddings
"""

from typing import Dict, Any, Optional, List
import os


class UAEPlugin:
    """Plugin for UAE embeddings"""

    name = "uae"
    version = "1.0.0"
    description = "Integration with UAE models for angle-optimized embeddings"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the UAE plugin"""
        try:
            from transformers import AutoTokenizer, AutoModel

            model_name = config.get("model", "WhereIsAI/UAE-Large-V1") if config else "WhereIsAI/UAE-Large-V1"

            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self._initialized = True
            return True

        except ImportError:
            print("transformers package not installed. Install with: pip install transformers")
            return False
        except Exception as e:
            print(f"Error initializing UAE plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a UAE action"""
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
        """Embed text(s)"""
        import torch
        import torch.nn.functional as F

        texts = params.get("texts", [])

        if isinstance(texts, str):
            texts = [texts]

        inputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt")

        with torch.no_grad():
            outputs = self.model(**inputs)

        # CLS pooling + normalization
        embeddings = outputs.last_hidden_state[:, 0]
        embeddings = F.normalize(embeddings, p=2, dim=1)

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
