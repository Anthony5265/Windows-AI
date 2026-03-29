import pytest
try:
    from backends import LocalBackend
except ImportError:
    pytest.skip("backends module not available in this environment", allow_module_level=True)
import importlib
from pathlib import Path


def test_export_import(tmp_path, monkeypatch):
    workflow_mod = importlib.import_module("automation.workflow")
    builder_mod = importlib.import_module("automation.builder")
    monkeypatch.setattr(workflow_mod, "WORKFLOW_DIR", tmp_path)
    monkeypatch.setattr(builder_mod, "WORKFLOW_DIR", tmp_path)

    backend = LocalBackend()
    builder = builder_mod.WorkflowBuilder(backend=backend, use_gui=False)
    a = builder.add_step("start")
    b = builder.add_step("end")
    builder.connect_steps(a, b)
    builder.export("sample")
    path = tmp_path / "sample.yml"
    assert path.exists()

    other = builder_mod.WorkflowBuilder(backend=backend, use_gui=False)
    other.import_file(path)
    assert b in other.workflow.steps[a].next


def test_suggest_uses_backend():
    from automation.builder import WorkflowBuilder

    backend = LocalBackend()
    builder = WorkflowBuilder(backend=backend, use_gui=False)
    suggestion = builder.suggest("test")
    assert suggestion.startswith("[local]")
