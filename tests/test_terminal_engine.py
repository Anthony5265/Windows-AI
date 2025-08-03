from terminal.engine import TerminalEngine


def test_run_command():
    engine = TerminalEngine()
    out = engine.run("echo hello")
    assert out == "hello"
    assert engine.history[0] == ("echo hello", "hello")
