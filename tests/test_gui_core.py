from gui.core import GuiCore


class DummyModel:
    def generate(self, prompt: str) -> str:
        return prompt.upper()


def test_gui_launch_and_chat():
    """GUI should launch and echo chat messages."""
    model = DummyModel()
    gui = GuiCore(model)
    assert gui.launch() is True
    assert gui.chat("hello") == "HELLO"
    logs = gui.get_logs()
    assert "GUI launched" in logs
    assert "chat: hello" in logs

def test_overlays_and_hotkeys():
    """Overlays toggle visibility and hotkeys trigger callbacks."""
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
    """Workflow panels open external tools in the GUI."""
    model = DummyModel()
    gui = GuiCore(model)
    panel = gui.add_workflow_panel("FlowTool", "http://localhost:5678")
    assert panel.active is False
    assert gui.open_workflow("FlowTool") is True
    assert panel.active is True


def test_tooltips_and_walkthroughs():
    """Tooltips and walkthroughs show stepwise guidance."""
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
