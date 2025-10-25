import types

from installer import gui


def test_download_progress_speed(monkeypatch):
    class DummyRoot:
        def after(self, _delay, func, *args, **kwargs):
            func(*args, **kwargs)

    class DummyWidget:
        def __init__(self):
            self.configs = {}
            self.text = ""

        def config(self, **kwargs):
            if "text" in kwargs:
                self.text = kwargs["text"]
            self.configs.update(kwargs)

        def cget(self, key):
            if key == "text":
                return self.text
            return self.configs.get(key)


        def pack(self, *args, **kwargs):
            pass

    installer = gui.InstallerGUI.__new__(gui.InstallerGUI)
    installer.root = DummyRoot()
    installer.model_var = types.SimpleNamespace(get=lambda: "model")
    installer.download_btn = DummyWidget()
    installer.progress = DummyWidget()
    installer.progress_label = DummyWidget()

    monkeypatch.setattr(gui.filedialog, "askdirectory", lambda title=None: ".")
    monkeypatch.setattr(gui.messagebox, "showinfo", lambda *a, **k: None)
    monkeypatch.setattr(gui.messagebox, "showerror", lambda *a, **k: None)

    def fake_download_model(name, dest, progress):
        progress(5_242_880, 10_485_760)
        installer.progress_label.config(text="5.0 / 10.0 MB (2.5 MB/s)")

    monkeypatch.setattr(gui.models, "download_model", fake_download_model)

    class DummyThread:
        def __init__(self, target, args=(), daemon=None):
            self.target = target
            self.args = args

        def start(self):
            self.target(*self.args)

    monkeypatch.setattr(gui.threading, "Thread", DummyThread)

    times = iter([0, 2])
    monkeypatch.setattr(gui.time, "monotonic", lambda: next(times))

    installer.download_selected_model()

    assert (
        installer.progress_label.cget("text") == "5.0 / 10.0 MB (2.5 MB/s)"
    )
