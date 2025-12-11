"""
Base64 Encoder Plugin - Utility
Encode and decode Base64 strings
"""
from typing import Dict, Any
import logging
import base64

logger = logging.getLogger(__name__)

class Plugin:
    """Utility plugin for Base64 Encoder functionality"""
    
    def __init__(self):
        self.name = "Base64 Encoder"
        self.version = "2.0.0"
        self.description = "Encode and decode Base64 strings"
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute utility function"""
        try:
            operation = kwargs.get("operation", "encode")
            input_data = kwargs.get("input")
            
            if input_data is None:
                return {"status": "error", "message": "No input provided"}
            
            # Process the data based on operation
            if operation == "encode":
                result = await self._encode(input_data, **kwargs)
            elif operation == "decode":
                result = await self._decode(input_data, **kwargs)
            else:
                return {"status": "error", "message": f"Unknown operation: {operation}"}
            
            return {"status": "success", "result": result}
            
        except Exception as e:
            logger.error(f"{self.name} error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _encode(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Encode data to Base64"""
        try:
            # Convert to bytes if string
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            elif isinstance(data, bytes):
                data_bytes = data
            else:
                data_bytes = str(data).encode('utf-8')
            
            # Encode to Base64
            encoded = base64.b64encode(data_bytes).decode('utf-8')
            
            return {
                "encoded": encoded,
                "original_length": len(data_bytes),
                "encoded_length": len(encoded)
            }
        except Exception as e:
            raise Exception(f"Encoding failed: {str(e)}")
    
    async def _decode(self, data: str, **kwargs) -> Dict[str, Any]:
        """Decode Base64 data"""
        try:
            # Decode from Base64
            decoded_bytes = base64.b64decode(data)
            
            # Try to decode as UTF-8 string
            try:
                decoded_str = decoded_bytes.decode('utf-8')
            except UnicodeDecodeError:
                decoded_str = decoded_bytes.hex()  # Return as hex if not valid UTF-8
            
            return {
                "decoded": decoded_str,
                "decoded_length": len(decoded_bytes),
                "is_text": isinstance(decoded_str, str) and not decoded_str.startswith('\\x')
            }
        except Exception as e:
            raise Exception(f"Decoding failed: {str(e)}")

