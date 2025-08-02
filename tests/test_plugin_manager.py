from installer.plugins.manager import PluginManager, load_catalog


def test_catalog_loads_default_manifest():
    plugins = load_catalog()
    names = [p.name for p in plugins]
    assert "LangChain" in names
    # ensure at least one paid plugin exists
    assert any(p.paid for p in plugins)


def test_plugin_manager_initializes():
    manager = PluginManager()
    assert manager.plugins  # catalog should not be empty
