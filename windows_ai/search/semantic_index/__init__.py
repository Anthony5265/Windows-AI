"""
Semantic Index sub-package for Windows AI Search.

Exports the public classes from every module in this package so that callers
can import directly from ``windows_ai.search.semantic_index``.
"""

from .dataset_sampler import DatasetSampler
from .document_tags import DocumentTags
from .embedding_cache import EmbeddingCache
from .query_profiler import QueryProfiler, QueryProfile, PerformanceStatistics
from .schedule_rebuild import ScheduleRebuild, RebuildScheduler
from .vector_exporter import VectorExporter

__all__ = [
    "DatasetSampler",
    "DocumentTags",
    "EmbeddingCache",
    "QueryProfiler",
    "QueryProfile",
    "PerformanceStatistics",
    "RebuildScheduler",
    "ScheduleRebuild",
    "VectorExporter",
]
