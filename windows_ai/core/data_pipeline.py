"""
Data Pipeline Engine — ETL pipeline with source connectors, transformations, and sinks.
Supports streaming and batch modes, data validation, and schema evolution.
"""
import logging
import uuid
import time
import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class PipelineMode(Enum):
    BATCH = "batch"
    STREAMING = "streaming"
    MICRO_BATCH = "micro_batch"


class DataType(Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    JSON = "json"
    BINARY = "binary"


@dataclass
class ColumnSchema:
    name: str
    data_type: DataType
    nullable: bool = True
    default: Any = None
    validators: List[str] = field(default_factory=list)


@dataclass
class DataSchema:
    name: str
    columns: List[ColumnSchema]
    version: int = 1
    primary_key: Optional[str] = None

    def validate_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        for col in self.columns:
            if col.name not in record:
                if not col.nullable and col.default is None:
                    errors.append(f"Missing required field: {col.name}")
                continue
            value = record[col.name]
            if value is None and not col.nullable:
                errors.append(f"Null value for non-nullable field: {col.name}")
            elif value is not None:
                if col.data_type == DataType.INTEGER and not isinstance(value, int):
                    try:
                        int(value)
                    except (ValueError, TypeError):
                        errors.append(f"Invalid integer for {col.name}: {value}")
                elif col.data_type == DataType.FLOAT and not isinstance(value, (int, float)):
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        errors.append(f"Invalid float for {col.name}: {value}")
        return len(errors) == 0, errors


@dataclass
class TransformStep:
    name: str
    transform_type: str  # filter, map, aggregate, join, deduplicate, sort, window
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineMetrics:
    records_read: int = 0
    records_written: int = 0
    records_filtered: int = 0
    records_errored: int = 0
    bytes_processed: int = 0
    start_time: float = 0
    end_time: float = 0
    transform_times: Dict[str, float] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        return self.end_time - self.start_time if self.end_time else time.time() - self.start_time

    @property
    def throughput(self) -> float:
        d = self.duration_seconds
        return self.records_written / d if d > 0 else 0


class DataSource:
    """Abstract data source."""
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config

    async def connect(self) -> bool:
        return True

    async def read_batch(self, batch_size: int = 1000) -> List[Dict[str, Any]]:
        return []

    async def close(self):
        pass


class CSVSource(DataSource):
    """CSV file data source."""
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.file_path = config.get("file_path", "")
        self.delimiter = config.get("delimiter", ",")
        self.headers = config.get("headers", [])
        self._data: List[Dict[str, Any]] = []
        self._position = 0

    async def connect(self) -> bool:
        try:
            import csv
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    reader = csv.DictReader(f, delimiter=self.delimiter)
                    self._data = list(reader)
            return True
        except Exception as e:
            logger.error(f"CSVSource connect failed: {e}")
            return False

    async def read_batch(self, batch_size: int = 1000) -> List[Dict[str, Any]]:
        batch = self._data[self._position:self._position + batch_size]
        self._position += batch_size
        return batch


class JSONSource(DataSource):
    """JSON file/API data source."""
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self._data = config.get("data", [])
        self._position = 0

    async def read_batch(self, batch_size: int = 1000) -> List[Dict[str, Any]]:
        batch = self._data[self._position:self._position + batch_size]
        self._position += batch_size
        return batch


class DataSink:
    """Abstract data sink."""
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.written_count = 0

    async def connect(self) -> bool:
        return True

    async def write_batch(self, records: List[Dict[str, Any]]) -> int:
        self.written_count += len(records)
        return len(records)

    async def close(self):
        pass


class MemorySink(DataSink):
    """In-memory data sink for testing."""
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config or {})
        self.records: List[Dict[str, Any]] = []

    async def write_batch(self, records: List[Dict[str, Any]]) -> int:
        self.records.extend(records)
        self.written_count += len(records)
        return len(records)


