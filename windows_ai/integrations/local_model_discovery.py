"""
Local Model Discovery

Discovers and manages locally installed AI models from:
- Ollama
- LM Studio
- text-generation-webui
- vLLM
- llama.cpp
"""

import os
import json
import shutil
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class LocalModel:
    """Represents a locally discovered AI model."""
    name: str
    provider: str  # ollama, lm_studio, tgw, vllm, llama_cpp
    size: Optional[str] = None
    path: Optional[str] = None
    endpoint: Optional[str] = None
    parameters: Optional[str] = None
    quantization: Optional[str] = None
    family: Optional[str] = None
    running: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LocalModelDiscovery:
    """
    Discovers and manages local AI models across multiple providers.
    
    Supports:
    - Ollama: CLI-based model management
    - LM Studio: GUI-based local model server
    - text-generation-webui: Web UI for text generation
    - vLLM: High-throughput serving engine
    - llama.cpp: Native C++ inference
    """

    def __init__(self):
        self._models: List[LocalModel] = []
        self._initialized = False
        self._providers: Dict[str, bool] = {}
    
    async def initialize(self):
        """Initialize and run first discovery."""
        self._initialized = True
        await self.discover_all()
    
    async def discover_all(self) -> List[LocalModel]:
        """Discover models from all available providers."""
        self._models = []
        
        # Run all discoveries concurrently
        results = await asyncio.gather(
            self._discover_ollama(),
            self._discover_lm_studio(),
            self._discover_tgw(),
            self._discover_vllm(),
            self._discover_llama_cpp(),
            return_exceptions=True,
        )
        
        for result in results:
            if isinstance(result, list):
                self._models.extend(result)
            elif isinstance(result, Exception):
                logger.debug(f"Discovery error (non-fatal): {result}")
        
        logger.info(f"Discovered {len(self._models)} local models from {len(self._providers)} providers")
        return self._models
    
    async def _discover_ollama(self) -> List[LocalModel]:
        """Discover models managed by Ollama."""
        models = []
        
        # Check if ollama is available
        ollama_path = shutil.which("ollama")
        if not ollama_path:
            self._providers["ollama"] = False
            return models
        
        self._providers["ollama"] = True
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "ollama", "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
            
            if proc.returncode == 0:
                lines = stdout.decode().strip().split("\n")
                # Skip header line
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[0]
                        size = parts[2] if len(parts) > 2 else None
                        
                        model = LocalModel(
                            name=name,
                            provider="ollama",
                            size=size,
                            endpoint="http://localhost:11434",
                            metadata={"raw_line": line},
                        )
                        
                        # Detect quantization from name
                        for q in ["q4_0", "q4_1", "q5_0", "q5_1", "q8_0", "fp16", "f16"]:
                            if q in name.lower():
                                model.quantization = q
                                break
                        
                        models.append(model)
        except (asyncio.TimeoutError, FileNotFoundError, OSError) as e:
            logger.debug(f"Ollama discovery failed: {e}")
        
        return models
    
    async def _discover_lm_studio(self) -> List[LocalModel]:
        """Discover models from LM Studio."""
        models = []
        
        # Check common LM Studio model directories
        lm_studio_paths = [
            Path.home() / ".cache" / "lm-studio" / "models",
            Path.home() / "AppData" / "Local" / "LM Studio" / "models",
            Path(os.environ.get("LM_STUDIO_MODELS", "")),
        ]
        
        found_dir = None
        for path in lm_studio_paths:
            if path.exists() and path.is_dir():
                found_dir = path
                break
        
        if not found_dir:
            self._providers["lm_studio"] = False
            return models
        
        self._providers["lm_studio"] = True
        
        # Scan for GGUF/GGML model files
        for model_file in found_dir.rglob("*.gguf"):
            name = model_file.stem
            size_bytes = model_file.stat().st_size
            size = f"{size_bytes / (1024**3):.1f}GB"
            
            model = LocalModel(
                name=name,
                provider="lm_studio",
                size=size,
                path=str(model_file),
                endpoint="http://localhost:1234/v1",
                metadata={"file_size_bytes": size_bytes},
            )
            models.append(model)
        
        for model_file in found_dir.rglob("*.ggml"):
            name = model_file.stem
            size_bytes = model_file.stat().st_size
            size = f"{size_bytes / (1024**3):.1f}GB"
            
            model = LocalModel(
                name=name,
                provider="lm_studio",
                size=size,
                path=str(model_file),
                endpoint="http://localhost:1234/v1",
                metadata={"file_size_bytes": size_bytes},
            )
            models.append(model)
        
        return models
    
    async def _discover_tgw(self) -> List[LocalModel]:
        """Discover text-generation-webui models."""
        models = []
        
        # Check common text-generation-webui model directories
        tgw_paths = [
            Path.home() / "text-generation-webui" / "models",
            Path("/opt/text-generation-webui/models"),
            Path(os.environ.get("TGW_MODELS", "")),
        ]
        
        found_dir = None
        for path in tgw_paths:
            if path.exists() and path.is_dir():
                found_dir = path
                break
        
        if not found_dir:
            self._providers["text_generation_webui"] = False
            return models
        
        self._providers["text_generation_webui"] = True
        
        for model_dir in found_dir.iterdir():
            if model_dir.is_dir() and not model_dir.name.startswith("."):
                model = LocalModel(
                    name=model_dir.name,
                    provider="text_generation_webui",
                    path=str(model_dir),
                    endpoint="http://localhost:5000/api/v1",
                )
                models.append(model)
        
        return models
    
    async def _discover_vllm(self) -> List[LocalModel]:
        """Discover vLLM served models."""
        models = []
        
        # Check if vLLM is running by trying the API
        try:
            import httpx
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get("http://localhost:8000/v1/models")
                if resp.status_code == 200:
                    self._providers["vllm"] = True
                    data = resp.json()
                    for m in data.get("data", []):
                        model = LocalModel(
                            name=m.get("id", "unknown"),
                            provider="vllm",
                            endpoint="http://localhost:8000/v1",
                            running=True,
                        )
                        models.append(model)
                    return models
        except Exception:
            pass
        
        self._providers["vllm"] = False
        return models
    
    async def _discover_llama_cpp(self) -> List[LocalModel]:
        """Discover llama.cpp models."""
        models = []
        
        # Check common llama.cpp model directories
        llama_paths = [
            Path.home() / ".cache" / "llama.cpp" / "models",
            Path.home() / "llama.cpp" / "models",
            Path(os.environ.get("LLAMA_CPP_MODELS", "")),
        ]
        
        found_dir = None
        for path in llama_paths:
            if path.exists() and path.is_dir():
                found_dir = path
                break
        
        if not found_dir:
            self._providers["llama_cpp"] = False
            return models
        
        self._providers["llama_cpp"] = True
        
        for model_file in found_dir.rglob("*.gguf"):
            name = model_file.stem
            size_bytes = model_file.stat().st_size
            size = f"{size_bytes / (1024**3):.1f}GB"
            
            model = LocalModel(
                name=name,
                provider="llama_cpp",
                size=size,
                path=str(model_file),
                metadata={"file_size_bytes": size_bytes},
            )
            models.append(model)
        
        return models
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List all discovered models."""
        return [m.to_dict() for m in self._models]
    
    def list_providers(self) -> Dict[str, bool]:
        """List all checked providers and their availability."""
        return dict(self._providers)
    
    def get_model(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific model by name."""
        for m in self._models:
            if m.name == name:
                return m.to_dict()
        return None
    
    def get_models_by_provider(self, provider: str) -> List[Dict[str, Any]]:
        """Get all models from a specific provider."""
        return [m.to_dict() for m in self._models if m.provider == provider]
