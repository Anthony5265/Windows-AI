import os
import sys
import tempfile
import asyncio
import pytest

# Ensure project root on path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from windows_ai.plugins.builtin.audio_models.faster_whisper_plugin import plugin as faster_whisper_plugin

@pytest.mark.asyncio
async def test_initialize_and_models():
    ok = await faster_whisper_plugin.initialize()
    assert ok is True
    models = await faster_whisper_plugin.execute("get_models", {})
    assert models["success"] is True
    assert "models" in models["result"]

@pytest.mark.asyncio
async def test_stub_transcribe(monkeypatch):
    # Force fallback path to avoid heavy dependency/model download
    monkeypatch.setattr(faster_whisper_plugin, "_ensure_model", lambda *args, **kwargs: False)
    await faster_whisper_plugin.initialize()
    await faster_whisper_plugin.connect()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        res = await faster_whisper_plugin.execute("transcribe", {"audio_file": tmp_path, "model": "base"})
        assert res["success"] is True
        assert "result" in res
        assert "text" in res["result"]
    finally:
        await faster_whisper_plugin.shutdown()
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
