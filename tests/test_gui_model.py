import pytest
tk = pytest.importorskip("tkinter")
from gui.core import GuiCore
from gui.simple_model import SimpleModel


def test_chat_returns_model_output():
    model = SimpleModel()
    gui = GuiCore(model)
    message = "hello world"
    assert gui.chat(message) == model.generate(message)
