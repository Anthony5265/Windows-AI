"""
Metadata Filter Plugin
Advanced filtering of documents based on metadata
"""

from typing import Dict, Any, Optional, List
from datetime import datetime


class MetadataFilterPlugin:
    """Plugin for filtering documents using metadata"""

    name = "metadata_filter"
    version = "1.0.0"
    description = "Filter and query documents using structured metadata"
    author = "Windows AI Team"

    def __init__(self):
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Metadata Filter plugin"""
        try:
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Metadata Filter plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Metadata Filter action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "filter":
                return self._filter(params)
            elif action == "filter_by_date":
                return self._filter_by_date(params)
            elif action == "filter_by_source":
                return self._filter_by_source(params)
            elif action == "filter_by_tags":
                return self._filter_by_tags(params)
            elif action == "complex_filter":
                return self._complex_filter(params)
            elif action == "extract_metadata":
                return self._extract_metadata(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _filter(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generic metadata filtering"""
        documents = params.get("documents", [])
        filters = params.get("filters", {})

        filtered = []
        for doc in documents:
            metadata = doc.get("metadata", {})
            matches = True

            # Check all filter conditions
            for key, value in filters.items():
                if key not in metadata:
                    matches = False
                    break

                # Handle different comparison types
                if isinstance(value, dict):
                    # Complex filter with operators
                    if not self._evaluate_condition(metadata[key], value):
                        matches = False
                        break
                else:
                    # Direct equality
                    if metadata[key] != value:
                        matches = False
                        break

            if matches:
                filtered.append(doc)

        return {
            "success": True,
            "filtered_documents": filtered,
            "count": len(filtered),
            "original_count": len(documents),
            "filters_applied": filters
        }

    def _evaluate_condition(self, value: Any, condition: Dict[str, Any]) -> bool:
        """Evaluate a filter condition with operators"""
        operator = condition.get("op", "eq")
        target = condition.get("value")

        if operator == "eq":
            return value == target
        elif operator == "ne":
            return value != target
        elif operator == "gt":
            return value > target
        elif operator == "gte":
            return value >= target
        elif operator == "lt":
            return value < target
        elif operator == "lte":
            return value <= target
        elif operator == "in":
            return value in target
        elif operator == "nin":
            return value not in target
        elif operator == "contains":
            return target in value
        elif operator == "startswith":
            return str(value).startswith(str(target))
        elif operator == "endswith":
            return str(value).endswith(str(target))
        else:
            return False

    def _filter_by_date(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Filter documents by date range"""
        documents = params.get("documents", [])
        start_date = params.get("start_date")  # ISO format string
        end_date = params.get("end_date")
        date_field = params.get("date_field", "created_at")

        filtered = []
        for doc in documents:
            metadata = doc.get("metadata", {})

            if date_field not in metadata:
                continue

            doc_date = metadata[date_field]

            # Convert to datetime if string
            if isinstance(doc_date, str):
                try:
                    doc_date = datetime.fromisoformat(doc_date.replace('Z', '+00:00'))
                except:
                    continue

            # Check date range
            in_range = True
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                if doc_date < start_dt:
                    in_range = False

            if end_date and in_range:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                if doc_date > end_dt:
                    in_range = False

            if in_range:
                filtered.append(doc)

        return {
            "success": True,
            "filtered_documents": filtered,
            "count": len(filtered),
            "original_count": len(documents),
            "date_range": {
                "start": start_date,
                "end": end_date,
                "field": date_field
            }
        }

    def _filter_by_source(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Filter documents by source"""
        documents = params.get("documents", [])
        sources = params.get("sources", [])  # List of allowed sources
        source_field = params.get("source_field", "source")

        if not isinstance(sources, list):
            sources = [sources]

        filtered = []
        for doc in documents:
            metadata = doc.get("metadata", {})

            if source_field in metadata:
                if metadata[source_field] in sources:
                    filtered.append(doc)

        return {
            "success": True,
            "filtered_documents": filtered,
            "count": len(filtered),
            "original_count": len(documents),
            "allowed_sources": sources
        }

    def _filter_by_tags(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Filter documents by tags"""
        documents = params.get("documents", [])
        required_tags = params.get("required_tags", [])
        any_of_tags = params.get("any_of_tags", [])
        excluded_tags = params.get("excluded_tags", [])
        tags_field = params.get("tags_field", "tags")

        filtered = []
        for doc in documents:
            metadata = doc.get("metadata", {})

            if tags_field not in metadata:
                continue

            doc_tags = set(metadata[tags_field])

            # Check required tags (all must be present)
            if required_tags:
                if not set(required_tags).issubset(doc_tags):
                    continue

            # Check any_of tags (at least one must be present)
            if any_of_tags:
                if not set(any_of_tags).intersection(doc_tags):
                    continue

            # Check excluded tags (none should be present)
            if excluded_tags:
                if set(excluded_tags).intersection(doc_tags):
                    continue

            filtered.append(doc)

        return {
            "success": True,
            "filtered_documents": filtered,
            "count": len(filtered),
            "original_count": len(documents),
            "tag_filters": {
                "required": required_tags,
                "any_of": any_of_tags,
                "excluded": excluded_tags
            }
        }

    def _complex_filter(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Apply complex logical filters (AND, OR, NOT)"""
        documents = params.get("documents", [])
        filter_tree = params.get("filter", {})

        # Filter tree format:
        # {
        #   "operator": "AND" | "OR" | "NOT",
        #   "conditions": [
        #     {"field": "key", "op": "eq", "value": "val"},
        #     {"operator": "OR", "conditions": [...]}
        #   ]
        # }

        filtered = []
        for doc in documents:
            if self._evaluate_filter_tree(doc.get("metadata", {}), filter_tree):
                filtered.append(doc)

        return {
            "success": True,
            "filtered_documents": filtered,
            "count": len(filtered),
            "original_count": len(documents),
            "filter": filter_tree
        }

    def _evaluate_filter_tree(self, metadata: Dict[str, Any], filter_tree: Dict[str, Any]) -> bool:
        """Recursively evaluate complex filter tree"""
        operator = filter_tree.get("operator", "AND")

        # Leaf node: single condition
        if "field" in filter_tree:
            field = filter_tree["field"]
            if field not in metadata:
                return False

            condition = {
                "op": filter_tree.get("op", "eq"),
                "value": filter_tree.get("value")
            }
            return self._evaluate_condition(metadata[field], condition)

        # Internal node: logical operator
        conditions = filter_tree.get("conditions", [])

        if operator == "AND":
            return all(self._evaluate_filter_tree(metadata, cond) for cond in conditions)
        elif operator == "OR":
            return any(self._evaluate_filter_tree(metadata, cond) for cond in conditions)
        elif operator == "NOT":
            return not all(self._evaluate_filter_tree(metadata, cond) for cond in conditions)
        else:
            return False

    def _extract_metadata(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from documents"""
        documents = params.get("documents", [])
        fields = params.get("fields", None)  # Specific fields to extract, None = all

        metadata_list = []
        for doc in documents:
            metadata = doc.get("metadata", {})

            if fields:
                # Extract only specified fields
                extracted = {k: metadata.get(k) for k in fields if k in metadata}
            else:
                # Extract all metadata
                extracted = metadata.copy()

            metadata_list.append({
                "document_id": doc.get("id"),
                "metadata": extracted
            })

        # Aggregate statistics
        all_fields = set()
        for item in metadata_list:
            all_fields.update(item["metadata"].keys())

        return {
            "success": True,
            "metadata": metadata_list,
            "count": len(metadata_list),
            "unique_fields": sorted(list(all_fields)),
            "num_fields": len(all_fields)
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        return True
