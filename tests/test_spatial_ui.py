import xr
from xr.spatial_ui import GestureVoiceController


def test_load_spatial_ui_no_runtime(monkeypatch):
    monkeypatch.setattr(xr, "load_runtime", lambda: None)
    assert xr.load_spatial_ui() is None


def test_load_spatial_ui_with_runtime(monkeypatch):
    class DummyRuntime:
        pass

    monkeypatch.setattr(xr, "load_runtime", lambda: DummyRuntime())
    controller = xr.load_spatial_ui()
    assert isinstance(controller, GestureVoiceController)

    called = []
    controller.bind_gesture("pinch", lambda: called.append("gesture"))
    controller.bind_voice("hello", lambda: called.append("voice"))
    controller.process_event({"type": "gesture", "name": "pinch"})
    controller.process_event({"type": "voice", "phrase": "hello"})
    assert called == ["gesture", "voice"]
