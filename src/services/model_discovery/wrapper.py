"""
ModelDiscovery Wrapper - High-level API for model discovery and download
"""
from __future__ import annotations

import os
from typing import List, Dict, Any
from .discovery import discover_models, fetch_llm


class ModelDiscovery:
    """High-level API for discovering and downloading AI models"""

    def __init__(self, model_dir: str = "models"):
        """Initialize model discovery with default model directory"""
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)

    def discover_all(self) -> List[Dict[str, Any]]:
        """Discover all available models (local and known remote)"""
        models = []

        # Discover local models
        local_models = discover_models(self.model_dir, extension=".model")
        for path in local_models:
            models.append({
                "type": "local",
                "name": os.path.basename(path),
                "path": path,
                "size": os.path.getsize(path) if os.path.exists(path) else 0
            })

        # Also check for common model files (.gguf, .bin, .safetensors)
        for ext in [".gguf", ".bin", ".safetensors", ".pth", ".pt"]:
            local_files = discover_models(self.model_dir, extension=ext)
            for path in local_files:
                models.append({
                    "type": "local",
                    "name": os.path.basename(path),
                    "path": path,
                    "size": os.path.getsize(path) if os.path.exists(path) else 0
                })

        # Add popular models from HuggingFace that can be downloaded
        popular_models = [
            {"type": "huggingface", "name": "microsoft/phi-2", "id": "microsoft/phi-2"},
            {"type": "huggingface", "name": "mistralai/Mistral-7B-v0.1", "id": "mistralai/Mistral-7B-v0.1"},
            {"type": "huggingface", "name": "meta-llama/Llama-2-7b-hf", "id": "meta-llama/Llama-2-7b-hf"},
            {"type": "huggingface", "name": "tiiuae/falcon-7b", "id": "tiiuae/falcon-7b"},
        ]
        models.extend(popular_models)

        return models

    def download_model(self, model_id: str, source: str = "huggingface") -> Dict[str, Any]:
        """Download a model from specified source

        Args:
            model_id: Model identifier (HuggingFace repo ID or URL)
            source: Source type ('huggingface', 'url', or 'local')

        Returns:
            Dict with download result
        """
        try:
            if source == "url" or model_id.startswith(("http://", "https://")):
                # Download from URL
                filename = os.path.basename(model_id.split("?")[0])
                dest_path = os.path.join(self.model_dir, filename)
                result = fetch_llm(model_id, dest_path)

                if result:
                    return {
                        "success": True,
                        "path": result,
                        "name": filename,
                        "size": os.path.getsize(result) if os.path.exists(result) else 0
                    }
                else:
                    return {"success": False, "error": "Download failed"}

            elif source == "huggingface":
                # Download from HuggingFace
                dest_dir = os.path.join(self.model_dir, model_id.replace("/", "_"))
                result = fetch_llm(model_id, dest_dir)

                if result:
                    return {
                        "success": True,
                        "path": result,
                        "name": model_id,
                        "type": "directory"
                    }
                else:
                    return {"success": False, "error": "Download failed"}

            else:
                return {"success": False, "error": f"Unknown source: {source}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        model_path = os.path.join(self.model_dir, model_name)

        if os.path.exists(model_path):
            if os.path.isfile(model_path):
                return {
                    "name": model_name,
                    "path": model_path,
                    "type": "file",
                    "size": os.path.getsize(model_path),
                    "exists": True
                }
            elif os.path.isdir(model_path):
                # Calculate total size of directory
                total_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(model_path)
                    for filename in filenames
                )
                return {
                    "name": model_name,
                    "path": model_path,
                    "type": "directory",
                    "size": total_size,
                    "exists": True
                }

        return {
            "name": model_name,
            "exists": False,
            "error": "Model not found"
        }
