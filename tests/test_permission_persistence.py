from security import PermissionManager


def test_permission_persistence(tmp_path):
    perm_file = tmp_path / "perms.json"
    manager = PermissionManager(path=perm_file)
    manager.grant("PluginA", "network")
    manager.save()

    # Simulate a process restart
    new_manager = PermissionManager(path=perm_file)
    assert new_manager.has("PluginA", "network")
