from control_center.backends import context_menu_enabled, set_context_menu


def test_context_menu_toggle():
    set_context_menu(True)
    assert context_menu_enabled() is True
    set_context_menu(False)
    assert context_menu_enabled() is False
