from security import RollbackManager

from security import RollbackManager


def test_hooks_execute_in_reverse_order():
    manager = RollbackManager()
    events = []
    manager.add(lambda: events.append("first"))
    manager.add(lambda: events.append("second"))
    manager.rollback()
    assert events == ["second", "first"]


def test_hooks_cleared_after_rollback():
    manager = RollbackManager()
    manager.add(lambda: None)
    manager.rollback()
    assert not manager.hooks
