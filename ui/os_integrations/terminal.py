"""Simple PySide6 terminal prototype with placeholder AI suggestions."""

from __future__ import annotations

import subprocess
import sys

from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class AITerminal(QWidget):
    """Tiny terminal window that could host AI completion features."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI Terminal Prototype")
        layout = QVBoxLayout(self)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        self.prompt = QLineEdit()
        self.prompt.setPlaceholderText("Enter command and press Enter")
        self.prompt.returnPressed.connect(self.run_command)
        layout.addWidget(self.prompt)

        self.status = QLabel("AI suggestions will appear here")
        layout.addWidget(self.status)

        button = QPushButton("Suggest")
        button.clicked.connect(self._suggest)
        layout.addWidget(button)

    def run_command(self) -> None:
        cmd = self.prompt.text()
        if not cmd:
            return
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, shell=True, check=False
            )
            self.output.append(f"$ {cmd}\n{result.stdout}{result.stderr}")
        except Exception as exc:  # pragma: no cover - unlikely in tests
            self.output.append(f"Error: {exc}")
        self.prompt.clear()

    def _suggest(self) -> None:
        # Placeholder for AI-assisted command suggestions.
        self.status.setText("AI would suggest a useful command")


def main() -> None:
    app = QApplication(sys.argv)
    term = AITerminal()
    term.resize(640, 400)
    term.show()
    sys.exit(app.exec())


if __name__ == "__main__":  # pragma: no cover - manual launch
    main()
