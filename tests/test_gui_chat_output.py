from gui.core import GuiCore


class DummyModel:
    """Trivial model that prefixes messages."""

    def generate(self, prompt: str) -> str:
        return f"dummy:{prompt}"


def test_chat_with_default_simple_model():
    gui = GuiCore()
    assert gui.chat("hello") == "HELLO"


def test_chat_with_custom_model():
    gui = GuiCore(DummyModel())
    assert gui.chat("world") == "dummy:world"
