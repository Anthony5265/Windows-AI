import pytest

from windows_ai.provider_cli_registry import ProviderCLIRegistry


def test_provider_definitions_include_target_examples():
    registry = ProviderCLIRegistry()
    definitions = {item["id"]: item for item in registry.list_provider_definitions()}

    assert definitions["codex"]["metadata"]["target_format"] == "cli:codex"
    assert definitions["codex"]["metadata"]["example_targets"] == ["cli:codex"]
    assert definitions["ollama"]["metadata"]["target_format"] == "ollama:<model>"
    assert "ollama:llama3.1:8b" in definitions["ollama"]["metadata"]["example_targets"]


def test_detect_provider_raises_value_error_for_unknown_provider():
    registry = ProviderCLIRegistry()

    with pytest.raises(ValueError, match="Unknown provider: unknown"):
        registry.detect_provider("unknown")
