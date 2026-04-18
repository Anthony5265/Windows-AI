"""Windows AI provider and CLI detection registry.

This module centralizes discovery of third-party AI CLIs and local runtimes so
Windows AI can:
- detect pre-installed providers during setup or first run
- surface installation/authentication actions for missing providers
- recommend local models based on hardware capabilities

It is intentionally conservative: it discovers tools and proposes actions, but
it does not bypass OS security or silently install third-party software.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from shutil import which
from typing import Any, Dict, List, Optional
import os
import platform
import subprocess


DEFAULT_WINDOWS_INSTALL_PATHS = {
    "gemini": [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "GeminiCLI" / "gemini.exe",
        Path(os.environ.get("ProgramFiles", "")) / "GeminiCLI" / "gemini.exe",
    ],
    "codex": [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "CodexCLI" / "codex.exe",
        Path(os.environ.get("ProgramFiles", "")) / "CodexCLI" / "codex.exe",
    ],
    "claude": [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "ClaudeCLI" / "claude.exe",
        Path(os.environ.get("ProgramFiles", "")) / "ClaudeCLI" / "claude.exe",
    ],
    "grok": [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "GrokCLI" / "grok.exe",
        Path(os.environ.get("ProgramFiles", "")) / "GrokCLI" / "grok.exe",
    ],
    "ollama": [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe",
        Path(os.environ.get("ProgramFiles", "")) / "Ollama" / "ollama.exe",
    ],
}


@dataclass
class ProviderDefinition:
    id: str
    display_name: str
    category: str
    executable_names: List[str]
    install_url: str
    auth_hint: str
    supports_local_models: bool = False
    supports_chat: bool = True
    supports_code: bool = False
    supports_vision: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderDetectionResult:
    provider_id: str
    detected: bool
    executable_path: Optional[str]
    version: Optional[str]
    auth_configured: bool
    recommended_action: str
    install_url: str
    auth_hint: str
    capabilities: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HardwareProfile:
    platform: str
    architecture: str
    cpu_count: int
    total_memory_gb: Optional[float]
    gpu_hint: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProviderCLIRegistry:
    def __init__(self) -> None:
        self.providers: Dict[str, ProviderDefinition] = {
            "gemini": ProviderDefinition(
                id="gemini",
                display_name="Gemini CLI",
                category="cloud_cli",
                executable_names=["gemini", "gemini.exe"],
                install_url="https://ai.google.dev/",
                auth_hint="Sign in with your Google AI credentials or configure an API key.",
                supports_vision=True,
            ),
            "codex": ProviderDefinition(
                id="codex",
                display_name="Codex CLI",
                category="cloud_cli",
                executable_names=["codex", "codex.exe"],
                install_url="https://platform.openai.com/",
                auth_hint="Authenticate with your OpenAI account or API key.",
                supports_code=True,
            ),
            "claude": ProviderDefinition(
                id="claude",
                display_name="Claude CLI",
                category="cloud_cli",
                executable_names=["claude", "claude.exe"],
                install_url="https://console.anthropic.com/",
                auth_hint="Authenticate with Anthropic credentials or API key.",
                supports_code=True,
                supports_vision=True,
            ),
            "grok": ProviderDefinition(
                id="grok",
                display_name="Grok CLI",
                category="cloud_cli",
                executable_names=["grok", "grok.exe"],
                install_url="https://x.ai/",
                auth_hint="Authenticate with your xAI account or API key.",
                supports_code=True,
            ),
            "ollama": ProviderDefinition(
                id="ollama",
                display_name="Ollama",
                category="local_runtime",
                executable_names=["ollama", "ollama.exe"],
                install_url="https://ollama.com/download",
                auth_hint="No cloud auth required. Download a model to begin.",
                supports_local_models=True,
                supports_code=True,
            ),
        }

    def list_provider_definitions(self) -> List[Dict[str, Any]]:
        return [asdict(provider) for provider in self.providers.values()]

    def detect_all(self) -> List[ProviderDetectionResult]:
        return [self.detect_provider(provider_id) for provider_id in self.providers]

    def detect_provider(self, provider_id: str) -> ProviderDetectionResult:
        provider = self.providers[provider_id]
        executable_path = self._locate_executable(provider_id, provider.executable_names)
        version = self._get_version(executable_path) if executable_path else None
        auth_configured = self._detect_auth(provider_id)

        if executable_path and auth_configured:
            recommended_action = "ready"
        elif executable_path and not auth_configured:
            recommended_action = "authenticate"
        else:
            recommended_action = "install"

        return ProviderDetectionResult(
            provider_id=provider.id,
            detected=bool(executable_path),
            executable_path=str(executable_path) if executable_path else None,
            version=version,
            auth_configured=auth_configured,
            recommended_action=recommended_action,
            install_url=provider.install_url,
            auth_hint=provider.auth_hint,
            capabilities={
                "supports_local_models": provider.supports_local_models,
                "supports_chat": provider.supports_chat,
                "supports_code": provider.supports_code,
                "supports_vision": provider.supports_vision,
            },
        )

    def get_hardware_profile(self) -> HardwareProfile:
        total_memory_gb = None
        gpu_hint = None

        try:
            import psutil  # type: ignore
            total_memory_gb = round(psutil.virtual_memory().total / (1024 ** 3), 1)
        except Exception:
            total_memory_gb = None

        if platform.system().lower() == "windows":
            gpu_hint = self._detect_gpu_hint_windows()

        return HardwareProfile(
            platform=platform.system(),
            architecture=platform.machine(),
            cpu_count=os.cpu_count() or 1,
            total_memory_gb=total_memory_gb,
            gpu_hint=gpu_hint,
        )

    def recommend_ollama_models(self) -> Dict[str, Any]:
        profile = self.get_hardware_profile()
        ram = profile.total_memory_gb or 0
        has_gpu = bool(profile.gpu_hint)

        if ram >= 32:
            models = [
                {"id": "qwen2.5-coder:14b", "reason": "Strong coding model for high-memory systems"},
                {"id": "llama3.1:8b", "reason": "General purpose balanced model"},
                {"id": "mistral:7b", "reason": "Fast local general model"},
            ]
        elif ram >= 16:
            models = [
                {"id": "llama3.1:8b", "reason": "Balanced default for midrange systems"},
                {"id": "qwen2.5-coder:7b", "reason": "Good code model for midrange systems"},
                {"id": "phi3:mini", "reason": "Fast and lighter backup option"},
            ]
        else:
            models = [
                {"id": "phi3:mini", "reason": "Lightweight default for lower-memory systems"},
                {"id": "gemma2:2b", "reason": "Small local model for constrained hardware"},
                {"id": "tinyllama", "reason": "Very lightweight fallback"},
            ]

        return {
            "hardware_profile": profile.to_dict(),
            "has_gpu_hint": has_gpu,
            "recommended_models": models,
        }

    def get_setup_plan(self) -> Dict[str, Any]:
        detections = self.detect_all()
        return {
            "providers": [item.to_dict() for item in detections],
            "ollama": self.recommend_ollama_models(),
            "installer_actions": [
                {
                    "provider_id": item.provider_id,
                    "action": item.recommended_action,
                    "detected": item.detected,
                }
                for item in detections
            ],
        }

    def _locate_executable(self, provider_id: str, executable_names: List[str]) -> Optional[Path]:
        for executable_name in executable_names:
            resolved = which(executable_name)
            if resolved:
                return Path(resolved)

        for candidate in DEFAULT_WINDOWS_INSTALL_PATHS.get(provider_id, []):
            if candidate and candidate.exists():
                return candidate

        return None

    def _get_version(self, executable_path: Optional[Path]) -> Optional[str]:
        if not executable_path:
            return None

        version_args = (["--version"], ["version"], ["-v"])
        for args in version_args:
            try:
                result = subprocess.run(
                    [str(executable_path), *args],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                output = (result.stdout or result.stderr or "").strip()
                if output:
                    return output.splitlines()[0][:200]
            except Exception:
                continue
        return None

    def _detect_auth(self, provider_id: str) -> bool:
        env_checks = {
            "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
            "codex": ["OPENAI_API_KEY"],
            "claude": ["ANTHROPIC_API_KEY"],
            "grok": ["XAI_API_KEY", "GROK_API_KEY"],
            "ollama": ["OLLAMA_HOST"],
        }
        return any(os.getenv(key) for key in env_checks.get(provider_id, []))

    def _detect_gpu_hint_windows(self) -> Optional[str]:
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name",
                ],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            output = (result.stdout or "").strip()
            if output:
                return output.splitlines()[0][:200]
        except Exception:
            return None
        return None


provider_cli_registry = ProviderCLIRegistry()
