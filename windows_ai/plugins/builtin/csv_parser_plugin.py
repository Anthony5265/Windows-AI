"""
CSV Parser Plugin - Utility
Parse and manipulate CSV data
"""
from typing import Dict, Any, List
import logging
import csv
import io

logger = logging.getLogger(__name__)

class Plugin:
    """Utility plugin for CSV Parser functionality"""
    
    def __init__(self):
        self.name = "CSV Parser"
        self.version = "2.0.0"
        self.description = "Parse and manipulate CSV data"
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute utility function"""
        try:
            operation = kwargs.get("operation", "parse")
            input_data = kwargs.get("input")
            
            if input_data is None:
                return {"status": "error", "message": "No input provided"}
            
            if operation == "parse":
                result = await self._parse(input_data, **kwargs)
            elif operation == "to_json":
                result = await self._to_json(input_data, **kwargs)
            elif operation == "validate":
                result = await self._validate(input_data, **kwargs)
            else:
                return {"status": "error", "message": f"Unknown operation: {operation}"}
            
            return {"status": "success", "result": result}
            
        except Exception as e:
            logger.error(f"{self.name} error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _parse(self, data: str, **kwargs) -> Dict[str, Any]:
        """Parse CSV string to list of dicts"""
        try:
            delimiter = kwargs.get("delimiter", ",")
            has_header = kwargs.get("has_header", True)
            
            reader = csv.DictReader(io.StringIO(data), delimiter=delimiter) if has_header else csv.reader(io.StringIO(data), delimiter=delimiter)
            rows = list(reader)
            
            return {
                "rows": rows,
                "row_count": len(rows),
                "columns": list(rows[0].keys()) if has_header and rows else None
            }
        except Exception as e:
            raise Exception(f"CSV parsing failed: {str(e)}")
    
    async def _to_json(self, data: str, **kwargs) -> Dict[str, Any]:
        """Convert CSV to JSON"""
        import json
        parsed = await self._parse(data, **kwargs)
        return {"json": json.dumps(parsed["rows"], indent=2)}
    
    async def _validate(self, data: str, **kwargs) -> Dict[str, Any]:
        """Validate CSV structure"""
        try:
            await self._parse(data, **kwargs)
            return {"valid": True, "message": "Valid CSV"}
        except Exception as e:
            return {"valid": False, "message": str(e)}
