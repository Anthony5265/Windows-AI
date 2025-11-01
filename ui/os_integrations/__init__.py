"""Prototypes that integrate Windows AI features into OS components."""

from .file_explorer import main as launch_file_explorer
from .terminal import main as launch_terminal

__all__ = ["launch_file_explorer", "launch_terminal"]
