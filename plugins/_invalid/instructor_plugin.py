"""
Instructor Embeddings Plugin
Supports instruction-following text embeddings using Instructor models
"""

from typing import Dict, Any, Optional, List
import os


class InstructorPlugin:
    """Plugin for Instructor embeddings"""

    name = "instructor"
    version = "1.0.0"
    description = "Integration with Instructor embeddings for instruction-following text embeddings"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Instructor plugin"""
        try:
            from InstructorEmbedding import INSTRUCTOR

            # Get model name from config or use default
            model_name = (
                config.get("model_name") if config
                else "hkunlp/instructor-large"
            )

            # Initialize the model
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
            return {"error": "Plugin not initialized. Please check model configuration."}

        try:
            if action == "embed":
                return self._embed(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _embed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate embeddings with instructions"""
        sentences = params.get("sentences", [])
        instruction = params.get("instruction", "Represent the document for retrieval: ")

        if not sentences:
            return {"error": "sentences parameter is required"}

        if isinstance(sentences, str):
            sentences = [sentences]

        # Prepare input as list of [instruction, sentence] pairs
        instruction_sentence_pairs = [[instruction, sentence] for sentence in sentences]

        try:
            embeddings = self.model.encode(instruction_sentence_pairs)

            # Convert to list if it's a numpy array
            if hasattr(embeddings, 'tolist'):
                embeddings = embeddings.tolist()

            return {
                "embeddings": embeddings,
                "instruction": instruction,
                "count": len(sentences),
                "dimensions": len(embeddings[0]) if embeddings else 0
            }

        except Exception as e:
            return {"error": f"Error generating embeddings: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self.model = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = InstructorPlugin
PLUGIN_NAME = "instructor"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Instructor embeddings for instruction-following text embeddings"
PLUGIN_ACTIONS = ["embed"]