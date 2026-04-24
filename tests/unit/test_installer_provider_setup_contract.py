from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "install" / "detect-ai-providers.ps1"


def _script_text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_installer_provider_preflight_emits_target_catalog_contract():
    script = _script_text()

    assert "function New-ProviderTargetCatalog" in script
    assert "target_catalog = $targetCatalog" in script
    assert "available_targets" in script
    assert "setup_required_targets" in script
    assert "default_target" in script
    assert "all_targets" in script


def test_installer_ollama_recommendations_are_directly_runnable_targets():
    script = _script_text()

    assert 'target = "ollama:$($_.id)"' in script
    assert "default_model_id = $defaultModelId" in script
    assert "default_target = $DefaultTarget" not in script
    assert "default_target = $defaultTarget" in script


def test_installer_treats_ollama_as_local_runtime_without_cloud_auth():
    script = _script_text()

    assert '-Id "ollama"' in script
    assert '-AuthEnvVars @()' in script
    assert '-AuthEnvVars @("OLLAMA_HOST")' not in script
    assert 'target_format = "ollama:<model>"' in script
    assert 'installer_strategy = "detect_or_install_runtime"' in script


def test_installer_uses_safe_dynamic_environment_lookup():
    script = _script_text()
    legacy_dynamic_env_lookup = "$" + "env:" + "$envVar"

    assert "[Environment]::GetEnvironmentVariable($envVar)" in script
    assert legacy_dynamic_env_lookup not in script
