import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "install" / "provider-setup.schema.json"


def _schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def test_provider_setup_schema_is_valid_json_with_expected_identity():
    schema = _schema()

    assert schema["title"] == "Windows AI Provider Setup Plan"
    assert schema["$schema"].endswith("/draft/2020-12/schema")
    assert "Anthony5265/Windows-AI" in schema["$id"]


def test_provider_setup_schema_requires_core_installer_contract():
    schema = _schema()

    assert set(schema["required"]) == {"providers", "ollama", "installer_actions"}
    assert "target_catalog" in schema["properties"]
    assert "hardware" in schema["properties"]


def test_provider_setup_schema_defines_supported_provider_ids_and_actions():
    schema = _schema()
    provider = schema["$defs"]["provider"]
    action = schema["$defs"]["installerAction"]

    assert provider["properties"]["provider_id"]["enum"] == ["gemini", "codex", "claude", "grok", "ollama"]
    assert provider["properties"]["recommended_action"]["enum"] == ["ready", "authenticate", "install"]
    assert action["properties"]["action"]["enum"] == ["ready", "authenticate", "install"]


def test_provider_setup_schema_requires_runnable_ollama_targets():
    schema = _schema()
    ollama_model = schema["$defs"]["ollamaModel"]

    assert set(ollama_model["required"]) == {"id", "target"}
    assert ollama_model["properties"]["target"]["pattern"] == "^ollama:.+"


def test_provider_setup_schema_covers_target_catalog_groups():
    schema = _schema()
    catalog = schema["properties"]["target_catalog"]["properties"]
    target = schema["$defs"]["providerTarget"]

    assert {"available_targets", "setup_required_targets", "all_targets", "counts"}.issubset(catalog)
    assert set(target["required"]) == {"provider_id", "target", "recommended_action"}
    assert target["properties"]["recommended_action"]["enum"] == ["ready", "authenticate", "install"]
