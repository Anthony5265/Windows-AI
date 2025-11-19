"""Tkinter dashboard for system performance metrics."""

from __future__ import annotations

from typing import Optional

try:  # pragma: no cover - import may fail on headless systems
    import tkinter as tk  # type: ignore
    from tkinter import ttk  # type: ignore
except Exception:  # pragma: no cover - environment specific
    tk = None  # type: ignore[assignment]
    ttk = None  # type: ignore[assignment]

from performance.optimizer import SystemOptimizer

__all__ = ["PerformanceGUI"]


class PerformanceGUI:
    """Display live system metrics and optimization tips."""

    def __init__(self, root: Optional["tk.Tk"] = None) -> None:
        if tk is None or ttk is None:
            raise RuntimeError("tkinter is not available")
        try:
            self.root = root or tk.Tk()
        except tk.TclError as exc:  # pragma: no cover - environment specific
            raise RuntimeError("tkinter is not available or no display is found") from exc

        self.root.title("Performance Dashboard")
        self.optimizer = SystemOptimizer()
        self.cpu_var = tk.StringVar()
        self.mem_var = tk.StringVar()
        self.disk_var = tk.StringVar()
        self.reco_var = tk.StringVar()
        self._build_widgets()
        self.refresh()

    def _build_widgets(self) -> None:
        frame = ttk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        ttk.Label(frame, text="CPU:").grid(row=0, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.cpu_var).grid(row=0, column=1, sticky="w")
        ttk.Label(frame, text="Memory:").grid(row=1, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.mem_var).grid(row=1, column=1, sticky="w")
        ttk.Label(frame, text="Disk:").grid(row=2, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.disk_var).grid(row=2, column=1, sticky="w")
        ttk.Label(frame, text="Recommendation:").grid(row=3, column=0, sticky="nw")
        ttk.Label(frame, textvariable=self.reco_var, wraplength=300).grid(row=3, column=1, sticky="w")
        ttk.Button(frame, text="Refresh", command=self.refresh).grid(row=4, column=0, columnspan=2, pady=5)

    def refresh(self) -> None:
        metrics = self.optimizer.collect_metrics()
        self.cpu_var.set(f"{metrics.cpu_percent or 0:.1f}%")
        self.mem_var.set(f"{metrics.memory_percent or 0:.1f}%")
        self.disk_var.set(f"{metrics.disk_percent or 0:.1f}%")
        recos = self.optimizer.recommend_tweaks(metrics)
        self.reco_var.set("; ".join(recos))

    def run(self) -> None:  # pragma: no cover - GUI loop
        self.root.mainloop()


def main() -> None:  # pragma: no cover - CLI helper
    gui = PerformanceGUI()
    gui.run()


if __name__ == "__main__":  # pragma: no cover
    main()
