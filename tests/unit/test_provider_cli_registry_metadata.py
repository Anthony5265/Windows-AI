import pytest

from windows_ai.provider_cli_registry import ProviderCLIRegistry


def test_provider_definitions_include_target_examples():
    registry = ProviderCLIRegistry()
    definitions = {item["id"]: item for item in registry.list_provider_definitions()}

    assert definitions["codex"]["metadata"]["target_format"] == "cli:codex"
    assert definitions["codex"]["metadata"]["example_targets"] == ["cli:codex"]
    assert definitions["ollama"]["metadata"]["target_format"] == "ollama:<model>"
    assert "ollama:llama3.1:8b" in definitions["ollama"]["metadata"]["example_targets"]


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


def test_detect_provider_raises_value_error_for_unknown_provider():
    registry = ProviderCLIRegistry()

    with pytest.raises(ValueError, match="Unknown provider: unknown"):
        registry.detect_provider("unknown")
