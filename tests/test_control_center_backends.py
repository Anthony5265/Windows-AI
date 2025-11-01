import importlib


def test_backends_importable():
    importlib.import_module('control_center.backends')


from control_center.backends import LocalBackend, SessionManager


def test_session_manager_generates_session_id():
    manager = SessionManager()
    sid = manager.create('alice', LocalBackend())
    assert isinstance(sid, str) and sid
    assert sid in manager._sessions
