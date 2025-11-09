"""
GitHub Copilot AI Model Provider Plugin
Supports code completion and chat functionality through GitHub Copilot API
"""

from typing import Dict, Any, Optional, List
import os
import json
import requests


class GitHubCopilotPlugin:
    """Plugin for GitHub Copilot AI models"""
    
    name = "github_copilot"
    version = "1.0.0"
    description = "Integration with GitHub Copilot API for code completion and chat"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.github_token: Optional[str] = None
        self.base_url = "https://api.githubcopilot.com"
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the GitHub Copilot plugin"""
        try:
            # Get API keys from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("GITHUB_COPILOT_API_KEY")
            )
            self.github_token = (
                config.get("github_token") if config 
                else os.getenv("GITHUB_TOKEN")
            )
            
            if not self.github_token:
                return False
                
            # If no Copilot API key, try to get it using GitHub token
            if not self.api_key:
                self.api_key = self._get_copilot_token()
                if not self.api_key:
                    return False
                    
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing GitHub Copilot plugin: {e}")
            return False
    
    def _get_copilot_token(self) -> Optional[str]:
        """Get Copilot API token using GitHub token"""
        try:
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Get Copilot token from GitHub API
            response = requests.get(
                "https://api.github.com/copilot/internal/v2/token",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("token")
            else:
                print(f"Failed to get Copilot token: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error getting Copilot token: {e}")
            return None
    
    def _make_request(self, endpoint: str, method: str = "POST", data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make request to Copilot API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Editor-Version": "vscode/1.0.0",
                "Editor-Plugin-Version": "copilot/1.0.0"
            }
            
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=data)
            else:
                response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API request failed: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GitHub Copilot action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide GitHub token."}
        
        try:
            if action == "complete":
                return self._complete(params)
            elif action == "chat":
                return self._chat(params)
            elif action == "explain":
                return self._explain(params)
            elif action == "fix":
                return self._fix(params)
            elif action == "generate":
                return self._generate(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _complete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Code completion"""
        prompt = params.get("prompt", "")
        language = params.get("language", "python")
        max_tokens = params.get("max_tokens", 100)
        temperature = params.get("temperature", 0.1)
        
        data = {
            "prompt": prompt,
            "suffix": "",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 1,
            "n": 1,
            "stop": [],
            "stream": False,
            "logprobs": 0,
            "echo": False,
            "context": {
                "language": language,
                "editor": "vscode"
            }
        }
        
        result = self._make_request("/completions", "POST", data)
        
        if "error" in result:
            return result
            
        return {
            "completion": result.get("choices", [{}])[0].get("text", ""),
            "model": "copilot-code-completion",
            "usage": result.get("usage", {})
        }
    
    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat with Copilot"""
        messages = params.get("messages", [])
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
            
        model = params.get("model", "gpt-4")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 500)
        
        data = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 1,
            "n": 1,
            "stream": False,
            "stop": []
        }
        
        result = self._make_request("/chat/completions", "POST", data)
        
        if "error" in result:
            return result
            
        return {
            "response": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
            "model": model,
            "usage": result.get("usage", {}),
            "finish_reason": result.get("choices", [{}])[0].get("finish_reason", "")
        }
    
    def _explain(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Explain code"""
        code = params.get("code", "")
        language = params.get("language", "python")
        
        messages = [
            {
                "role": "system",
                "content": f"You are a helpful programming assistant. Explain the following {language} code in detail."
            },
            {
                "role": "user",
                "content": f"Please explain this code:\n\n```{language}\n{code}\n```"
            }
        ]
        
        return self._chat({
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 800
        })
    
    def _fix(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fix code issues"""
        code = params.get("code", "")
        error_message = params.get("error", "")
        language = params.get("language", "python")
        
        messages = [
            {
                "role": "system",
                "content": f"You are a helpful programming assistant. Fix the following {language} code and explain the changes."
            },
            {
                "role": "user",
                "content": f"Please fix this code:\n\n```{language}\n{code}\n```\n\nError: {error_message}"
            }
        ]
        
        return self._chat({
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1000
        })
    
    def _generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code from description"""
        description = params.get("description", "")
        language = params.get("language", "python")
        context = params.get("context", "")
        
        messages = [
            {
                "role": "system",
                "content": f"You are a helpful programming assistant. Generate {language} code based on the description."
            },
            {
                "role": "user",
                "content": f"Generate {language} code for: {description}\n\nContext: {context}"
            }
        ]
        
        return self._chat({
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1000
        })
    
    def cleanup(self):
        """Cleanup resources"""
        self.api_key = None
        self.github_token = None
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = GitHubCopilotPlugin
PLUGIN_NAME = "github_copilot"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with GitHub Copilot API for code completion and chat"
PLUGIN_ACTIONS = ["complete", "chat", "explain", "fix", "generate"]