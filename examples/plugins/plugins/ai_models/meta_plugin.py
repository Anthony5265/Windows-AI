"""
Meta AI Model Provider Plugin
Supports Llama 2, Code Llama, Llama Guard
"""

from typing import Dict, Any, Optional, List
import os


class MetaPlugin:
    """Plugin for Meta Llama models"""
    
    name = "meta"
    version = "1.0.0"
    description = "Integration with Meta Llama models (Llama 2, Code Llama, Llama Guard)"
    author = "Windows AI Team"
    
    def __init__(self):
        self.model_path: Optional[str] = None
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Meta Llama plugin"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            # Get model configuration
            model_name = (
                config.get("model_name") if config 
                else "meta-llama/Llama-2-7b-chat-hf"
            )
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            self._initialized = True
            return True
            
        except ImportError:
            print("transformers package not installed. Install with: pip install transformers torch")
            return False
        except Exception as e:
            print(f"Error initializing Meta plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Meta Llama action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}
            
        try:
            if action == "chat":
                return self._chat(params)
            elif action == "generate":
                return self._generate(params)
            elif action == "code":
                return self._code_generation(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion with Llama 2"""
        messages = params.get("messages", [])
        max_tokens = params.get("max_tokens", 500)
        temperature = params.get("temperature", 0.7)
        
        # Format chat prompt for Llama 2
        prompt = self._format_chat_prompt(messages)
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return {
            "success": True,
            "response": response[len(prompt):].strip()
        }
    
    def _generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text with Llama"""
        prompt = params.get("prompt", "")
        max_tokens = params.get("max_tokens", 500)
        temperature = params.get("temperature", 0.7)
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return {
            "success": True,
            "response": response[len(prompt):].strip()
        }
    
    def _code_generation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code with Code Llama"""
        prompt = params.get("prompt", "")
        max_tokens = params.get("max_tokens", 1000)
        temperature = params.get("temperature", 0.2)
        
        # Add code-specific formatting
        formatted_prompt = f"<s>[INST] {prompt} [/INST]"
        
        inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.model.device)
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return {
            "success": True,
            "response": response[len(formatted_prompt):].strip()
        }
    
    def _format_chat_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for Llama 2 chat"""
        prompt = "<s>"
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                prompt += f"[INST] {content} [/INST]"
            else:
                prompt += f" {content} </s><s>"
        return prompt
    
    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.model = None
        self.tokenizer = None
        return True
