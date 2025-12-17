#!/usr/bin/env python3
"""Vector Exporter for semantic index embeddings.

Provides a simple interface to export vector data (ids, texts, metadata, and
embeddings) to JSONL or CSV for downstream analysis or migration. Designed to
operate in offline contexts without external dependencies beyond the standard
library.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)


class VectorExporter:
    """Export semantic vectors to JSONL or CSV for external analysis."""
    
    def __init__(self, output_dir: Optional[str | Path] = None, export_format: str = "jsonl"):
        """Initialize the vector exporter system.

        Args:
            output_dir: Base directory where exports will be written.
            export_format: Default export format ("jsonl" or "csv").
        """
        self.output_dir = Path(output_dir or "exports/vectors")
        self.export_format = export_format.lower()
        self.initialized = False
        logger.info("Initialized vector_exporter")
    
    def setup(self, output_dir: Optional[str | Path] = None, export_format: Optional[str] = None) -> bool:
        """Prepare output directory and validate configuration."""
        try:
            if output_dir:
                self.output_dir = Path(output_dir)
            if export_format:
                self.export_format = export_format.lower()

            if self.export_format not in {"jsonl", "csv"}:
                raise ValueError("export_format must be either 'jsonl' or 'csv'")

            self.output_dir = self.output_dir.expanduser().resolve()
            self.output_dir.mkdir(parents=True, exist_ok=True)

            self.initialized = True
            logger.info("vector_exporter setup completed")
            return True
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False
    
    def execute(
        self,
        *,
        vectors: Optional[Iterable[Dict[str, Any]]] = None,
        retriever: Optional[Callable[[], Iterable[Dict[str, Any]]]] = None,
        source_path: Optional[str | Path] = None,
        output_name: Optional[str] = None,
        export_format: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Export vectors from provided data, retriever, or file.

        Args:
            vectors: Iterable of vector records already loaded in memory.
            retriever: Callable returning an iterable of vector records.
            source_path: Path to JSONL file containing vector records.
            output_name: Override output filename (defaults to vectors.jsonl/csv).
            export_format: Override export format for this run.

        Returns:
            Dict with status, message, and export metadata.
        """
        if not self.initialized:
            raise RuntimeError("vector_exporter not initialized. Call setup() first.")

        chosen_format = (export_format or self.export_format).lower()
        if chosen_format not in {"jsonl", "csv"}:
            raise ValueError("export_format must be either 'jsonl' or 'csv'")

        records: List[Dict[str, Any]] = []

        if vectors is not None:
            records = list(vectors)
        elif retriever is not None:
            records = list(retriever())
        elif source_path is not None:
            records = self._load_from_jsonl(Path(source_path))
        else:
            raise ValueError("Provide vectors, retriever, or source_path to export")

        normalized = [self._normalize_record(record) for record in records]

        output_file = self.output_dir / (output_name or f"vectors.{chosen_format}")
        if chosen_format == "jsonl":
            self._write_jsonl(output_file, normalized)
        else:
            self._write_csv(output_file, normalized)

        message = f"Exported {len(normalized)} vectors to {output_file}"
        logger.info(message)

        return {
            "status": "success",
            "message": message,
            "data": {
                "output_file": str(output_file),
                "count": len(normalized),
                "format": chosen_format,
            },
        }

    @staticmethod
    def _normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure a record has consistent keys and serializable types."""
        vector_id = record.get("id") or record.get("doc_id")
        embedding = record.get("embedding") or record.get("vector")
        metadata = record.get("metadata") or {}

        if embedding is None:
            raise ValueError("Vector record missing 'embedding'")

        return {
            "id": vector_id,
            "embedding": embedding,
            "metadata": metadata,
        }

    @staticmethod
    def _write_jsonl(path: Path, records: List[Dict[str, Any]]):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for record in records:
                json.dump(record, f)
                f.write("\n")

    @staticmethod
    def _write_csv(path: Path, records: List[Dict[str, Any]]):
        path.parent.mkdir(parents=True, exist_ok=True)
        headers = ["id", "embedding", "metadata"]
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for record in records:
                writer.writerow(
                    {
                        "id": record.get("id"),
                        "embedding": json.dumps(record.get("embedding")),
                        "metadata": json.dumps(record.get("metadata", {})),
                    }
                )

    @staticmethod
    def _load_from_jsonl(path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {path}")

        records: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        return records


def main():
    """Main entry point for standalone execution."""
    system = VectorExporter()
    
    if system.setup():
        result = system.execute()
        print(f"Result: {result}")
    else:
        print("Setup failed")


if __name__ == "__main__":
    main()
