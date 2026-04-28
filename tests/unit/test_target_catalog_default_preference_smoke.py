from windows_ai.provider_cli_registry import ProviderCLIRegistry, ProviderDetectionResult


def _detection(provider_id: str, action: str, detected: bool = True) -> ProviderDetectionResult:
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


def test_target_catalog_prefers_ready_target_for_default_selection():
    registry = ProviderCLIRegistry()
    catalog = registry.get_target_catalog(
        detections=[
            _detection("codex", action="ready", detected=True),
            _detection("ollama", action="install", detected=False),
        ],
        ollama_recommendations={
            "default_target": "ollama:phi3:mini",
            "recommended_models": [
                {"id": "phi3:mini", "target": "ollama:phi3:mini", "reason": "Fast local default"},
            ],
        },
    )

    assert catalog["default_target"] == "cli:codex"
    assert catalog["available_targets"][0]["target"] == "cli:codex"
    assert catalog["setup_required_targets"][0]["target"] == "ollama:phi3:mini"
