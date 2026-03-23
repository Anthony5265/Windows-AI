"""
Search module tests.
Tests SearchEngine, LocalBackend, and SearchService.
"""

import pytest
from windows_ai.search import SearchEngine, LocalBackend


def test_search_engine_creation():
    """Test SearchEngine can be created with a LocalBackend."""
    backend = LocalBackend()
    engine = SearchEngine(backend)
    assert engine is not None
    assert engine.backend is backend


def test_local_backend_index_and_search():
    """Test LocalBackend indexes documents and returns search results."""
    backend = LocalBackend()
    backend.index({"doc1": "hello world", "doc2": "foo bar baz"})
    results = backend.search("hello")
    assert "doc1" in results
    assert "doc2" not in results


def test_search_engine_index_and_search():
    """Test SearchEngine indexes and searches via backend."""
    backend = LocalBackend()
    engine = SearchEngine(backend)
    engine.index({"a": "python programming", "b": "javascript web"})
    results = engine.search("python")
    assert "a" in results


def test_search_engine_empty_query():
    """Test SearchEngine handles empty search gracefully."""
    backend = LocalBackend()
    engine = SearchEngine(backend)
    engine.index({"a": "hello world"})
    results = engine.search("")
    assert isinstance(results, list)


def test_search_engine_no_results():
    """Test SearchEngine returns empty list when no matches."""
    backend = LocalBackend()
    engine = SearchEngine(backend)
    engine.index({"a": "hello world"})
    results = engine.search("zzzznonexistent")
    assert results == []


def test_search_engine_top_k():
    """Test SearchEngine respects top_k parameter."""
    backend = LocalBackend()
    engine = SearchEngine(backend)
    docs = {f"doc{i}": f"test content {i}" for i in range(20)}
    engine.index(docs)
    results = engine.search("test", top_k=3)
    assert len(results) <= 3


def test_search_engine_with_remote_apis_none():
    """Test SearchEngine works with no remote APIs."""
    backend = LocalBackend()
    engine = SearchEngine(backend, remote_apis=None)
    engine.index({"a": "hello"})
    results = engine.search("hello")
    assert "a" in results


def test_search_engine_deduplicates_results():
    """Test SearchEngine removes duplicate results."""
    backend = LocalBackend()
    engine = SearchEngine(backend)
    engine.index({"a": "test query", "b": "another test query"})
    results = engine.search("test")
    # Results should have no duplicates
    assert len(results) == len(set(results))
