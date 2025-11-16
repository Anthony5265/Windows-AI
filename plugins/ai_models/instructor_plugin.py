"""
Instructor Embeddings Plugin
Instruction-finetuned text embeddings
"""

from typing import Dict, Any, Optional, List
import os


class InstructorPlugin:
    """Plugin for Instructor embeddings"""

    name = "instructor"
    version = "1.0.0"
    description = "Integration with Instructor models for instruction-based embeddings"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Instructor plugin"""
        try:
            from InstructorEmbedding import INSTRUCTOR

            model_name = config.get("model", "hkunlp/instructor-large") if config else "hkunlp/instructor-large"

            self.model = INSTRUCTOR(model_name)
            self._initialized = True
            return True

        except ImportError:
            print("InstructorEmbedding package not installed. Install with: pip install InstructorEmbedding")
            return False
        except Exception as e:
            print(f"Error initializing Instructor plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Instructor action"""
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
        """Embed text with instruction"""
        texts = params.get("texts", [])
        instruction = params.get("instruction", "Represent the document for retrieval:")

        if isinstance(texts, str):
            texts = [texts]

        # Format as instruction-text pairs
        texts_with_instruction = [[instruction, text] for text in texts]

        embeddings = self.model.encode(texts_with_instruction)

        return {
            "success": True,
            "embeddings": embeddings.tolist()
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.model = None
        return True
