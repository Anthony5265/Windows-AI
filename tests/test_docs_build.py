import pytest
markdown = pytest.importorskip("markdown")
import pathlib

DOCS_DIR = pathlib.Path(__file__).resolve().parent.parent / "docs"


def test_markdown_files_parse():
    for path in DOCS_DIR.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        # Parsing should not raise exceptions
        markdown.markdown(text)
