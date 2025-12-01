from control_center.chat_ui import ChatUI


def test_voice_and_alt_input_hooks():
    ui = ChatUI(build=False)
    called = {}

    def voice(cmd: str) -> None:
        called['voice'] = cmd

    ui.register_voice_handler(voice)
    ui.handle_voice_command('hello')
    assert called['voice'] == 'hello'

    def alt(data: str) -> None:
        called['alt'] = data

    ui.register_alt_input(alt)
    ui.receive_alt_input('world')
    assert called['alt'] == 'world'
