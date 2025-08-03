from search import SearchEngine, LocalBackend
from gui.core import GuiCore


class DummyModel:
    def generate(self, prompt: str) -> str:
        return prompt.upper()


def test_search_index_and_query():
    backend = LocalBackend()
    engine = SearchEngine(backend)
    engine.index({"a": "hello world", "b": "foo bar"})
    assert engine.search("hello") == ["a"]


def test_gui_search_integration():
    backend = LocalBackend()
    engine = SearchEngine(backend)
    engine.index({"file1": "open sesame"})
    gui = GuiCore(DummyModel())
    gui.enable_search(engine)
    triggered = []
    gui.register_search_action("file1", lambda: triggered.append(True))
    results = gui.search("sesame")
    assert results == ["file1"]
    assert gui.overlays["search"].visible is True
    assert gui.activate_search_result("file1") is True
    assert triggered == [True]
