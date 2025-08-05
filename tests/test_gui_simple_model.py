from gui.core import GuiCore
from gui.simple_model import SimpleModel


def test_chat_returns_simple_model_output():
    gui = GuiCore()
    prompt = "hello"
    expected = SimpleModel().generate(prompt)
    assert gui.chat(prompt) == expected
