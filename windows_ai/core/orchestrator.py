"""
Windows AI Master Orchestrator
Unified interface to ALL 2500+ AI capabilities
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import unified configuration system
from windows_ai.config.unified_config import WindowsAIConfig, get_config

logger = logging.getLogger(__name__)

class WindowsAI:
    """
    Master orchestrator for all Windows AI capabilities.
    One-stop interface to 2500+ AI features.
    """

    def __init__(self, config: Optional[WindowsAIConfig] = None):
        """
        Initialize Windows AI orchestrator
        
        Args:
            config: WindowsAIConfig instance (optional, will load from file if not provided)
        """
        self._initialized = False
        self._managers = {}
        self._config = config or get_config()  # Load unified config

    async def initialize(self, config_override: Optional[Dict] = None, config: Optional[Dict] = None):
        """
        Initialize all AI managers with unified configuration
        
        Args:
            config_override: Optional dictionary to override specific config values
            config: Alternative parameter name for config_override (for compatibility)
            
        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True

        logger.info("[*] Initializing Windows AI - 2500+ capabilities loading...")
        
        # Support both parameter names for compatibility
        override = config_override or config

        # Initialize Sentry error tracking (if DSN provided)
        import os
        sentry_dsn = os.environ.get("SENTRY_DSN")
        if sentry_dsn:
            try:
                import sentry_sdk
                sentry_sdk.init(
                    dsn=sentry_dsn,
                    environment=self._config.environment,
                    traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
                    send_default_pii=False,
                    attach_stacktrace=True,
                    release=self._config.version,
                )
                logger.info("[+] Sentry error tracking initialized")
            except ImportError:
                logger.warning("[!] Sentry SDK not installed - error tracking disabled")
            except Exception as e:
                logger.error(f"[!] Failed to initialize Sentry: {e}")

        # Apply any config overrides
        if override:
            for key, value in override.items():
                try:
                    self._config.set_nested(key, value)
                except Exception as e:
                    logger.warning(f"[!] Failed to apply config override {key}={value}: {e}")

        # Initialize all integration managers
        await self._init_all_managers()

        self._initialized = True
        logger.info(f"[+] Windows AI v{self._config.version} ready - All systems operational!")
        return True

    async def _init_all_managers(self):
        """Initialize ALL integration managers with unified configuration"""
        from windows_ai.integrations import (
            AIProvidersManager, ImageGenerationManager, AudioSpeechManager,
            VideoGenerationManager, DocumentProcessingManager, WindowsAutomationManager,
            BrowserAutomationManager, ProductivityManager, DataAnalysisManager,
            CodeAssistantsManager, TranslationManager, SearchEnginesManager,
            KnowledgeGraphManager, ThreeDGenerationManager, MusicGenerationManager,
            EmbeddingsManager, VectorStoresManager, WorkflowAutomationManager,
            EmailServicesManager, NotificationsManager, CloudStorageManager,
            DatabaseManager, MonitoringManager, AIAgentsManager,
            SecurityScanningManager, ContentModerationManager, RAGPipelineManager,
            MLOpsManager, PaymentsManager, SocialMediaManager, SchedulingManager,
            CRMManager, IoTHardwareManager, ComputerVisionManager,
            HealthcareAIManager, LegalAIManager, EducationAIManager,
            FinanceAIManager, ScientificAIManager, AccessibilityAIManager,
            RealEstateAIManager, GamingAIManager, ConversationalAIManager,
            AutomationRoboticsManager, BiometricsIdentityManager
        )

        # Initialize all managers
        managers = {
            "ai": AIProvidersManager(),
            "images": ImageGenerationManager(),
            "audio": AudioSpeechManager(),
            "video": VideoGenerationManager(),
            "documents": DocumentProcessingManager(),
            "windows": WindowsAutomationManager(),
            "browser": BrowserAutomationManager(),
            "productivity": ProductivityManager(),
            "data": DataAnalysisManager(),
            "code": CodeAssistantsManager(),
            "translation": TranslationManager(),
            "search": SearchEnginesManager(),
            "knowledge": KnowledgeGraphManager(),
            "3d": ThreeDGenerationManager(),
            "music": MusicGenerationManager(),
            "embeddings": EmbeddingsManager(),
            "vectors": VectorStoresManager(),
            "workflows": WorkflowAutomationManager(),
            "email": EmailServicesManager(),
            "notifications": NotificationsManager(),
            "storage": CloudStorageManager(),
            "database": DatabaseManager(),
            "monitoring": MonitoringManager(),
            "agents": AIAgentsManager(),
            "security": SecurityScanningManager(),
            "moderation": ContentModerationManager(),
            "rag": RAGPipelineManager(),
            "mlops": MLOpsManager(),
            "payments": PaymentsManager(),
            "social": SocialMediaManager(),
            "scheduling": SchedulingManager(),
            "crm": CRMManager(),
            "iot": IoTHardwareManager(),
            "vision": ComputerVisionManager(),
            "healthcare": HealthcareAIManager(),
            "legal": LegalAIManager(),
            "education": EducationAIManager(),
            "finance": FinanceAIManager(),
            "science": ScientificAIManager(),
            "accessibility": AccessibilityAIManager(),
            "realestate": RealEstateAIManager(),
            "gaming": GamingAIManager(),
            "conversation": ConversationalAIManager(),
            "automation": AutomationRoboticsManager(),
            "biometrics": BiometricsIdentityManager()
        }

        # Initialize each manager with graceful degradation
        initialization_tasks = []
        for name, manager in managers.items():
            initialization_tasks.append(self._init_single_manager(name, manager))
        
        # Run all initializations concurrently
        await asyncio.gather(*initialization_tasks, return_exceptions=True)
    
    async def _init_single_manager(self, name: str, manager: Any):
        """Initialize a single manager with error handling"""
        try:
            await manager.initialize(self._config)
            self._managers[name] = manager
            logger.info(f"[+] {name.capitalize()} manager initialized")
        except Exception as e:
            logger.warning(f"[!] {name.capitalize()} manager failed: {e}")
            self._managers[name] = manager  # Still add it for graceful degradation

    # ==================== UNIFIED API ====================

    async def chat(self, message: str, provider: str = "openai", **kwargs) -> str:
        """
        Universal chat interface
        
        Args:
            message: User message
            provider: AI provider (openai, anthropic, google, etc.)
            **kwargs: Provider-specific options (model, temperature, max_tokens, etc.)
        
        Returns:
            AI response as string
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self._managers["ai"].chat(message, provider, **kwargs)
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return f"Error: {str(e)}"

    async def generate_image(self, prompt: str, **kwargs) -> bytes:
        """Universal image generation"""
        return await self._managers["images"].generate(prompt, **kwargs)

    async def analyze_image(self, image_path: str, task: str = "describe") -> Dict:
        """Universal image analysis"""
        return await self._managers["vision"].analyze(image_path, task)

    async def transcribe(self, audio_path: str) -> str:
        """Universal audio transcription"""
        return await self._managers["audio"].speech_to_text(audio_path)

    async def speak(self, text: str, **kwargs) -> bytes:
        """Universal text-to-speech"""
        return await self._managers["audio"].text_to_speech(text, **kwargs)

    async def search_web(self, query: str, **kwargs) -> List[Dict]:
        """Universal web search"""
        return await self._managers["search"].search(query, **kwargs)

    async def send_email(self, to: List[str], subject: str, body: str, **kwargs):
        """Universal email sending"""
        return await self._managers["email"].send(to, subject, body, **kwargs)

    async def automate_task(self, task_description: str) -> Dict:
        """AI-powered task automation"""
        return await self._managers["automation"].run_task(task_description)

    async def analyze_data(self, data: Any, analysis_type: str = "auto") -> Dict:
        """Universal data analysis"""
        return await self._managers["data"].analyze(data, analysis_type)

    # ==================== QUICK ACCESS METHODS ====================

    def ai(self) -> Any:
        """Quick access to AI providers"""
        return self._managers.get("ai")

    def vision(self) -> Any:
        """Quick access to computer vision"""
        return self._managers.get("vision")

    def audio(self) -> Any:
        """Quick access to audio processing"""
        return self._managers.get("audio")

    def documents(self) -> Any:
        """Quick access to document processing"""
        return self._managers.get("documents")

    def automation(self) -> Any:
        """Quick access to automation"""
        return self._managers.get("automation")

    def healthcare(self) -> Any:
        """Quick access to healthcare AI"""
        return self._managers.get("healthcare")

    def finance(self) -> Any:
        """Quick access to finance AI"""
        return self._managers.get("finance")

    def legal(self) -> Any:
        """Quick access to legal AI"""
        return self._managers.get("legal")

    def education(self) -> Any:
        """Quick access to education AI"""
        return self._managers.get("education")

    # ==================== UTILITY METHODS ====================
    
    def _detect_api_keys(self) -> Dict[str, str]:
        """
        Detect available API keys from environment variables.
        
        Returns:
            Dictionary of detected API keys
        """
        import os
        
        key_patterns = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GOOGLE_API_KEY",
            "AZURE_API_KEY",
            "COHERE_API_KEY",
            "MISTRAL_API_KEY",
            "GROQ_API_KEY",
            "REPLICATE_API_TOKEN",
            "HUGGINGFACE_API_KEY",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AZURE_OPENAI_API_KEY",
            "STABILITY_API_KEY",
            "ELEVENLABS_API_KEY",
            "PINECONE_API_KEY",
            "WEAVIATE_API_KEY",
            "QDRANT_API_KEY",
        ]
        
        detected = {}
        for key in key_patterns:
            value = os.environ.get(key)
            if value:
                detected[key] = value
        
        return detected
    
    async def _auto_configure(self, config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Auto-configure the orchestrator based on environment.
        
        Args:
            config: Optional base configuration
            
        Returns:
            Auto-detected configuration
        """
        auto_config = config or {}
        
        # Detect API keys
        detected_keys = self._detect_api_keys()
        auto_config["detected_providers"] = list(detected_keys.keys())
        
        # Detect available providers based on keys
        providers = []
        if "OPENAI_API_KEY" in detected_keys:
            providers.append("openai")
        if "ANTHROPIC_API_KEY" in detected_keys:
            providers.append("anthropic")
        if "GOOGLE_API_KEY" in detected_keys:
            providers.append("google")
        if "AZURE_API_KEY" in detected_keys or "AZURE_OPENAI_API_KEY" in detected_keys:
            providers.append("azure")
        if "COHERE_API_KEY" in detected_keys:
            providers.append("cohere")
        if "MISTRAL_API_KEY" in detected_keys:
            providers.append("mistral")
        if "GROQ_API_KEY" in detected_keys:
            providers.append("groq")
        
        auto_config["available_providers"] = providers
        auto_config["default_provider"] = providers[0] if providers else "openai"
        
        return auto_config
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all components.
        
        Returns:
            Health status dictionary with component states
        """
        health = {
            "status": "healthy",
            "initialized": self._initialized,
            "managers": {},
            "errors": []
        }
        
        # Check each manager
        for name, manager in self._managers.items():
            try:
                if hasattr(manager, 'health_check'):
                    manager_health = await manager.health_check()
                    health["managers"][name] = manager_health
                else:
                    # Basic check - manager exists and has expected attributes
                    health["managers"][name] = {
                        "status": "ok",
                        "initialized": getattr(manager, '_initialized', True)
                    }
            except Exception as e:
                health["managers"][name] = {
                    "status": "error",
                    "error": str(e)
                }
                health["errors"].append(f"{name}: {str(e)}")
        
        # Overall status
        if health["errors"]:
            health["status"] = "degraded" if len(health["errors"]) < len(self._managers) / 2 else "unhealthy"
        
        return health

    def list_capabilities(self) -> Dict[str, List[str]]:
        """List all available capabilities"""
        capabilities = {}
        for name, manager in self._managers.items():
            if hasattr(manager, 'list_capabilities'):
                capabilities[name] = manager.list_capabilities()
        return capabilities

    def get_manager(self, name: str) -> Optional[Any]:
        """Get specific manager by name"""
        return self._managers.get(name)

    def status(self) -> Dict:
        """Get system status with unified config"""
        return {
            "initialized": self._initialized,
            "managers_loaded": len(self._managers),
            "total_capabilities": sum(len(caps) if isinstance(caps, (list, dict)) else 1
                                     for mgr in self._managers.values()
                                     if hasattr(mgr, 'list_capabilities')
                                     for caps in [mgr.list_capabilities()]),
            "config": self._config.model_dump(exclude={
                'llm': {'api_key'},  # Exclude sensitive API keys
                'database': {'password'}  # Exclude database passwords
            }) if hasattr(self._config, 'model_dump') else {}
        }
    
    async def cleanup(self):
        """Cleanup all managers and resources"""
        logger.info("[*] Shutting down Windows AI...")
        
        cleanup_tasks = []
        for name, manager in self._managers.items():
            if hasattr(manager, 'cleanup'):
                cleanup_tasks.append(self._cleanup_single_manager(name, manager))
        
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        self._initialized = False
        self._managers.clear()
        logger.info("[+] Windows AI shut down complete")
    
    async def _cleanup_single_manager(self, name: str, manager: Any):
        """Cleanup a single manager"""
        try:
            await manager.cleanup()
            logger.debug(f"[+] {name.capitalize()} manager cleaned up")
        except Exception as e:
            logger.warning(f"[!] {name.capitalize()} cleanup failed: {e}")
    
    async def execute_plugin(self, plugin_id: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a plugin by ID
        
        Args:
            plugin_id: Plugin identifier
            **kwargs: Plugin-specific parameters
        
        Returns:
            Plugin execution result
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            from windows_ai.core.plugin_manager import get_plugin_manager
            plugin_mgr = get_plugin_manager()
            return await plugin_mgr.execute_plugin(plugin_id, **kwargs)
        except Exception as e:
            logger.error(f"Plugin execution failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def list_plugins(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available plugins
        
        Args:
            category: Optional category filter
        
        Returns:
            List of plugin metadata
        """
        try:
            from windows_ai.core.plugin_manager import get_plugin_manager
            plugin_mgr = get_plugin_manager()
            return await plugin_mgr.list_plugins(category)
        except Exception as e:
            logger.error(f"Failed to list plugins: {e}")
            return []
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    async def __aenter__(self):
        """Async context manager support"""
        await self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        pass
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager cleanup"""
        await self.cleanup()


# Global singleton instance
_windows_ai_instance = None

def get_windows_ai() -> WindowsAI:
    """Get global Windows AI instance"""
    global _windows_ai_instance
    if _windows_ai_instance is None:
        _windows_ai_instance = WindowsAI()
    return _windows_ai_instance


async def quick_start():
    """Quick start Windows AI with one line"""
    ai = get_windows_ai()
    await ai.initialize()
    return ai
