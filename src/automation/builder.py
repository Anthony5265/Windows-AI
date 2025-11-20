from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from backends import Backend
from .workflow import (
    Step,
    Workflow,
    save_workflow,
    load_workflow,
    WORKFLOW_DIR,
)

try:  # pragma: no cover - optional dependency
    import tkinter as tk  # type: ignore
    from tkinter import ttk, filedialog, simpledialog, messagebox
except Exception:  # pragma: no cover - environment specific
    tk = None  # type: ignore
    ttk = None  # type: ignore


class WorkflowBuilder:
    """Minimal visual editor for workflows."""

    def __init__(
        self,
        backend: Backend,
        root: Optional["tk.Tk"] = None,
        use_gui: bool = True,
    ) -> None:
        self.backend = backend
        self.workflow = Workflow()
        self.use_gui = use_gui and tk is not None
        self.root = root
        if self.use_gui:
            try:
                self.root = root or tk.Toplevel()
            except tk.TclError as exc:  # pragma: no cover - headless
                raise RuntimeError("tkinter is not available") from exc
            self.root.title("Workflow Builder")
            self._build_widgets()

    # ------------------------------------------------------------------ logic
    def add_step(self, name: str) -> str:
        sid = uuid.uuid4().hex[:8]
        self.workflow.steps[sid] = Step(id=sid, name=name)
        if self.use_gui:
            self.listbox.insert("end", f"{sid}: {name}")
        return sid

    def connect_steps(self, src: str, dst: str) -> None:
        if src in self.workflow.steps and dst in self.workflow.steps:
            step = self.workflow.steps[src]
            if dst not in step.next:
                step.next.append(dst)

    def suggest(self, prompt: str) -> str:
        return self.backend.generate(prompt)

    def export(self, name: str) -> Path:
        WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
        path = WORKFLOW_DIR / f"{name}.yml"
        save_workflow(self.workflow, path)
        return path

    def import_file(self, path: Path) -> None:
        self.workflow = load_workflow(path)
        if self.use_gui:
            self.listbox.delete(0, "end")
            for step in self.workflow.steps.values():
                self.listbox.insert("end", f"{step.id}: {step.name}")

    # ------------------------------------------------------------------- GUI
    def _build_widgets(self) -> None:
        self.listbox = tk.Listbox(self.root, height=10)
        self.listbox.pack(fill="both", expand=True, padx=5, pady=5)

        frame = ttk.Frame(self.root)
        frame.pack(fill="x", padx=5, pady=5)
        self.entry = ttk.Entry(frame)
        self.entry.pack(side="left", fill="x", expand=True)
        ttk.Button(frame, text="Suggest", command=self._suggest).pack(side="left", padx=2)
        ttk.Button(frame, text="Add", command=self._add_step).pack(side="left", padx=2)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(btn_frame, text="Connect", command=self._connect).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Export", command=self._export_gui).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Import", command=self._import_gui).pack(side="left", padx=2)

    def _add_step(self) -> None:
        name = self.entry.get().strip()
        if not name:
            return
        self.add_step(name)
        self.entry.delete(0, "end")

    def _connect(self) -> None:
        sel = list(self.listbox.curselection())
        if len(sel) != 2:
            messagebox.showerror("Connect", "Select two steps to connect")
            return
        src_id = self.listbox.get(sel[0]).split(":", 1)[0]
        dst_id = self.listbox.get(sel[1]).split(":", 1)[0]
        self.connect_steps(src_id, dst_id)

    def _suggest(self) -> None:
        prompt = self.entry.get() or "Next step"
        suggestion = self.suggest(prompt)
        self.entry.delete(0, "end")
        self.entry.insert(0, suggestion)

    def _export_gui(self) -> None:
        name = simpledialog.askstring("Export", "Workflow name:")
        if not name:
            return
        path = self.export(name)
        messagebox.showinfo("Export", f"Saved to {path}")

    def _import_gui(self) -> None:
        path = filedialog.askopenfilename(initialdir=WORKFLOW_DIR, filetypes=[["YAML", "*.yml"]])
        if not path:
            return
        self.import_file(Path(path))


__all__ = ["WorkflowBuilder"]
