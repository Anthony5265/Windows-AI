"""
SuperAGI Model Provider Plugin
Supports SuperAGI autonomous agents via API
"""

from typing import Dict, Any, Optional, List
import os


class SuperagiPlugin:
    """Plugin for SuperAGI autonomous agents"""

    name = "superagi"
    version = "1.0.0"
    description = "Integration with SuperAGI autonomous agents"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.base_url: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the SuperAGI plugin"""
        try:
            import requests

            # Get configuration from config or environment
            self.api_key = (
                config.get("api_key") if config
                else os.getenv("SUPERAGI_API_KEY")
            )
            self.base_url = (
                config.get("base_url", "https://api.superagi.com") if config
                else os.getenv("SUPERAGI_BASE_URL", "https://api.superagi.com")
            )

            if not self.api_key:
                return False

            # Store requests session for reuse
            self.client = requests.Session()
            self.client.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            })

            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing SuperAGI plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a SuperAGI action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}

        try:
            if action == "chat":
                return self._chat(params)
            elif action == "agent_run":
                return self._agent_run(params)
            elif action == "list_agents":
                return self._list_agents()
            elif action == "create_agent":
                return self._create_agent(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat with a SuperAGI agent"""
        agent_id = params.get("agent_id")
        if not agent_id:
            return {"error": "agent_id is required for chat"}

        message = params.get("message", "")
        model = params.get("model", "gpt-4")  # Default model
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 1000)

        payload = {
            "agent_id": agent_id,
            "message": message,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        response = self.client.post(f"{self.base_url}/chat", json=payload)
        response.raise_for_status()

        result = response.json()
        return {
            "response": result.get("response", ""),
            "agent_id": agent_id,
            "model": model,
            "usage": result.get("usage", {}),
            "metadata": result.get("metadata", {})
        }

    def _agent_run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a SuperAGI agent with goals/tasks"""
        agent_id = params.get("agent_id")
        if not agent_id:
            return {"error": "agent_id is required for agent_run"}

        goals = params.get("goals", [])
        tools = params.get("tools", [])
        max_iterations = params.get("max_iterations", 10)

        payload = {
            "agent_id": agent_id,
            "goals": goals,
            "tools": tools,
            "max_iterations": max_iterations
        }

        response = self.client.post(f"{self.base_url}/agent/run", json=payload)
        response.raise_for_status()

        result = response.json()
        return {
            "agent_id": agent_id,
            "status": result.get("status", "completed"),
            "results": result.get("results", []),
            "iterations": result.get("iterations", 0),
            "execution_time": result.get("execution_time", 0)
        }

    def _list_agents(self) -> Dict[str, Any]:
        """List available SuperAGI agents"""
        response = self.client.get(f"{self.base_url}/agents")
        response.raise_for_status()

        result = response.json()
        return {
            "agents": result.get("agents", []),
            "count": len(result.get("agents", []))
        }

    def _create_agent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new SuperAGI agent"""
        name = params.get("name")
        if not name:
            return {"error": "name is required for agent creation"}

        description = params.get("description", "")
        model = params.get("model", "gpt-4")
        tools = params.get("tools", [])
        goals = params.get("goals", [])

        payload = {
            "name": name,
            "description": description,
            "model": model,
            "tools": tools,
            "goals": goals
        }

        response = self.client.post(f"{self.base_url}/agents", json=payload)
        response.raise_for_status()

        result = response.json()
        return {
            "agent_id": result.get("agent_id"),
            "name": name,
            "status": "created",
            "created_at": result.get("created_at")
        }

    def cleanup(self):
        """Cleanup resources"""
        if self.client:
            self.client.close()
        self.client = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = SuperagiPlugin
PLUGIN_NAME = "superagi"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with SuperAGI autonomous agents"
PLUGIN_ACTIONS = ["chat", "agent_run", "list_agents", "create_agent"]