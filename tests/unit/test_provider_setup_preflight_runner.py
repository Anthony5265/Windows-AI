from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "install" / "run-provider-preflight.ps1"
DOC = ROOT / "install" / "PROVIDER_SETUP.md"
VALIDATOR = ROOT / "install" / "validate-provider-setup.ps1"


def _runner_text() -> str:
    return RUNNER.read_text(encoding="utf-8")


def _validator_text() -> str:
    return VALIDATOR.read_text(encoding="utf-8")


def test_provider_preflight_runner_exists_and_calls_detection_and_validation():
    script = _runner_text()

    assert "detect-ai-providers.ps1" in script
    assert "validate-provider-setup.ps1" in script
    assert "-OutputPath $OutputPath" in script
    assert "-SetupPlanPath $OutputPath" in script


def test_provider_preflight_runner_has_installer_friendly_defaults():
    script = _runner_text()

    assert "$env:TEMP\\windows-ai-provider-setup.json" in script
    assert "Provider setup plan was not created" in script
    assert "SkipValidation" in script
    assert "Write-Output $OutputPath" in script


def test_provider_setup_docs_describe_target_catalog_contract():
    doc = DOC.read_text(encoding="utf-8")

    assert "target_catalog" in doc
    assert "cli:codex" in doc
    assert "ollama:phi3:mini" in doc
    assert "run-provider-preflight.ps1" in doc


def test_provider_setup_validator_checks_target_catalog_count_consistency():
    script = _validator_text()

    assert "target_catalog.counts is required" in script
    assert "target_catalog.counts.available" in script
    assert "target_catalog.counts.setup_required" in script
    assert "target_catalog.counts.total" in script
    assert "available_targets count" in script
    assert "setup_required_targets count" in script
    assert "all_targets count must equal available_targets plus setup_required_targets" in script


def test_provider_setup_validator_normalizes_missing_arrays_to_empty_lists():
    script = _validator_text()

    assert "function Get-ArrayValue" in script
    assert "if ($null -eq $Value) { return @() }" in script
    assert "Get-ArrayValue -Value $plan.target_catalog.available_targets" in script
    assert "Get-ArrayValue -Value $plan.target_catalog.setup_required_targets" in script
    assert "Get-ArrayValue -Value $plan.target_catalog.all_targets" in script
