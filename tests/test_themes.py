from ui.themes import Theme, Keyset, ThemeManager


def test_theme_manager():
    manager = ThemeManager()
    theme = Theme(name="dark", background="#000", foreground="#fff")
    keyset = Keyset(name="vim", mappings={"j": "down"})
    manager.add_theme(theme)
    manager.add_keyset(keyset)
    assert manager.get_theme("dark") == theme
    assert manager.get_keyset("vim") == keyset
