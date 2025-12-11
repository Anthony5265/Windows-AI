"""
Hash Generator Plugin - Utility
Generate cryptographic hashes (MD5, SHA256, SHA512, etc.)
"""
from typing import Dict, Any
import logging
import hashlib

logger = logging.getLogger(__name__)

class Plugin:
    """Utility plugin for Hash Generator functionality"""
    
    def __init__(self):
        self.name = "Hash Generator"
        self.version = "2.0.0"
        self.description = "Generate cryptographic hashes"
        self.supported_algorithms = ['md5', 'sha1', 'sha256', 'sha384', 'sha512', 'blake2b', 'blake2s']
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute utility function"""
        try:
            input_data = kwargs.get("input")
            algorithm = kwargs.get("algorithm", "sha256").lower()
            
            if input_data is None:
                return {"status": "error", "message": "No input provided"}
            
            if algorithm not in self.supported_algorithms:
                return {
                    "status": "error", 
                    "message": f"Unsupported algorithm. Supported: {', '.join(self.supported_algorithms)}"
                }
            
            # Generate hash
            result = await self._generate_hash(input_data, algorithm, **kwargs)
            
            return {"status": "success", "result": result}
            
        except Exception as e:
            logger.error(f"{self.name} error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _generate_hash(self, data: Any, algorithm: str, **kwargs) -> Dict[str, Any]:
        """Generate hash for the input data"""
        try:
            # Convert to bytes if string
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            elif isinstance(data, bytes):
                data_bytes = data
            else:
                data_bytes = str(data).encode('utf-8')
            
            # Create hash object
            hash_obj = hashlib.new(algorithm)
            hash_obj.update(data_bytes)
            
            # Get hex digest
            hash_hex = hash_obj.hexdigest()
            
            # Optional: generate all common hashes
            all_hashes = kwargs.get("all_hashes", False)
            
            result = {
                "hash": hash_hex,
                "algorithm": algorithm,
                "input_length": len(data_bytes),
                "hash_length": len(hash_hex)
            }
            
            if all_hashes:
                result["all_hashes"] = {}
                for algo in self.supported_algorithms:
                    h = hashlib.new(algo)
                    h.update(data_bytes)
                    result["all_hashes"][algo] = h.hexdigest()
            
            return result
            
        except Exception as e:
            raise Exception(f"Hash generation failed: {str(e)}")

