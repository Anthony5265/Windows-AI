import pytest

from windows_ai.provider_cli_registry import HardwareProfile, ProviderCLIRegistry, ProviderDetectionResult


def _detection(provider_id, action="ready", detected=True):
    return ProviderDetectionResult(
        provider_id=provider_id,
        detected=detected,
        executable_path=f"C:/Tools/{provider_id}.exe" if detected else None,
        version="1.0.0" if detected else None,
        auth_configured=action == "ready",
        recommended_action=action,
        install_url="https://example.invalid/install",
        auth_hint="Authenticate this provider",
        capabilities={"supports_chat": True},
        metadata={"target_format": f"cli:{provider_id}", "example_targets": [f"cli:{provider_id}"]},
    )


def test_provider_definitions_include_target_examples():
    registry = ProviderCLIRegistry()
    definitions = {item["id"]: item for item in registry.list_provider_definitions()}

    assert definitions["codex"]["metadata"]["target_format"] == "cli:codex"
    assert definitions["codex"]["metadata"]["example_targets"] == ["cli:codex"]
    assert definitions["ollama"]["metadata"]["target_format"] == "ollama:<model>"
    assert "ollama:llama3.1:8b" in definitions["ollama"]["metadata"]["example_targets"]


def test_detect_provider_includes_target_metadata(monkeypatch):
    registry = ProviderCLIRegistry()
    monkeypatch.setattr(registry, "_locate_executable", lambda provider_id, executable_names: None)

    detection = registry.detect_provider("codex")

    assert detection.metadata["target_format"] == "cli:codex"
    assert detection.metadata["example_targets"] == ["cli:codex"]


def test_ollama_recommendations_include_direct_target_strings(monkeypatch):
    registry = ProviderCLIRegistry()
    monkeypatch.setattr(
        registry,
        "get_hardware_profile",
        lambda: HardwareProfile(
            platform="Windows",
            architecture="AMD64",
            cpu_count=16,
            total_memory_gb=16.0,
            gpu_hint="NVIDIA GeForce RTX 4070",
        ),
    )

    recommendations = registry.recommend_ollama_models()

    assert recommendations["recommended_models"]
    first_model = recommendations["recommended_models"][0]
    assert first_model["target"] == f"ollama:{first_model['id']}"


def test_setup_plan_includes_provider_definitions_and_actions(monkeypatch):
    registry = ProviderCLIRegistry()

    monkeypatch.setattr(registry, "detect_all", lambda: [])
    monkeypatch.setattr(
        registry,
        "recommend_ollama_models",
        lambda: {"hardware_profile": {}, "has_gpu_hint": False, "recommended_models": []},
    )

    setup_plan = registry.get_setup_plan()

    assert "definitions" in setup_plan
    assert {item["id"] for item in setup_plan["definitions"]} == {"gemini", "codex", "claude", "grok", "ollama"}
    assert setup_plan["providers"] == []
    assert setup_plan["installer_actions"] == []


def test_target_catalog_groups_ready_and_setup_required_targets():
    registry = ProviderCLIRegistry()
    detections = [
        _detection("codex", action="ready", detected=True),
        _detection("gemini", action="authenticate", detected=True),
        _detection("ollama", action="ready", detected=True),
    ]
    ollama = {
        "default_target": "ollama:phi3:mini",
        "recommended_models": [
            {"id": "phi3:mini", "target": "ollama:phi3:mini", "reason": "Fast local default"},
        ],
    }

    catalog = registry.get_target_catalog(detections=detections, ollama_recommendations=ollama)

    ready_targets = {item["target"] for item in catalog["available_targets"]}
    setup_targets = {item["target"] for item in catalog["setup_required_targets"]}
    assert "cli:codex" in ready_targets
    assert "ollama:phi3:mini" in ready_targets
    assert "cli:gemini" in setup_targets
    assert catalog["default_target"] == "ollama:phi3:mini"
    assert catalog["counts"] == {"available": 2, "setup_required": 1, "total": 3}


def test_setup_plan_includes_target_catalog(monkeypatch):
    registry = ProviderCLIRegistry()
    monkeypatch.setattr(
        registry,
        "detect_all",
        lambda: [_detection("codex", action="ready", detected=True)],
    )
    monkeypatch.setattr(
        registry,
        "recommend_ollama_models",
        lambda: {
            "hardware_profile": {},
            "has_gpu_hint": False,
            "default_model_id": "phi3:mini",
            "default_target": "ollama:phi3:mini",
            "recommended_models": [
                {"id": "phi3:mini", "target": "ollama:phi3:mini", "reason": "Fast local default"},
            ],
        },
    )

    setup_plan = registry.get_setup_plan()

    assert "target_catalog" in setup_plan
    assert setup_plan["target_catalog"]["available_targets"][0]["target"] == "cli:codex"
    assert setup_plan["target_catalog"]["default_target"] == "ollama:phi3:mini"


def test_detect_provider_raises_value_error_for_unknown_provider():
    registry = ProviderCLIRegistry()

    with pytest.raises(ValueError, match="Unknown provider: unknown"):
        registry.detect_provider("unknown")
