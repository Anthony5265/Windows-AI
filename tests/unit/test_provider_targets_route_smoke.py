import importlib
import sys
import types

from fastapi import FastAPI
from fastapi.testclient import TestClient


_MANAGER_SPECS = [
    ("ai_providers", "AIProvidersManager"),
    ("image_generation", "ImageGenerationManager"),
    ("audio_speech", "AudioSpeechManager"),
    ("video_generation", "VideoGenerationManager"),
    ("document_processing", "DocumentProcessingManager"),
    ("windows_automation", "WindowsAutomationManager"),
    ("browser_automation", "BrowserAutomationManager"),
    ("productivity", "ProductivityManager"),
    ("data_analysis", "DataAnalysisManager"),
    ("code_assistants", "CodeAssistantsManager"),
    ("translation", "TranslationManager"),
    ("search_engines", "SearchEnginesManager"),
    ("knowledge_graphs", "KnowledgeGraphManager"),
    ("threed_generation", "ThreeDGenerationManager"),
    ("music_generation", "MusicGenerationManager"),
    ("embeddings", "EmbeddingsManager"),
    ("vector_stores", "VectorStoresManager"),
    ("workflow_automation", "WorkflowAutomationManager"),
    ("email_services", "EmailServicesManager"),
    ("notifications", "NotificationsManager"),
    ("cloud_storage", "CloudStorageManager"),
    ("databases", "DatabaseManager"),
    ("monitoring", "MonitoringManager"),
    ("ai_agents", "AIAgentsManager"),
    ("security_scanning", "SecurityScanningManager"),
    ("content_moderation", "ContentModerationManager"),
    ("rag_pipeline", "RAGPipelineManager"),
    ("mlops", "MLOpsManager"),
    ("payments", "PaymentsManager"),
    ("social_media", "SocialMediaManager"),
    ("scheduling", "SchedulingManager"),
    ("crm", "CRMManager"),
    ("iot_hardware", "IoTHardwareManager"),
    ("computer_vision", "ComputerVisionManager"),
    ("healthcare_ai", "HealthcareAIManager"),
    ("legal_ai", "LegalAIManager"),
    ("education_ai", "EducationAIManager"),
    ("finance_ai", "FinanceAIManager"),
    ("scientific_ai", "ScientificAIManager"),
    ("accessibility_ai", "AccessibilityAIManager"),
    ("real_estate_ai", "RealEstateAIManager"),
    ("gaming_ai", "GamingAIManager"),
    ("conversational_ai", "ConversationalAIManager"),
    ("automation_robotics", "AutomationRoboticsManager"),
    ("biometrics_identity", "BiometricsIdentityManager"),
]


def _build_client(monkeypatch):
    for module_suffix, class_name in _MANAGER_SPECS:
        module_name = f"windows_ai.integrations.{module_suffix}"
        fake_module = types.ModuleType(module_name)
        setattr(fake_module, class_name, type(class_name, (), {}))
        monkeypatch.setitem(sys.modules, module_name, fake_module)

    monkeypatch.delitem(sys.modules, "windows_ai.integrations", raising=False)
    integrations_module = importlib.import_module("windows_ai.integrations")
    integrations_module = importlib.reload(integrations_module)

    app = FastAPI()
    app.include_router(integrations_module.router)
    return integrations_module, TestClient(app)


def test_provider_targets_route_smoke(monkeypatch):
    integrations_module, client = _build_client(monkeypatch)
    monkeypatch.setattr(
        integrations_module.provider_cli_registry,
        "get_target_catalog",
        lambda: {
            "default_target": "cli:codex",
            "available_targets": [{"provider_id": "codex", "target": "cli:codex"}],
            "setup_required_targets": [],
            "all_targets": [{"provider_id": "codex", "target": "cli:codex"}],
            "counts": {"available": 1, "setup_required": 0, "total": 1},
        },
    )

    response = client.get("/integrations/providers/targets")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["default_target"] == "cli:codex"
    assert body["available_targets"][0]["target"] == "cli:codex"
