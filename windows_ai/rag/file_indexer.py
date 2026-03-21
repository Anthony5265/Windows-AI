"""Windows File System Indexer for RAG.

Indexes local files for retrieval-augmented generation. Watches for
changes using ``watchdog`` and keeps an in-memory search index updated.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from windows_ai.rag.hybrid_search import BM25Index, SearchResult

logger = logging.getLogger(__name__)

# File extensions that are safe to read as text
TEXT_EXTENSIONS: Set[str] = {
    ".txt", ".md", ".rst", ".py", ".js", ".ts", ".jsx", ".tsx",
    ".html", ".css", ".json", ".yaml", ".yml", ".toml", ".ini",
    ".cfg", ".conf", ".xml", ".csv", ".log", ".sh", ".bat", ".ps1",
    ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".go", ".rs",
    ".rb", ".php", ".sql", ".r", ".m", ".swift", ".kt",
    ".dockerfile", ".gitignore", ".env",
}

# Maximum file size to index (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


class FileSystemIndexer:
    """Index local files for full-text search.

    Parameters
    ----------
    roots : list of str
        Directories to index recursively.
    extensions : set of str, optional
        File extensions to include (default: common text files).
    max_file_size : int
        Skip files larger than this (bytes).
    exclude_patterns : list of str
        Directory names to exclude (e.g. ``[".git", "node_modules"]``).
    """

    def __init__(
        self,
        roots: Optional[List[str]] = None,
        extensions: Optional[Set[str]] = None,
        max_file_size: int = MAX_FILE_SIZE,
        exclude_patterns: Optional[List[str]] = None,
    ) -> None:
        self.roots = roots or []
        self.extensions = extensions or TEXT_EXTENSIONS
        self.max_file_size = max_file_size
        self.exclude_patterns = set(exclude_patterns or [
            ".git", "node_modules", "__pycache__", ".venv", "venv",
            ".tox", "dist", "build", ".eggs",
        ])
        self._index = BM25Index()
        self._file_metadata: Dict[str, Dict[str, Any]] = {}
        self._indexed_count = 0
        self._last_index_time: Optional[float] = None
        self._watcher = None

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def index_all(self) -> Dict[str, Any]:
        """Perform a full index of all configured root directories."""
        start = time.time()
        count = 0
        errors = 0

        for root in self.roots:
            c, e = self._index_directory(root)
            count += c
            errors += e

        elapsed = time.time() - start
        self._indexed_count = count
        self._last_index_time = time.time()

        logger.info("Indexed %d files in %.2fs (%d errors)", count, elapsed, errors)
        return {
            "status": "success",
            "files_indexed": count,
            "errors": errors,
            "elapsed_seconds": round(elapsed, 2),
        }

    def index_file(self, file_path: str) -> bool:
        """Index a single file. Returns True on success."""
        path = Path(file_path)
        if not path.is_file():
            return False
        if path.suffix.lower() not in self.extensions:
            return False
        if path.stat().st_size > self.max_file_size:
            return False

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            doc_id = str(path.resolve())
            self._index.add_document(doc_id, content)
            self._file_metadata[doc_id] = {
                "path": str(path),
                "name": path.name,
                "extension": path.suffix,
                "size": path.stat().st_size,
                "modified": path.stat().st_mtime,
            }
            return True
        except Exception as exc:
            logger.debug("Failed to index %s: %s", file_path, exc)
            return False

    def remove_file(self, file_path: str) -> bool:
        """Remove a file from the index."""
        doc_id = str(Path(file_path).resolve())
        self._file_metadata.pop(doc_id, None)
        return self._index.remove_document(doc_id)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search indexed files."""
        results = self._index.search(query, top_k=top_k)
        # Attach file metadata
        for r in results:
            r.metadata = self._file_metadata.get(r.doc_id, {})
        return results

    # ------------------------------------------------------------------
    # File watching
    # ------------------------------------------------------------------

    def start_watching(self) -> bool:
        """Start watching root directories for file changes.

        Requires the ``watchdog`` package.
        """
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            indexer = self

            class _Handler(FileSystemEventHandler):
                def on_created(self, event):
                    if not event.is_directory:
                        indexer.index_file(event.src_path)

                def on_modified(self, event):
                    if not event.is_directory:
                        indexer.index_file(event.src_path)

                def on_deleted(self, event):
                    if not event.is_directory:
                        indexer.remove_file(event.src_path)

            observer = Observer()
            handler = _Handler()
            for root in self.roots:
                if os.path.isdir(root):
                    observer.schedule(handler, root, recursive=True)

            observer.start()
            self._watcher = observer
            logger.info("File watcher started for %d roots", len(self.roots))
            return True

        except ImportError:
            logger.warning("watchdog not installed – file watching disabled")
            return False

    def stop_watching(self) -> None:
        """Stop watching for file changes."""
        if self._watcher:
            self._watcher.stop()
            self._watcher.join(timeout=5)
            self._watcher = None

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _index_directory(self, root: str) -> tuple:
        """Walk *root* and index text files. Returns (count, errors)."""
        count = 0
        errors = 0
        root_path = Path(root)

        if not root_path.is_dir():
            logger.warning("Root directory not found: %s", root)
            return 0, 0

        for path in root_path.rglob("*"):
            if any(part in self.exclude_patterns for part in path.parts):
                continue
            if path.is_file() and path.suffix.lower() in self.extensions:
                if self.index_file(str(path)):
                    count += 1
                else:
                    errors += 1

        return count, errors

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        """Return indexer statistics."""
        return {
            "roots": self.roots,
            "indexed_files": self._index.document_count,
            "watching": self._watcher is not None,
            "last_index_time": self._last_index_time,
            "extensions": sorted(self.extensions),
        }
