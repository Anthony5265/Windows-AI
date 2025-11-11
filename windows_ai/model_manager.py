"""
Model Download Manager
Handles downloading, installing, and managing AI models (Ollama, GGUF, etc.)

Features:
- Browse available models
- Download models with progress tracking
- Manage installed models
- Model metadata and capabilities
- Multi-source support (Ollama, Hugging Face)
- System specs detection for model recommendations
"""

import os
import asyncio
import logging
import platform
import psutil
import subprocess
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

        # System specs cache
        self._system_specs: Optional[Dict[str, Any]] = None

    # =========================================================================
    # System Specs Detection
    # =========================================================================

    def get_system_specs(self) -> Dict[str, Any]:
        """
        Get system specifications for model recommendations

        Returns:
            Dictionary containing RAM, CPU, GPU info
        """
        if self._system_specs:
            return self._system_specs

        specs = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }

        # RAM information
        try:
            mem = psutil.virtual_memory()
            specs["ram_total_gb"] = round(mem.total / (1024**3), 2)
            specs["ram_available_gb"] = round(mem.available / (1024**3), 2)
            specs["ram_percent_used"] = mem.percent
        except Exception as e:
            logger.warning(f"Could not detect RAM: {e}")
            specs["ram_total_gb"] = 0
            specs["ram_available_gb"] = 0

        # CPU information
        try:
            specs["cpu_count"] = psutil.cpu_count(logical=True)
            specs["cpu_physical_cores"] = psutil.cpu_count(logical=False)
            specs["cpu_freq_mhz"] = psutil.cpu_freq().max if psutil.cpu_freq() else 0
        except Exception as e:
            logger.warning(f"Could not detect CPU: {e}")
            specs["cpu_count"] = 0

        # GPU detection
        specs["gpu"] = self._detect_gpu()

        # Disk space for models directory
        try:
            disk = psutil.disk_usage(str(self.models_dir))
            specs["disk_free_gb"] = round(disk.free / (1024**3), 2)
            specs["disk_total_gb"] = round(disk.total / (1024**3), 2)
        except Exception as e:
            logger.warning(f"Could not detect disk space: {e}")
            specs["disk_free_gb"] = 0

        self._system_specs = specs
        return specs

    def _detect_gpu(self) -> Dict[str, Any]:
        """
        Detect GPU information (NVIDIA, AMD, Intel, Apple Silicon)

        Returns:
            Dictionary with GPU type, memory, and capabilities
        """
        gpu_info = {
            "available": False,
            "type": "none",
            "name": "CPU Only",
            "memory_gb": 0,
            "cuda": False,
            "metal": False,
            "rocm": False
        }

        system = platform.system()

        # Check for NVIDIA GPU (CUDA)
        try:
            if system in ["Linux", "Windows"]:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                if result.returncode == 0 and result.stdout:
                    lines = result.stdout.strip().split("\n")
                    if lines:
                        parts = lines[0].split(",")
                        gpu_info["available"] = True
                        gpu_info["type"] = "nvidia"
                        gpu_info["name"] = parts[0].strip()
                        gpu_info["cuda"] = True
                        if len(parts) > 1:
                            mem_str = parts[1].strip().split()[0]
                            gpu_info["memory_gb"] = round(int(mem_str) / 1024, 2)
                        return gpu_info
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
            logger.debug(f"NVIDIA GPU not detected: {e}")

        # Check for Apple Silicon (Metal)
        if system == "Darwin" and platform.machine() == "arm64":
            gpu_info["available"] = True
            gpu_info["type"] = "apple_silicon"
            gpu_info["name"] = "Apple Silicon GPU"
            gpu_info["metal"] = True
            # Apple Silicon shares RAM with GPU
            try:
                mem = psutil.virtual_memory()
                gpu_info["memory_gb"] = round(mem.total / (1024**3), 2)
            except:
                pass
            return gpu_info

        # Check for AMD GPU (ROCm)
        try:
            if system == "Linux":
                result = subprocess.run(
                    ["rocm-smi", "--showproductname"],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                if result.returncode == 0 and result.stdout:
                    gpu_info["available"] = True
                    gpu_info["type"] = "amd"
                    gpu_info["name"] = "AMD GPU"
                    gpu_info["rocm"] = True
                    return gpu_info
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
            logger.debug(f"AMD GPU not detected: {e}")

        # Fallback: Try to detect integrated GPU on Windows
        if system == "Windows":
            try:
                import wmi
                c = wmi.WMI()
                for gpu in c.Win32_VideoController():
                    if gpu.Name:
                        gpu_info["available"] = True
                        gpu_info["type"] = "integrated"
                        gpu_info["name"] = gpu.Name
                        if gpu.AdapterRAM:
                            gpu_info["memory_gb"] = round(int(gpu.AdapterRAM) / (1024**3), 2)
                        return gpu_info
            except Exception as e:
                logger.debug(f"Could not detect Windows GPU: {e}")

        return gpu_info

    def get_recommended_models_for_system(self) -> List[Dict[str, Any]]:
        """
        Get recommended models based on system specifications

        Returns:
            List of recommended model metadata
        """
        specs = self.get_system_specs()
        ram_gb = specs.get("ram_total_gb", 0)
        gpu_available = specs.get("gpu", {}).get("available", False)

        # Filter models based on RAM requirements
        suitable_models = []
        for model in self.model_catalog:
            ram_required_str = model.get("ram_required", "0 GB")
            ram_required = float(ram_required_str.split()[0])

            # Check if system has enough RAM (with 2GB buffer)
            if ram_gb >= (ram_required + 2):
                model_copy = model.copy()

                # Add suitability score
                if ram_gb >= ram_required * 2:
                    model_copy["suitability"] = "excellent"
                elif ram_gb >= ram_required * 1.5:
                    model_copy["suitability"] = "good"
                else:
                    model_copy["suitability"] = "minimum"

                # Boost score for GPU-accelerated systems
                if gpu_available and model_copy.get("tier") in [2, 3]:
                    model_copy["gpu_optimized"] = True

                suitable_models.append(model_copy)

        # Sort by tier (lower is better for recommendations) and recommended flag
        suitable_models.sort(key=lambda m: (m.get("tier", 99), not m.get("recommended", False)))

        return suitable_models

    # =========================================================================
    # Model Catalog
    # =========================================================================

    def _load_model_catalog(self) -> List[Dict[str, Any]]:
        """Load curated model catalog with latest models"""
        return [
            # Tier 1: Essential (Auto-install on first run)
            {
                "id": "llama3.2:1b",
                "name": "Llama 3.2 1B",
                "provider": "ollama",
                "size": "1.3 GB",
                "ram_required": "2 GB",
                "description": "Ultra-fast, minimal resource model - perfect for quick tasks",
                "capabilities": ["chat", "generation"],
                "recommended": True,
                "tier": 1,
                "category": "lightweight",
                "quantization": "Q4"
            },
            {
                "id": "llama3.2:3b",
                "name": "Llama 3.2 3B",
                "provider": "ollama",
                "size": "2.0 GB",
                "ram_required": "4 GB",
                "description": "Fast, general-purpose model with excellent quality - recommended default",
                "capabilities": ["chat", "generation"],
                "recommended": True,
                "tier": 1,
                "category": "general",
                "quantization": "Q4"
            },

            # Tier 2: Performance (User-selected)
            {
                "id": "llama3.1:8b",
                "name": "Llama 3.1 8B",
                "provider": "ollama",
                "size": "4.7 GB",
                "ram_required": "8 GB",
                "description": "High-quality chat model with excellent reasoning capabilities",
                "capabilities": ["chat", "generation", "reasoning"],
                "recommended": True,
                "tier": 2,
                "category": "general",
                "quantization": "Q4"
            },
            {
                "id": "mistral:7b",
                "name": "Mistral 7B",
                "provider": "ollama",
                "size": "4.1 GB",
                "ram_required": "8 GB",
                "description": "Balanced performance with excellent instruction following",
                "capabilities": ["chat", "generation"],
                "recommended": True,
                "tier": 2,
                "category": "general",
                "quantization": "Q4"
            },
            {
                "id": "deepseek-coder:6.7b",
                "name": "DeepSeek Coder 6.7B",
                "provider": "ollama",
                "size": "3.8 GB",
                "ram_required": "8 GB",
                "description": "Code specialist with excellent programming capabilities",
                "capabilities": ["code", "generation", "analysis"],
                "recommended": True,
                "tier": 2,
                "category": "coding",
                "quantization": "Q4"
            },

            # Tier 3: Advanced (Power users)
            {
                "id": "llama3.1:70b",
                "name": "Llama 3.1 70B",
                "provider": "ollama",
                "size": "40 GB",
                "ram_required": "64 GB",
                "description": "Maximum quality responses - requires powerful hardware",
                "capabilities": ["chat", "generation", "reasoning", "analysis"],
                "recommended": False,
                "tier": 3,
                "category": "premium",
                "quantization": "Q4"
            },
            {
                "id": "codellama:34b",
                "name": "Code Llama 34B",
                "provider": "ollama",
                "size": "19 GB",
                "ram_required": "32 GB",
                "description": "Advanced coding model for complex programming tasks",
                "capabilities": ["code", "generation", "debugging", "analysis"],
                "recommended": False,
                "tier": 3,
                "category": "coding",
                "quantization": "Q4"
            },

            # Embeddings
            {
                "id": "nomic-embed-text",
                "name": "Nomic Embed Text",
                "provider": "ollama",
                "size": "274 MB",
                "ram_required": "1 GB",
                "description": "High-quality text embeddings for RAG and semantic search",
                "capabilities": ["embeddings", "rag"],
                "recommended": True,
                "tier": 1,
                "category": "embeddings",
                "quantization": "FP16"
            },

            # Legacy models (for compatibility)
            {
                "id": "llama2:7b",
                "name": "Llama 2 7B",
                "provider": "ollama",
                "size": "3.8 GB",
                "ram_required": "8 GB",
                "description": "Legacy Llama 2 model - consider upgrading to Llama 3.2",
                "capabilities": ["chat", "generation"],
                "recommended": False,
                "tier": 2,
                "category": "general",
                "quantization": "Q4"
            },
            {
                "id": "codellama:7b",
                "name": "Code Llama 7B",
                "provider": "ollama",
                "size": "3.8 GB",
                "ram_required": "8 GB",
                "description": "Legacy code model - consider DeepSeek Coder for better results",
                "capabilities": ["code", "generation"],
                "recommended": False,
                "tier": 2,
                "category": "coding",
                "quantization": "Q4"
            },
            {
                "id": "phi:2.7b",
                "name": "Phi 2.7B",
                "provider": "ollama",
                "size": "1.6 GB",
                "ram_required": "4 GB",
                "description": "Microsoft's compact model - fast and efficient",
                "capabilities": ["chat", "generation"],
                "recommended": False,
                "tier": 1,
                "category": "lightweight",
                "quantization": "Q4"
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