class TransformEngine:
    """Applies transformations to data records."""

    def __init__(self):
        self._transforms: Dict[str, Callable] = {
            "filter": self._apply_filter,
            "map": self._apply_map,
            "deduplicate": self._apply_deduplicate,
            "rename": self._apply_rename,
            "cast": self._apply_cast,
            "fill_null": self._apply_fill_null,
            "drop_columns": self._apply_drop_columns,
            "add_column": self._apply_add_column,
            "sort": self._apply_sort,
        }

    def apply(self, records: List[Dict[str, Any]], step: TransformStep) -> List[Dict[str, Any]]:
        handler = self._transforms.get(step.transform_type)
        if not handler:
            logger.warning(f"Unknown transform type: {step.transform_type}")
            return records
        return handler(records, step.config)

    def _apply_filter(self, records, config):
        field_name = config.get("field", "")
        operator = config.get("operator", "eq")
        value = config.get("value")
        result = []
        for r in records:
            v = r.get(field_name)
            if operator == "eq" and v == value:
                result.append(r)
            elif operator == "neq" and v != value:
                result.append(r)
            elif operator == "gt" and v is not None and v > value:
                result.append(r)
            elif operator == "lt" and v is not None and v < value:
                result.append(r)
            elif operator == "contains" and value in str(v):
                result.append(r)
            elif operator == "not_null" and v is not None:
                result.append(r)
        return result

    def _apply_map(self, records, config):
        field_name = config.get("field", "")
        expression = config.get("expression", "")
        for r in records:
            if field_name in r:
                if expression == "upper":
                    r[field_name] = str(r[field_name]).upper()
                elif expression == "lower":
                    r[field_name] = str(r[field_name]).lower()
                elif expression == "strip":
                    r[field_name] = str(r[field_name]).strip()
                elif expression == "abs":
                    try:
                        r[field_name] = abs(float(r[field_name]))
                    except (ValueError, TypeError):
                        pass
        return records

    def _apply_deduplicate(self, records, config):
        key_field = config.get("key", None)
        seen = set()
        result = []
        for r in records:
            key = r.get(key_field, str(r)) if key_field else str(sorted(r.items()))
            if key not in seen:
                seen.add(key)
                result.append(r)
        return result

    def _apply_rename(self, records, config):
        mapping = config.get("mapping", {})
        for r in records:
            for old_name, new_name in mapping.items():
                if old_name in r:
                    r[new_name] = r.pop(old_name)
        return records

    def _apply_cast(self, records, config):
        field_name = config.get("field", "")
        target_type = config.get("type", "string")
        for r in records:
            if field_name in r and r[field_name] is not None:
                try:
                    if target_type == "int":
                        r[field_name] = int(r[field_name])
                    elif target_type == "float":
                        r[field_name] = float(r[field_name])
                    elif target_type == "string":
                        r[field_name] = str(r[field_name])
                    elif target_type == "bool":
                        r[field_name] = bool(r[field_name])
                except (ValueError, TypeError):
                    pass
        return records

    def _apply_fill_null(self, records, config):
        field_name = config.get("field", "")
        fill_value = config.get("value", "")
        for r in records:
            if r.get(field_name) is None:
                r[field_name] = fill_value
        return records

    def _apply_drop_columns(self, records, config):
        columns = config.get("columns", [])
        for r in records:
            for col in columns:
                r.pop(col, None)
        return records

    def _apply_add_column(self, records, config):
        name = config.get("name", "new_col")
        value = config.get("value", None)
        for r in records:
            r[name] = value
        return records

    def _apply_sort(self, records, config):
        field_name = config.get("field", "")
        reverse = config.get("reverse", False)
        return sorted(records, key=lambda r: r.get(field_name, ""), reverse=reverse)


