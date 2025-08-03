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
