"""
Anthropic Model Provider Plugin
Supports Claude, Claude Instant, Claude 2, Claude 3
"""

from typing import Dict, Any, Optional, List
import os


class AnthropicPlugin:
    """Plugin for Anthropic Claude models"""
    
    name = "anthropic"
    version = "1.0.0"
    description = "Integration with Anthropic Claude models"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Anthropic plugin"""
        try:
            import anthropic
            
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("ANTHROPIC_API_KEY")
            )
            
            if not self.api_key:
                return False
                
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self._initialized = True
            return True
            
        except ImportError:
            print("anthropic package not installed. Install with: pip install anthropic")
            return False
        except Exception as e:
            print(f"Error initializing Anthropic plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Anthropic action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}
            
        try:
            if action == "chat":
                return self._chat(params)
            elif action == "completion":
                return self._completion(params)
            elif action == "vision":
                return self._vision_analysis(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion with Claude"""
        model = params.get("model", "claude-3-sonnet-20240229")
        messages = params.get("messages", [])
        max_tokens = params.get("max_tokens", 2000)
        temperature = params.get("temperature", 0.7)
        system = params.get("system", "")
        
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=messages
        )
        
        return {
            "success": True,
            "response": response.content[0].text,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            },
            "stop_reason": response.stop_reason
        }
    
    def _completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text completion"""
        model = params.get("model", "claude-2.1")
        prompt = params.get("prompt", "")
        max_tokens = params.get("max_tokens", 2000)
        temperature = params.get("temperature", 0.7)
        
        # Convert prompt to messages format
        messages = [{"role": "user", "content": prompt}]
        
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages
        )
        
        return {
            "success": True,
            "response": response.content[0].text,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        }
    
    def _vision_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze image with Claude 3"""
        messages = params.get("messages", [])
        model = params.get("model", "claude-3-opus-20240229")
        max_tokens = params.get("max_tokens", 1000)
        
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages
        )
        
        return {
            "success": True,
            "response": response.content[0].text,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        }
    
    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
