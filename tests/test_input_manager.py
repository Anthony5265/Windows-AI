from xr.input_manager import InputManager


def test_register_and_unregister_callbacks():
    called = []

    def on_gesture():
        called.append("gesture")

    def on_voice():
        called.append("voice")

    mgr = InputManager()
    mgr.register_gesture("swipe_left", on_gesture)
    mgr.register_voice_command("Hello", on_voice)

    assert mgr.handle_gesture("swipe_left") is True
    assert mgr.handle_voice_command("hello") is True
    assert called == ["gesture", "voice"]

    # Unregister callbacks and ensure they are not invoked
    assert mgr.unregister_gesture("swipe_left") is True
    # Unregister with different casing to ensure case-insensitive removal
    assert mgr.unregister_voice_command("HELLO") is True

    # Subsequent unregister attempts should report False
    assert mgr.unregister_gesture("swipe_left") is False
    assert mgr.unregister_voice_command("hello") is False

    assert mgr.handle_gesture("swipe_left") is False
    assert mgr.handle_voice_command("hello") is False
    # Callback list should remain unchanged after unregistration
    assert called == ["gesture", "voice"]
