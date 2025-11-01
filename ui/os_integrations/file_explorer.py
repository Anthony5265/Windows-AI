"""Simple PySide6 file explorer prototype with placeholder AI hooks."""

from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QFileSystemModel


class AIFileExplorer(QWidget):
    """Minimal file explorer that could host AI-powered actions."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI File Explorer Prototype")

        layout = QVBoxLayout(self)
        home = os.path.expanduser("~")
        self.model = QFileSystemModel(self)
        self.model.setRootPath(home)

        self.view = QTreeView()
        self.view.setModel(self.model)
        self.view.setRootIndex(self.model.index(home))
        layout.addWidget(self.view)

        self.status = QLabel("Select a file and press Suggest")
        layout.addWidget(self.status)

        button = QPushButton("Suggest")
        button.clicked.connect(self._suggest)
        layout.addWidget(button)

    def _suggest(self) -> None:
        index = self.view.currentIndex()
        path = self.model.filePath(index)
        if path:
            # Placeholder for calling an AI model about the selected path.
            self.status.setText(f"AI would analyze: {path}")
        else:
            self.status.setText("No selection")


def main() -> None:
    app = QApplication(sys.argv)
    explorer = AIFileExplorer()
    explorer.resize(640, 480)
    explorer.show()
    sys.exit(app.exec())


if __name__ == "__main__":  # pragma: no cover - manual launch
    main()
