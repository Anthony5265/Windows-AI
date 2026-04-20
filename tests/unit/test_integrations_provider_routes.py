import importlib
import sys
import types

from fastapi import FastAPI
from fastapi.testclient import TestClient

import windows_ai.provider_cli_registry as provider_cli_registry_module


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


def _build_integrations_client(monkeypatch):
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


def test_integrations_status_route_lists_stubbed_managers(monkeypatch):
    integrations_module, client = _build_integrations_client(monkeypatch)

    response = client.get("/integrations/status")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["count"] == len(integrations_module.__all__)
    assert "AIProvidersManager" in body["managers"]
    assert "BiometricsIdentityManager" in body["managers"]


def test_provider_definitions_route_uses_registry(monkeypatch):
    integrations_module, client = _build_integrations_client(monkeypatch)

    monkeypatch.setattr(
        integrations_module.provider_cli_registry,
        "providers",
        {"codex": object(), "ollama": object()},
    )
    monkeypatch.setattr(
        integrations_module.provider_cli_registry,
        "list_provider_definitions",
        lambda: [
            {"id": "codex", "display_name": "Codex CLI"},
            {"id": "ollama", "display_name": "Ollama"},
        ],
    )

    response = client.get("/integrations/providers/definitions")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["count"] == 2
    assert [provider["id"] for provider in body["providers"]] == ["codex", "ollama"]


def test_provider_detect_routes_return_success_and_unknown_error(monkeypatch):
    integrations_module, client = _build_integrations_client(monkeypatch)

    detection = provider_cli_registry_module.ProviderDetectionResult(
        provider_id="codex",
        detected=True,
        executable_path="/tmp/codex",
        version="codex 1.2.3",
        auth_configured=False,
        recommended_action="authenticate",
        install_url="https://platform.openai.com/",
        auth_hint="Authenticate with your OpenAI account or API key.",
        capabilities={"supports_code": True},
    )

    monkeypatch.setattr(integrations_module.provider_cli_registry, "providers", {"codex": object()})
    monkeypatch.setattr(integrations_module.provider_cli_registry, "detect_all", lambda: [detection])
    monkeypatch.setattr(integrations_module.provider_cli_registry, "detect_provider", lambda provider_id: detection)

    list_response = client.get("/integrations/providers/detect")
    assert list_response.status_code == 200
    list_body = list_response.json()
    assert list_body["status"] == "success"
    assert list_body["count"] == 1
    assert list_body["providers"][0]["provider_id"] == "codex"

    single_response = client.get("/integrations/providers/detect/codex")
    assert single_response.status_code == 200
    single_body = single_response.json()
    assert single_body["status"] == "success"
    assert single_body["provider"]["provider_id"] == "codex"
    assert single_body["provider"]["recommended_action"] == "authenticate"

    unknown_response = client.get("/integrations/providers/detect/unknown")
    assert unknown_response.status_code == 200
    unknown_body = unknown_response.json()
    assert unknown_body["status"] == "error"
    assert unknown_body["message"] == "Unknown provider: unknown"


def test_provider_hardware_recommendations_and_setup_plan_routes(monkeypatch):
    integrations_module, client = _build_integrations_client(monkeypatch)

    hardware = provider_cli_registry_module.HardwareProfile(
        platform="Windows",
        architecture="AMD64",
        cpu_count=16,
        total_memory_gb=32.0,
        gpu_hint="NVIDIA GeForce RTX 4070",
    )

    monkeypatch.setattr(integrations_module.provider_cli_registry, "get_hardware_profile", lambda: hardware)
    monkeypatch.setattr(
        integrations_module.provider_cli_registry,
        "recommend_ollama_models",
        lambda: {
            "hardware_profile": hardware.to_dict(),
            "has_gpu_hint": True,
            "recommended_models": [
                {"id": "qwen2.5-coder:14b", "reason": "Strong coding model for high-memory systems"}
            ],
        },
    )
    monkeypatch.setattr(
        integrations_module.provider_cli_registry,
        "get_setup_plan",
        lambda: {
            "providers": [{"provider_id": "ollama", "recommended_action": "ready"}],
            "ollama": {
                "hardware_profile": hardware.to_dict(),
                "has_gpu_hint": True,
                "recommended_models": [
                    {"id": "qwen2.5-coder:14b", "reason": "Strong coding model for high-memory systems"}
                ],
            },
            "installer_actions": [{"provider_id": "ollama", "action": "ready", "detected": True}],
        },
    )

    hardware_response = client.get("/integrations/providers/hardware")
    assert hardware_response.status_code == 200
    hardware_body = hardware_response.json()
    assert hardware_body["status"] == "success"
    assert hardware_body["hardware"]["gpu_hint"] == "NVIDIA GeForce RTX 4070"

    recommendations_response = client.get("/integrations/providers/ollama/recommendations")
    assert recommendations_response.status_code == 200
    recommendations_body = recommendations_response.json()
    assert recommendations_body["status"] == "success"
    assert recommendations_body["has_gpu_hint"] is True
    assert recommendations_body["recommended_models"][0]["id"] == "qwen2.5-coder:14b"

    setup_response = client.get("/integrations/providers/setup-plan")
    assert setup_response.status_code == 200
    setup_body = setup_response.json()
    assert setup_body["status"] == "success"
    assert setup_body["providers"][0]["provider_id"] == "ollama"
    assert setup_body["installer_actions"][0]["action"] == "ready"
