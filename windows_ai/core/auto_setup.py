"""
Windows AI Auto-Setup System
Handles first-run setup, dependency installation, and zero-config initialization
"""

import asyncio
import logging
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
import subprocess

logger = logging.getLogger(__name__)

class AutoSetup:
    """Automatic setup and configuration system"""

    def __init__(self):
        self.base_dir = Path.home() / ".windows_ai"
        self.config_file = self.base_dir / "config.json"
        self.models_dir = self.base_dir / "models"
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"

    async def run_first_time_setup(self) -> Dict:
        """Run complete first-time setup"""
        logger.info("[*] Starting Windows AI first-time setup...")

        results = {
            "directories_created": False,
            "dependencies_installed": False,
            "models_downloaded": False,
            "config_created": False,
            "system_optimized": False
        }

        try:
            # Step 1: Create directory structure
            logger.info("[*] Creating directory structure...")
            await self._create_directories()
            results["directories_created"] = True

            # Step 2: Install dependencies
            logger.info("[*] Installing dependencies...")
            await self._install_dependencies()
            results["dependencies_installed"] = True

            # Step 3: Download essential models
            logger.info("[*] Downloading essential AI models...")
            await self._download_essential_models()
            results["models_downloaded"] = True

            # Step 4: Create configuration
            logger.info("[*] Creating configuration...")
            await self._create_default_config()
            results["config_created"] = True

            # Step 5: Optimize system settings
            logger.info("[*] Optimizing system settings...")
            await self._optimize_system()
            results["system_optimized"] = True

            logger.info("[+] Windows AI setup complete! Ready to use.")
            return results

        except Exception as e:
            logger.error(f"[!] Setup failed: {e}")
            return results

    async def _create_directories(self):
        """Create necessary directory structure"""
        directories = [
            self.base_dir,
            self.models_dir,
            self.data_dir,
            self.logs_dir,
            self.base_dir / "cache",
            self.base_dir / "temp",
            self.base_dir / "plugins",
            self.base_dir / "embeddings",
            self.base_dir / "vector_stores",
            self.base_dir / "workflows"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"  [+] Created {directory}")

    async def _install_dependencies(self):
        """Install all required Python packages"""
        from windows_ai.core.dependency_installer import DependencyInstaller

        installer = DependencyInstaller()
        await installer.install_all()

    async def _download_essential_models(self):
        """Download essential AI models for offline use"""
        models_to_download = [
            {
                "name": "sentence-transformers/all-MiniLM-L6-v2",
                "type": "embeddings",
                "size": "80MB"
            },
            {
                "name": "facebook/bart-large-cnn",
                "type": "summarization",
                "size": "1.6GB"
            }
        ]

        for model in models_to_download:
            try:
                logger.info(f"  [*] Downloading {model['name']} ({model['size']})...")
                await self._download_model(model)
                logger.info(f"  [+] Downloaded {model['name']}")
            except Exception as e:
                logger.warning(f"  [!] Failed to download {model['name']}: {e}")

    async def _download_model(self, model: Dict):
        """Download a specific model"""
        model_type = model.get("type")
        model_name = model.get("name")

        if model_type == "embeddings":
            try:
                from sentence_transformers import SentenceTransformer
                # Download to local cache
                SentenceTransformer(model_name, cache_folder=str(self.models_dir))
            except ImportError:
                logger.warning(f"sentence-transformers not available, skipping {model_name}")

        elif model_type == "summarization":
            try:
                from transformers import pipeline
                # Download model to local cache
                pipeline("summarization", model=model_name, cache_dir=str(self.models_dir))
            except ImportError:
                logger.warning(f"transformers not available, skipping {model_name}")

    async def _create_default_config(self):
        """Create default configuration file"""
        config = {
            "version": "1.0.0",
            "first_run_completed": True,
            "directories": {
                "base": str(self.base_dir),
                "models": str(self.models_dir),
                "data": str(self.data_dir),
                "logs": str(self.logs_dir)
            },
            "settings": {
                "auto_update": True,
                "telemetry": False,
                "offline_mode": False,
                "privacy_mode": "standard",
                "performance_mode": "balanced",
                "max_memory_gb": 8,
                "max_cpu_cores": 4
            },
            "providers": {
                "default_llm": "openai",
                "default_image_gen": "stability",
                "default_audio": "elevenlabs",
                "default_embeddings": "openai"
            },
            "api_keys": self._detect_api_keys(),
            "features": {
                "enable_all": True,
                "sandbox_level": "standard"
            }
        }

        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"  [+] Configuration saved to {self.config_file}")

    def _detect_api_keys(self) -> Dict:
        """Auto-detect API keys from environment"""
        key_patterns = [
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
            "MISTRAL_API_KEY", "COHERE_API_KEY", "GROQ_API_KEY",
            "ELEVENLABS_API_KEY", "DEEPGRAM_API_KEY", "STABILITY_API_KEY",
            "REPLICATE_API_TOKEN", "HUGGINGFACE_API_KEY", "AWS_ACCESS_KEY_ID",
            "AZURE_API_KEY", "GCP_API_KEY"
        ]

        detected = {}
        for key in key_patterns:
            value = os.environ.get(key)
            if value:
                detected[key] = value
                logger.info(f"  [+] Detected {key}")

        return detected

    async def _optimize_system(self):
        """Optimize system settings for AI workloads"""
        import platform
        import psutil

        # Detect system capabilities
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)

        logger.info(f"  [*] System: {platform.system()} {platform.release()}")
        logger.info(f"  [*] CPU Cores: {cpu_count}")
        logger.info(f"  [*] RAM: {memory_gb:.1f} GB")

        # Optimize settings based on system
        optimizations = {
            "torch_threads": min(cpu_count - 1, 8),
            "batch_size": "auto",
            "gpu_available": self._check_gpu()
        }

        if optimizations["gpu_available"]:
            logger.info("  [+] GPU detected - enabling GPU acceleration")
        else:
            logger.info("  [*] No GPU detected - using CPU mode")

        return optimizations

    def _check_gpu(self) -> bool:
        """Check if GPU is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def is_first_run(self) -> bool:
        """Check if this is the first run"""
        return not self.config_file.exists()

    def load_config(self) -> Dict:
        """Load existing configuration"""
        if not self.config_file.exists():
            return {}

        with open(self.config_file, "r") as f:
            return json.load(f)

    async def update_config(self, updates: Dict):
        """Update configuration with new values"""
        config = self.load_config()
        config.update(updates)

        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)


async def ensure_setup() -> Dict:
    """Ensure Windows AI is properly set up"""
    setup = AutoSetup()

    if setup.is_first_run():
        logger.info("[*] Welcome to Windows AI! Running first-time setup...")
        return await setup.run_first_time_setup()
    else:
        logger.info("[+] Windows AI already configured")
        return setup.load_config()
