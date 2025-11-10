"""
Model Download Manager
Handles downloading, installing, and managing AI models (Ollama, GGUF, etc.)

Features:
- Browse available models
- Download models with progress tracking
- Manage installed models
- Model metadata and capabilities
- Multi-source support (Ollama, Hugging Face)
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import httpx
import json

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages AI model downloads and installations"""

    def __init__(self, models_dir: Optional[Path] = None):
        """
        Initialize model manager

        Args:
            models_dir: Directory to store downloaded models
        """
        self.models_dir = models_dir or Path.home() / ".windows-ai" / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Ollama configuration
        self.ollama_url = "http://localhost:11434"

        # Model catalog
        self.model_catalog = self._load_model_catalog()

        # Download progress tracking
        self.downloads: Dict[str, Dict[str, Any]] = {}

    def _load_model_catalog(self) -> List[Dict[str, Any]]:
        """Load curated model catalog"""
        return [
            {
                "id": "llama2:7b",
                "name": "Llama 2 7B",
                "provider": "ollama",
                "size": "3.8 GB",
                "description": "Meta's Llama 2 model - excellent general-purpose assistant",
                "capabilities": ["chat", "generation"],
                "recommended": True,
                "category": "general"
            },
            {
                "id": "mistral:7b",
                "name": "Mistral 7B",
                "provider": "ollama",
                "size": "4.1 GB",
                "description": "High-performance 7B model with excellent instruction following",
                "capabilities": ["chat", "generation"],
                "recommended": True,
                "category": "general"
            },
            {
                "id": "codellama:7b",
                "name": "Code Llama 7B",
                "provider": "ollama",
                "size": "3.8 GB",
                "description": "Specialized for code generation and programming tasks",
                "capabilities": ["code", "generation"],
                "recommended": True,
                "category": "coding"
            },
            {
                "id": "phi:2.7b",
                "name": "Phi 2.7B",
                "provider": "ollama",
                "size": "1.6 GB",
                "description": "Microsoft's compact but capable model - fast and efficient",
                "capabilities": ["chat", "generation"],
                "recommended": True,
                "category": "lightweight"
            },
            {
                "id": "llama2:13b",
                "name": "Llama 2 13B",
                "provider": "ollama",
                "size": "7.3 GB",
                "description": "Larger Llama 2 model with improved capabilities",
                "capabilities": ["chat", "generation"],
                "recommended": False,
                "category": "general"
            },
            {
                "id": "codellama:13b",
                "name": "Code Llama 13B",
                "provider": "ollama",
                "size": "7.3 GB",
                "description": "Larger code model for complex programming tasks",
                "capabilities": ["code", "generation"],
                "recommended": False,
                "category": "coding"
            },
            {
                "id": "neural-chat:7b",
                "name": "Neural Chat 7B",
                "provider": "ollama",
                "size": "4.1 GB",
                "description": "Optimized for conversational AI",
                "capabilities": ["chat"],
                "recommended": False,
                "category": "chat"
            },
            {
                "id": "orca-mini:3b",
                "name": "Orca Mini 3B",
                "provider": "ollama",
                "size": "1.9 GB",
                "description": "Compact model fine-tuned from Llama 2",
                "capabilities": ["chat", "generation"],
                "recommended": False,
                "category": "lightweight"
            },
            {
                "id": "vicuna:7b",
                "name": "Vicuna 7B",
                "provider": "ollama",
                "size": "3.8 GB",
                "description": "Fine-tuned Llama model with strong instruction following",
                "capabilities": ["chat", "generation"],
                "recommended": False,
                "category": "general"
            },
            {
                "id": "llama2:70b",
                "name": "Llama 2 70B",
                "provider": "ollama",
                "size": "39 GB",
                "description": "Largest Llama 2 model - highest quality responses (requires powerful hardware)",
                "capabilities": ["chat", "generation"],
                "recommended": False,
                "category": "premium"
            }
        ]

    async def list_available_models(self, category: Optional[str] = None,
                                    recommended_only: bool = False) -> List[Dict[str, Any]]:
        """
        List available models from catalog

        Args:
            category: Filter by category (general, coding, chat, lightweight, premium)
            recommended_only: Only show recommended models

        Returns:
            List of model metadata dictionaries
        """
        models = self.model_catalog.copy()

        # Apply filters
        if category:
            models = [m for m in models if m.get("category") == category]

        if recommended_only:
            models = [m for m in models if m.get("recommended", False)]

        # Check which models are installed
        installed = await self.list_installed_models()
        installed_ids = {m["id"] for m in installed}

        for model in models:
            model["installed"] = model["id"] in installed_ids

        return models

    async def list_installed_models(self) -> List[Dict[str, Any]]:
        """
        List installed models

        Returns:
            List of installed model metadata
        """
        installed = []

        # Check Ollama models
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")

                if response.status_code == 200:
                    data = response.json()
                    for model in data.get("models", []):
                        installed.append({
                            "id": model["name"],
                            "name": model["name"],
                            "provider": "ollama",
                            "size": model.get("size", 0),
                            "modified": model.get("modified_at")
                        })
        except Exception as e:
            logger.warning(f"Could not list Ollama models: {e}")

        # Check local GGUF models
        try:
            if self.models_dir.exists():
                for model_file in self.models_dir.glob("*.gguf"):
                    size = model_file.stat().st_size
                    installed.append({
                        "id": model_file.stem,
                        "name": model_file.name,
                        "provider": "local",
                        "size": size,
                        "path": str(model_file)
                    })
        except Exception as e:
            logger.warning(f"Could not list local models: {e}")

        return installed

    async def download_model(self, model_id: str,
                           progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Download a model

        Args:
            model_id: Model identifier
            progress_callback: Optional callback for progress updates

        Returns:
            Result dictionary with status and metadata
        """
        # Find model in catalog
        model = next((m for m in self.model_catalog if m["id"] == model_id), None)
        if not model:
            return {
                "status": "error",
                "message": f"Model {model_id} not found in catalog"
            }

        provider = model.get("provider", "ollama")

        # Track download
        self.downloads[model_id] = {
            "status": "downloading",
            "progress": 0,
            "model": model
        }

        try:
            if provider == "ollama":
                result = await self._download_ollama_model(model_id, progress_callback)
            else:
                result = {
                    "status": "error",
                    "message": f"Provider {provider} not supported yet"
                }

            # Update download tracking
            if result["status"] == "success":
                self.downloads[model_id]["status"] = "completed"
                self.downloads[model_id]["progress"] = 100
            else:
                self.downloads[model_id]["status"] = "failed"

            return result

        except Exception as e:
            logger.error(f"Error downloading model {model_id}: {e}")
            self.downloads[model_id]["status"] = "failed"
            return {
                "status": "error",
                "message": str(e)
            }

    async def _download_ollama_model(self, model_id: str,
                                     progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Download model via Ollama

        Args:
            model_id: Ollama model name
            progress_callback: Optional progress callback

        Returns:
            Download result
        """
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/pull",
                    json={"name": model_id},
                    timeout=600.0
                )

                if response.status_code == 200:
                    # Process streaming response
                    total_size = 0
                    downloaded = 0

                    async for line in response.aiter_lines():
                        if line:
                            try:
                                progress_data = json.loads(line)

                                # Extract progress info
                                if "total" in progress_data:
                                    total_size = progress_data["total"]
                                if "completed" in progress_data:
                                    downloaded = progress_data["completed"]

                                # Calculate percentage
                                if total_size > 0:
                                    percent = int((downloaded / total_size) * 100)
                                    self.downloads[model_id]["progress"] = percent

                                    if progress_callback:
                                        await progress_callback(percent, downloaded, total_size)

                            except json.JSONDecodeError:
                                pass

                    return {
                        "status": "success",
                        "message": f"Model {model_id} downloaded successfully",
                        "model_id": model_id
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Ollama returned HTTP {response.status_code}"
                    }

        except httpx.ConnectError:
            return {
                "status": "error",
                "message": "Cannot connect to Ollama. Please make sure Ollama is running."
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Download failed: {str(e)}"
            }

    async def delete_model(self, model_id: str) -> Dict[str, Any]:
        """
        Delete an installed model

        Args:
            model_id: Model identifier

        Returns:
            Deletion result
        """
        # Try Ollama first
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.ollama_url}/api/delete",
                    json={"name": model_id}
                )

                if response.status_code == 200:
                    return {
                        "status": "success",
                        "message": f"Model {model_id} deleted successfully"
                    }
        except Exception as e:
            logger.warning(f"Ollama delete failed: {e}")

        # Try local file deletion
        try:
            model_path = self.models_dir / f"{model_id}.gguf"
            if model_path.exists():
                model_path.unlink()
                return {
                    "status": "success",
                    "message": f"Model {model_id} deleted successfully"
                }
        except Exception as e:
            logger.error(f"Local model delete failed: {e}")

        return {
            "status": "error",
            "message": f"Model {model_id} not found"
        }

    async def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """
        Get detailed model information

        Args:
            model_id: Model identifier

        Returns:
            Model metadata and status
        """
        # Check catalog
        catalog_model = next((m for m in self.model_catalog if m["id"] == model_id), None)

        # Check if installed
        installed = await self.list_installed_models()
        installed_model = next((m for m in installed if m["id"] == model_id), None)

        if catalog_model:
            info = catalog_model.copy()
            info["installed"] = installed_model is not None
            if installed_model:
                info["install_info"] = installed_model
            return info
        elif installed_model:
            return installed_model
        else:
            return {
                "status": "error",
                "message": f"Model {model_id} not found"
            }

    def get_download_status(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get download status for a model

        Args:
            model_id: Model identifier

        Returns:
            Download status or None
        """
        return self.downloads.get(model_id)


# Example usage
if __name__ == "__main__":
    async def test_manager():
        manager = ModelManager()

        # List available models
        print("Available models:")
        models = await manager.list_available_models(recommended_only=True)
        for model in models:
            print(f"  - {model['name']} ({model['size']}) - {model['description']}")

        # List installed models
        print("\nInstalled models:")
        installed = await manager.list_installed_models()
        for model in installed:
            print(f"  - {model['name']} ({model.get('size', 'Unknown size')})")

    asyncio.run(test_manager())
