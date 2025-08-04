from gui.core import GuiCore


class DummyModel:
    def generate(self, prompt: str) -> str:
        return prompt.upper()


def test_gui_launch_and_chat():
    model = DummyModel()
    gui = GuiCore(model)
    assert gui.launch() is True
    assert gui.chat("hello") == "HELLO"
    logs = gui.get_logs()
    assert "GUI launched" in logs
    assert "chat: hello" in logs

def test_overlays_and_hotkeys():
    model = DummyModel()
    gui = GuiCore(model)
    overlay = gui.add_overlay("tip", "Hello")
    assert overlay.visible is False
    gui.show_overlay("tip")
    assert overlay.visible is True
    triggered = []

    def cb():
        triggered.append(True)

    gui.register_hotkey("Ctrl+H", cb)
    assert gui.handle_hotkey("Ctrl+H") is True
    assert triggered


def test_workflow_panel():
    model = DummyModel()
    gui = GuiCore(model)
    panel = gui.add_workflow_panel("n8n", "http://localhost:5678")
    assert panel.active is False
    assert gui.open_workflow("n8n") is True
    assert panel.active is True


def test_tooltips_and_walkthroughs():
    model = DummyModel()
    gui = GuiCore(model)

    tip = gui.add_tooltip("start", "Click to begin")
    assert tip.visible is False
    gui.show_tooltip("start")
    assert tip.visible is True
    gui.hide_tooltip("start")
    assert tip.visible is False

    walk = gui.add_walkthrough("intro", ["Step 1", "Step 2"])
    assert gui.start_walkthrough("intro") == "Step 1"
    assert gui.advance_walkthrough("intro") == "Step 2"
    assert gui.advance_walkthrough("intro") is None
