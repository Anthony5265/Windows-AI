from ui.themes import Theme, Keyset, ThemeManager


def test_theme_manager():
    manager = ThemeManager()
    theme = Theme(name="dark", background="#000", foreground="#fff")
    keyset = Keyset(name="vim", mappings={"j": "down"})
    manager.add_theme(theme)
    manager.add_keyset(keyset)
    assert manager.get_theme("dark") == theme
    assert manager.get_keyset("vim") == keyset


def test_accessibility_theme_selection():
    manager = ThemeManager()
    manager.add_theme(Theme(name="light", background="#fff", foreground="#000"))
    theme = manager.apply_accessibility(screen_reader=True, high_contrast=True)
    assert theme is not None and theme.name == "high_contrast"
    assert manager.screen_reader_enabled is True
