"""Lazy Manager Loader for Windows AI.

Provides on-demand loading of integration managers. Instead of initializing
all 45 managers at startup, managers are instantiated and initialized only
when first accessed. This reduces startup time and idle memory usage.

Usage
-----
In the orchestrator, replace direct manager access with the lazy loader::

    loader = LazyManagerLoader(config)
    ai_manager = await loader.get("ai")  # Initialized on first access
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Dict, Optional, Type

from windows_ai.config.unified_config import WindowsAIConfig

logger = logging.getLogger(__name__)


# Registry mapping manager short names to their import paths + class names
MANAGER_REGISTRY: Dict[str, tuple] = {
    "ai": ("windows_ai.integrations.ai_providers", "AIProvidersManager"),
    "images": ("windows_ai.integrations.image_generation", "ImageGenerationManager"),
    "audio": ("windows_ai.integrations.audio_speech", "AudioSpeechManager"),
    "video": ("windows_ai.integrations.video_generation", "VideoGenerationManager"),
    "documents": ("windows_ai.integrations.document_processing", "DocumentProcessingManager"),
    "windows": ("windows_ai.integrations.windows_automation", "WindowsAutomationManager"),
    "browser": ("windows_ai.integrations.browser_automation", "BrowserAutomationManager"),
    "productivity": ("windows_ai.integrations.productivity", "ProductivityManager"),
    "data": ("windows_ai.integrations.data_analysis", "DataAnalysisManager"),
    "code": ("windows_ai.integrations.code_assistants", "CodeAssistantsManager"),
    "translation": ("windows_ai.integrations.translation", "TranslationManager"),
    "search": ("windows_ai.integrations.search_engines", "SearchEnginesManager"),
    "knowledge": ("windows_ai.integrations.knowledge_graph", "KnowledgeGraphManager"),
    "3d": ("windows_ai.integrations.three_d_generation", "ThreeDGenerationManager"),
    "music": ("windows_ai.integrations.music_generation", "MusicGenerationManager"),
    "embeddings": ("windows_ai.integrations.embeddings", "EmbeddingsManager"),
    "vectors": ("windows_ai.integrations.vector_stores", "VectorStoresManager"),
    "workflows": ("windows_ai.integrations.workflow_automation", "WorkflowAutomationManager"),
    "email": ("windows_ai.integrations.email_services", "EmailServicesManager"),
    "notifications": ("windows_ai.integrations.notifications", "NotificationsManager"),
    "storage": ("windows_ai.integrations.cloud_storage", "CloudStorageManager"),
    "database": ("windows_ai.integrations.databases", "DatabaseManager"),
    "monitoring": ("windows_ai.integrations.monitoring", "MonitoringManager"),
    "agents": ("windows_ai.integrations.ai_agents", "AIAgentsManager"),
    "security": ("windows_ai.integrations.security_scanning", "SecurityScanningManager"),
    "moderation": ("windows_ai.integrations.content_moderation", "ContentModerationManager"),
    "rag": ("windows_ai.integrations.rag_pipeline", "RAGPipelineManager"),
    "mlops": ("windows_ai.integrations.mlops", "MLOpsManager"),
    "payments": ("windows_ai.integrations.payments", "PaymentsManager"),
    "social": ("windows_ai.integrations.social_media", "SocialMediaManager"),
    "scheduling": ("windows_ai.integrations.scheduling", "SchedulingManager"),
    "crm": ("windows_ai.integrations.crm", "CRMManager"),
    "iot": ("windows_ai.integrations.iot_hardware", "IoTHardwareManager"),
    "vision": ("windows_ai.integrations.computer_vision", "ComputerVisionManager"),
    "healthcare": ("windows_ai.integrations.healthcare_ai", "HealthcareAIManager"),
    "legal": ("windows_ai.integrations.legal_ai", "LegalAIManager"),
    "education": ("windows_ai.integrations.education_ai", "EducationAIManager"),
    "finance": ("windows_ai.integrations.finance_ai", "FinanceAIManager"),
    "science": ("windows_ai.integrations.scientific_ai", "ScientificAIManager"),
    "accessibility": ("windows_ai.integrations.accessibility_ai", "AccessibilityAIManager"),
    "realestate": ("windows_ai.integrations.real_estate_ai", "RealEstateAIManager"),
    "gaming": ("windows_ai.integrations.gaming_ai", "GamingAIManager"),
    "conversation": ("windows_ai.integrations.conversational_ai", "ConversationalAIManager"),
    "automation": ("windows_ai.integrations.automation_robotics", "AutomationRoboticsManager"),
    "biometrics": ("windows_ai.integrations.biometrics_identity", "BiometricsIdentityManager"),
}


class LazyManagerLoader:
    """Load integration managers on-demand instead of at startup.

    Attributes
    ----------
    config : WindowsAIConfig
        Configuration passed to each manager's ``initialize()`` method.
    """

    def __init__(self, config: Optional[WindowsAIConfig] = None) -> None:
        self._config = config
        self._instances: Dict[str, Any] = {}
        self._initialized: Dict[str, bool] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._load_times: Dict[str, float] = {}

    async def get(self, name: str) -> Any:
        """Get a manager by name, initializing it if necessary.

        Parameters
        ----------
        name : str
            Short name of the manager (e.g. ``"ai"``, ``"audio"``).

        Returns
        -------
        The initialized manager instance.

        Raises
        ------
        KeyError
            If *name* is not in the registry.
        """
        if name in self._initialized and self._initialized[name]:
            return self._instances[name]

        # Create per-name lock to prevent double init
        if name not in self._locks:
            self._locks[name] = asyncio.Lock()

        async with self._locks[name]:
            # Double-check after acquiring lock
            if name in self._initialized and self._initialized[name]:
                return self._instances[name]

            return await self._load_manager(name)

    async def _load_manager(self, name: str) -> Any:
        """Import, instantiate, and initialize a manager."""
        if name not in MANAGER_REGISTRY:
            raise KeyError(f"Unknown manager: {name}. Available: {sorted(MANAGER_REGISTRY.keys())}")

        module_path, class_name = MANAGER_REGISTRY[name]
        start = time.time()

        try:
            import importlib
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            instance = cls()
            await instance.initialize(self._config)

            self._instances[name] = instance
            self._initialized[name] = True
            self._load_times[name] = time.time() - start

            logger.info(
                "Lazy-loaded manager '%s' (%s) in %.3fs",
                name, class_name, self._load_times[name],
            )
            return instance

        except Exception as e:
            logger.warning("Failed to lazy-load manager '%s': %s", name, e)
            # Create a stub instance for graceful degradation
            try:
                import importlib
                module = importlib.import_module(module_path)
                cls = getattr(module, class_name)
                instance = cls()
                self._instances[name] = instance
                self._initialized[name] = False
                return instance
            except Exception:
                raise

    def is_loaded(self, name: str) -> bool:
        """Check if a manager has been loaded and initialized."""
        return self._initialized.get(name, False)

    @property
    def loaded_managers(self) -> Dict[str, bool]:
        """Return which managers are currently loaded."""
        return dict(self._initialized)

    @property
    def available_managers(self) -> list:
        """List all registered manager names."""
        return sorted(MANAGER_REGISTRY.keys())

    def stats(self) -> Dict[str, Any]:
        """Return lazy loader statistics."""
        return {
            "total_available": len(MANAGER_REGISTRY),
            "total_loaded": sum(1 for v in self._initialized.values() if v),
            "total_failed": sum(1 for v in self._initialized.values() if not v),
            "load_times": dict(self._load_times),
            "memory_saved_percent": round(
                (1 - sum(1 for v in self._initialized.values() if v) / len(MANAGER_REGISTRY)) * 100,
                1,
            ) if MANAGER_REGISTRY else 0,
        }
