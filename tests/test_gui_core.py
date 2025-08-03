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
