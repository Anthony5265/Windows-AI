"""
Amazon CodeWhisperer Plugin
AI-powered code completion
"""

from typing import Dict, Any, Optional, List
import os


class CodeWhispererPlugin:
    """Plugin for Amazon CodeWhisperer"""
    
    name = "codewhisperer"
    version = "1.0.0"
    description = "Integration with Amazon CodeWhisperer for AI code completion"
    author = "Windows AI Team"
    
    def __init__(self):
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the CodeWhisperer plugin"""
        try:
            import boto3
            
            # Initialize AWS client
            self.client = boto3.client('codewhisperer-runtime')
            self._initialized = True
            return True
            
        except ImportError:
            print("boto3 not installed. Install with: pip install boto3")
            return False
        except Exception as e:
            print(f"Error initializing CodeWhisperer plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a CodeWhisperer action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}
            
        try:
            if action == "suggest":
                return self._get_suggestions(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_suggestions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get code suggestions"""
        file_context = params.get("file_context", {})
        programming_language = params.get("programming_language", "python")
        
        response = self.client.generate_completions(
            fileContext=file_context,
            programmingLanguage={'languageName': programming_language}
        )
        
        return {
            "success": True,
            "completions": response.get("completions", [])
        }
    
    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        return True
