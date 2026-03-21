"""Semantic Search over Plugin Documentation.

Indexes plugin metadata (name, description, tags, capabilities) using BM25
for fast text search. Enables users to find relevant plugins by natural
language queries.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from windows_ai.rag.hybrid_search import BM25Index, SearchResult

logger = logging.getLogger(__name__)


class PluginSearchIndex:
    """Search index for plugin discovery.

    Builds a BM25 index over plugin metadata to enable natural language
    queries like "generate images" or "transcribe audio".

    Example
    -------
    >>> idx = PluginSearchIndex()
    >>> idx.index_plugin({
    ...     "id": "openai-dalle",
    ...     "name": "DALL-E Image Generator",
    ...     "description": "Generate images from text prompts using OpenAI DALL-E",
    ...     "tags": ["image", "generation", "openai"],
    ...     "capabilities": ["text-to-image", "image-editing"],
    ... })
    >>> results = idx.search("generate images from text")
    >>> results[0].doc_id
    'openai-dalle'
    """

    def __init__(self) -> None:
        self._index = BM25Index()
        self._plugin_data: Dict[str, Dict[str, Any]] = {}
        self._indexed_count = 0

    def index_plugin(self, plugin: Dict[str, Any]) -> bool:
        """Index a single plugin's metadata.

        The plugin dict should contain at least ``id`` and ``name``.
        Optional fields: ``description``, ``tags``, ``capabilities``,
        ``version``, ``author``, ``plugin_type``.
        """
        plugin_id = plugin.get("id", "")
        if not plugin_id:
            return False

        # Build a searchable document from all metadata fields
        parts = [
            plugin.get("name", ""),
            plugin.get("description", ""),
            " ".join(plugin.get("tags", [])),
            " ".join(plugin.get("capabilities", [])),
            plugin.get("author", ""),
            plugin.get("plugin_type", ""),
        ]
        document = " ".join(p for p in parts if p)

        self._index.add_document(plugin_id, document)
        self._plugin_data[plugin_id] = plugin
        self._indexed_count += 1
        return True

    def index_plugins(self, plugins: List[Dict[str, Any]]) -> int:
        """Index a batch of plugins. Returns the count indexed."""
        count = 0
        for p in plugins:
            if self.index_plugin(p):
                count += 1
        logger.info("Indexed %d/%d plugins", count, len(plugins))
        return count

    def remove_plugin(self, plugin_id: str) -> bool:
        """Remove a plugin from the index."""
        self._plugin_data.pop(plugin_id, None)
        return self._index.remove_document(plugin_id)

    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search for plugins matching *query*.

        Returns a list of ``SearchResult`` objects sorted by relevance.
        Each result's ``metadata`` contains the full plugin dict.
        """
        results = self._index.search(query, top_k=top_k)
        for r in results:
            r.metadata = self._plugin_data.get(r.doc_id, {})
        return results

    def search_by_tags(self, tags: List[str], top_k: int = 20) -> List[SearchResult]:
        """Find plugins that match any of the given tags."""
        query = " ".join(tags)
        return self.search(query, top_k=top_k)

    def search_by_capability(self, capability: str, top_k: int = 20) -> List[SearchResult]:
        """Find plugins providing a specific capability."""
        return self.search(capability, top_k=top_k)

    def get_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve indexed metadata for a plugin."""
        return self._plugin_data.get(plugin_id)

    def list_all(self) -> List[Dict[str, Any]]:
        """Return all indexed plugin metadata."""
        return list(self._plugin_data.values())

    @property
    def count(self) -> int:
        """Number of indexed plugins."""
        return self._index.document_count

    def stats(self) -> Dict[str, Any]:
        """Return index statistics."""
        all_tags = set()
        all_capabilities = set()
        for p in self._plugin_data.values():
            all_tags.update(p.get("tags", []))
            all_capabilities.update(p.get("capabilities", []))

        return {
            "indexed_plugins": self._index.document_count,
            "unique_tags": len(all_tags),
            "unique_capabilities": len(all_capabilities),
            "top_tags": sorted(all_tags)[:20],
        }
