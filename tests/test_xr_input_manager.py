from xr.input_manager import InputManager


def test_gesture_and_voice_mapping():
    called = []

    def on_swipe():
        called.append("swipe")

    def on_hello():
        called.append("hello")

    mgr = InputManager()
    mgr.register_gesture("swipe_left", on_swipe)
    mgr.register_voice_command("Hello", on_hello)

    assert mgr.handle_gesture("swipe_left") is True
    assert mgr.handle_voice_command("hello") is True
    assert called == ["swipe", "hello"]

    # Unregistered inputs should return False and not modify list
    assert mgr.handle_gesture("unknown") is False
    assert mgr.handle_voice_command("nope") is False
    assert called == ["swipe", "hello"]


def test_unregister_callbacks():
    called = []

    def on_swipe():
        called.append("swipe")

    def on_hello():
        called.append("hello")

    mgr = InputManager()
    mgr.register_gesture("swipe_left", on_swipe)
    mgr.register_voice_command("hello", on_hello)

    mgr.handle_gesture("swipe_left")
    mgr.handle_voice_command("hello")
    assert called == ["swipe", "hello"]

    assert mgr.unregister_gesture("swipe_left") is True
    assert mgr.unregister_voice_command("hello") is True

    # Second unregister should indicate nothing removed
    assert mgr.unregister_gesture("swipe_left") is False
    assert mgr.unregister_voice_command("hello") is False

    assert mgr.handle_gesture("swipe_left") is False
    assert mgr.handle_voice_command("hello") is False
    assert called == ["swipe", "hello"]