class DataPipeline:
    """Main data pipeline orchestrator."""

    def __init__(self, name: str, mode: PipelineMode = PipelineMode.BATCH):
        self.pipeline_id = str(uuid.uuid4())
        self.name = name
        self.mode = mode
        self.source: Optional[DataSource] = None
        self.sink: Optional[DataSink] = None
        self.transforms: List[TransformStep] = []
        self.schema: Optional[DataSchema] = None
        self.metrics = PipelineMetrics()
        self.transform_engine = TransformEngine()
        self._error_records: List[Dict[str, Any]] = []
        logger.info(f"DataPipeline '{name}' created (mode={mode.value})")

    def set_source(self, source: DataSource):
        self.source = source
        return self

    def set_sink(self, sink: DataSink):
        self.sink = sink
        return self

    def add_transform(self, step: TransformStep):
        self.transforms.append(step)
        return self

    def set_schema(self, schema: DataSchema):
        self.schema = schema
        return self

    async def execute(self, batch_size: int = 1000) -> PipelineMetrics:
        """Execute the pipeline."""
        self.metrics = PipelineMetrics(start_time=time.time())

        if not self.source or not self.sink:
            raise ValueError("Pipeline requires both source and sink")

        await self.source.connect()
        await self.sink.connect()

        try:
            while True:
                batch = await self.source.read_batch(batch_size)
                if not batch:
                    break

                self.metrics.records_read += len(batch)

                # Validate against schema
                if self.schema:
                    valid_batch = []
                    for record in batch:
                        is_valid, errors = self.schema.validate_record(record)
                        if is_valid:
                            valid_batch.append(record)
                        else:
                            self.metrics.records_errored += 1
                            self._error_records.append({"record": record, "errors": errors})
                    batch = valid_batch

                # Apply transforms
                for step in self.transforms:
                    t0 = time.time()
                    original_len = len(batch)
                    batch = self.transform_engine.apply(batch, step)
                    self.metrics.records_filtered += original_len - len(batch)
                    elapsed = time.time() - t0
                    self.metrics.transform_times[step.name] = self.metrics.transform_times.get(step.name, 0) + elapsed

                # Write to sink
                written = await self.sink.write_batch(batch)
                self.metrics.records_written += written

        finally:
            await self.source.close()
            await self.sink.close()
            self.metrics.end_time = time.time()

        logger.info(f"Pipeline '{self.name}' completed: {self.metrics.records_read} read, "
                     f"{self.metrics.records_written} written, {self.metrics.records_errored} errors "
                     f"in {self.metrics.duration_seconds:.2f}s")
        return self.metrics

    def get_error_records(self) -> List[Dict[str, Any]]:
        return self._error_records


class PipelineBuilder:
    """Fluent builder for constructing pipelines."""

    def __init__(self, name: str):
        self._pipeline = DataPipeline(name)

    def source(self, source_type: str, config: Dict[str, Any]) -> "PipelineBuilder":
        if source_type == "csv":
            self._pipeline.set_source(CSVSource("csv_source", config))
        elif source_type == "json":
            self._pipeline.set_source(JSONSource("json_source", config))
        else:
            self._pipeline.set_source(DataSource(source_type, config))
        return self

    def sink(self, sink_type: str, config: Dict[str, Any] = None) -> "PipelineBuilder":
        if sink_type == "memory":
            self._pipeline.set_sink(MemorySink("memory_sink", config or {}))
        else:
            self._pipeline.set_sink(DataSink(sink_type, config or {}))
        return self

    def filter(self, field: str, operator: str, value: Any) -> "PipelineBuilder":
        step = TransformStep(f"filter_{field}", "filter", {"field": field, "operator": operator, "value": value})
        self._pipeline.add_transform(step)
        return self

    def map_field(self, field: str, expression: str) -> "PipelineBuilder":
        step = TransformStep(f"map_{field}", "map", {"field": field, "expression": expression})
        self._pipeline.add_transform(step)
        return self

    def deduplicate(self, key: str = None) -> "PipelineBuilder":
        step = TransformStep("deduplicate", "deduplicate", {"key": key})
        self._pipeline.add_transform(step)
        return self

    def rename(self, mapping: Dict[str, str]) -> "PipelineBuilder":
        step = TransformStep("rename", "rename", {"mapping": mapping})
        self._pipeline.add_transform(step)
        return self

    def schema(self, schema: DataSchema) -> "PipelineBuilder":
        self._pipeline.set_schema(schema)
        return self

    def build(self) -> DataPipeline:
        return self._pipeline
