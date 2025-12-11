"""
JSON Parser Plugin - Utility
Parse, validate, and format JSON data
"""
from typing import Dict, Any
import logging
import json

logger = logging.getLogger(__name__)

class Plugin:
    """Utility plugin for JSON Parser functionality"""
    
    def __init__(self):
        self.name = "JSON Parser"
        self.version = "2.0.0"
        self.description = "Parse, validate, and format JSON data"
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute utility function"""
        try:
            operation = kwargs.get("operation", "parse")
            input_data = kwargs.get("input")
            
            if input_data is None:
                return {"status": "error", "message": "No input provided"}
            
            # Process the data based on operation
            if operation == "parse":
                result = await self._parse(input_data, **kwargs)
            elif operation == "validate":
                result = await self._validate(input_data, **kwargs)
            elif operation == "format":
                result = await self._format(input_data, **kwargs)
            elif operation == "minify":
                result = await self._minify(input_data, **kwargs)
            else:
                return {"status": "error", "message": f"Unknown operation: {operation}"}
            
            return {"status": "success", "result": result}
            
        except Exception as e:
            logger.error(f"{self.name} error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _parse(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Parse JSON string to object"""
        try:
            if isinstance(data, str):
                parsed = json.loads(data)
            else:
                parsed = data  # Already an object
            
            return {
                "parsed": parsed,
                "type": type(parsed).__name__,
                "size": len(json.dumps(parsed))
            }
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON: {str(e)}")
    
    async def _validate(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Validate JSON data"""
        try:
            if isinstance(data, str):
                json.loads(data)
                return {
                    "valid": True,
                    "message": "Valid JSON",
                    "size": len(data)
                }
            else:
                # Try to serialize to verify it's valid JSON-serializable
                json.dumps(data)
                return {
                    "valid": True,
                    "message": "Valid JSON object",
                    "type": type(data).__name__
                }
        except (json.JSONDecodeError, TypeError) as e:
            return {
                "valid": False,
                "message": str(e),
                "error_type": type(e).__name__
            }
    
    async def _format(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Format JSON with pretty printing"""
        try:
            indent = kwargs.get("indent", 2)
            
            if isinstance(data, str):
                parsed = json.loads(data)
            else:
                parsed = data
            
            formatted = json.dumps(parsed, indent=indent, ensure_ascii=False)
            
            return {
                "formatted": formatted,
                "lines": formatted.count('\n') + 1,
                "size": len(formatted)
            }
        except Exception as e:
            raise Exception(f"Formatting failed: {str(e)}")
    
    async def _minify(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Minify JSON by removing whitespace"""
        try:
            if isinstance(data, str):
                parsed = json.loads(data)
            else:
                parsed = data
            
            minified = json.dumps(parsed, separators=(',', ':'), ensure_ascii=False)
            
            return {
                "minified": minified,
                "size": len(minified),
                "compression_ratio": len(json.dumps(parsed, indent=2)) / len(minified) if len(minified) > 0 else 1.0
            }
        except Exception as e:
            raise Exception(f"Minification failed: {str(e)}")

