from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"


def _workflow_text() -> str:
    return RELEASE_WORKFLOW.read_text(encoding="utf-8")


def test_release_workflow_validates_provider_preflight_before_building_installer():
    workflow = _workflow_text()

    assert "Validate provider setup preflight" in workflow
    assert ".\\install\\run-provider-preflight.ps1" in workflow
    assert ".\\install\\validate-provider-setup.ps1" in workflow
    assert workflow.index("Validate provider setup preflight") < workflow.index("Build installer")


def test_release_changelog_mentions_provider_setup_preflight():
    workflow = _workflow_text()

    assert "Provider setup preflight validation for CLI and Ollama detection" in workflow
    assert "Hardware-aware Ollama target catalog for first-run setup" in workflow
