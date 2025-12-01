import control_center
from control_center import register_plugin
from control_center.chat_ui import ChatUI


class DummyPlugin:
    name = "DummyTool"

    def register(self, gui):
        pass


def test_chat_ui_lists_registered_plugins():
    original = list(control_center.get_plugins())
    try:
        register_plugin(DummyPlugin())
        ui = ChatUI(build=False)
        assert "DummyTool" in ui.plugin_names
    finally:
        control_center._PLUGINS[:] = original
