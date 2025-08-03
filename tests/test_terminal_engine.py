from terminal.engine import TerminalEngine
import pytest


def test_run_command():
    engine = TerminalEngine()
    out = engine.run("echo hello")
    assert out == "hello"
    assert engine.history[0] == ("echo hello", "hello")


def test_run_multi_word_command():
    engine = TerminalEngine()
    out = engine.run("echo hello world")
    assert out == "hello world"


def test_rejects_piped_command():
    engine = TerminalEngine()
    with pytest.raises(ValueError):
        engine.run("echo hi | grep h")


def test_rejects_redirection_command():
    engine = TerminalEngine()
    with pytest.raises(ValueError):
        engine.run("echo hi > /tmp/out")
