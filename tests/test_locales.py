import installer.locales as locales


def test_locales_differ():
    en = locales.load_strings("en")
    es = locales.load_strings("es")
    assert en["Windows AI Installer"] != es["Windows AI Installer"]
    assert en["Send"] != es["Send"]
