"""
Ollama Plugin - Production-Grade Local LLM Integration
Comprehensive integration with Ollama for local AI model management and inference

Features:
- Model management (list, pull, delete, show info)
- Chat with conversation history and streaming
- Text generation
- Embeddings generation
- Model information and status
- Multi-model support

Author: Windows AI Team
Version: 2.0.0
"""

from typing import Dict, Any, List, Optional
import logging
import asyncio
import httpx
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class Plugin:
    """Production-grade Ollama plugin for local LLM operations"""

    def __init__(self):
        self.name = "Ollama Local Models"
        self.version = "2.0.0"
        self.description = "Complete Ollama integration for local AI models - chat, embeddings, model management"
        self.author = "Windows AI Team"
        self.type = "integration"

        # Configuration
        self.base_url = "http://localhost:11434"
        self.timeout = 120.0

        # State
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
        self.available_models: List[str] = []

    def get_metadata(self) -> Dict[str, Any]:
        """Get plugin metadata"""
        return {
            "id": "ollama_local",
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "type": self.type,
            "enabled": True
        }

    def get_schema(self) -> Dict[str, Any]:
        """Get plugin action schema"""
        return {
            "actions": [
                {
                    "name": "list_models",
                    "description": "List all available Ollama models",
                    "parameters": {}
                },
                {
                    "name": "pull_model",
                    "description": "Download a model from Ollama library",
                    "parameters": {
                        "model": {"type": "string", "required": True, "description": "Model name (e.g., llama2, mistral, codellama)"}
                    }
                },
                {
                    "name": "delete_model",
                    "description": "Delete a model from local storage",
                    "parameters": {
                        "model": {"type": "string", "required": True, "description": "Model name to delete"}
                    }
                },
                {
                    "name": "show_model",
                    "description": "Show detailed information about a model",
                    "parameters": {
                        "model": {"type": "string", "required": True, "description": "Model name"}
                    }
                },
                {
                    "name": "chat",
                    "description": "Chat with a local model with conversation history",
                    "parameters": {
                        "model": {"type": "string", "required": True, "description": "Model name"},
                        "message": {"type": "string", "required": True, "description": "User message"},
                        "conversation_id": {"type": "string", "required": False, "description": "Conversation ID for history"},
                        "stream": {"type": "boolean", "required": False, "description": "Enable streaming"},
                        "temperature": {"type": "number", "required": False, "description": "Temperature (0-2)"},
                        "system_prompt": {"type": "string", "required": False, "description": "System prompt"}
                    }
                },
                {
                    "name": "generate",
                    "description": "Generate text completion",
                    "parameters": {
                        "model": {"type": "string", "required": True},
                        "prompt": {"type": "string", "required": True},
                        "stream": {"type": "boolean", "required": False},
                        "temperature": {"type": "number", "required": False}
                    }
                },
                {
                    "name": "embeddings",
                    "description": "Generate embeddings for text",
                    "parameters": {
                        "model": {"type": "string", "required": True, "description": "Model name (use embedding models)"},
                        "text": {"type": "string", "required": True, "description": "Text to embed"}
                    }
                },
                {
                    "name": "check_status",
                    "description": "Check if Ollama is running and accessible",
                    "parameters": {}
                }
            ]
        }

    async def execute(self, action: str = "chat", **kwargs) -> Dict[str, Any]:
        """Execute a plugin action"""
        try:
            # Route to appropriate action handler
            action_map = {
                "list_models": self._list_models,
                "pull_model": self._pull_model,
                "delete_model": self._delete_model,
                "show_model": self._show_model,
                "chat": self._chat,
                "generate": self._generate,
                "embeddings": self._embeddings,
                "check_status": self._check_status
            }

            if action not in action_map:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}. Available actions: {list(action_map.keys())}"
                }

            # Check Ollama is running (except for check_status)
            if action != "check_status":
                status = await self._check_status()
                if status["status"] != "success":
                    return {
                        "status": "error",
                        "message": "Ollama is not running. Please start Ollama first."
                    }

            # Execute action
            handler = action_map[action]
            return await handler(**kwargs)

        except Exception as e:
            logger.error(f"Ollama plugin error: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error executing {action}: {str(e)}"
            }

    # =========================================================================
    # Model Management Actions
    # =========================================================================

    async def _list_models(self, **kwargs) -> Dict[str, Any]:
        """List all available local models"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")

                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])

                    self.available_models = [m["name"] for m in models]

                    return {
                        "status": "success",
                        "models": models,
                        "count": len(models),
                        "model_names": self.available_models
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Failed to list models: HTTP {response.status_code}"
                    }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error listing models: {str(e)}"
            }

    async def _pull_model(self, model: str, **kwargs) -> Dict[str, Any]:
        """Pull/download a model from Ollama library"""
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": model},
                    timeout=600.0
                )

                if response.status_code == 200:
                    # Read streaming response
                    progress_data = []
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                progress = json.loads(line)
                                progress_data.append(progress)
                            except:
                                pass

                    return {
                        "status": "success",
                        "message": f"Model {model} downloaded successfully",
                        "model": model,
                        "progress": progress_data
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Failed to pull model: HTTP {response.status_code}"
                    }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error pulling model: {str(e)}"
            }

    async def _delete_model(self, model: str, **kwargs) -> Dict[str, Any]:
        """Delete a model from local storage"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.base_url}/api/delete",
                    json={"name": model}
                )

                if response.status_code == 200:
                    return {
                        "status": "success",
                        "message": f"Model {model} deleted successfully",
                        "model": model
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Failed to delete model: HTTP {response.status_code}"
                    }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error deleting model: {str(e)}"
            }

    async def _show_model(self, model: str, **kwargs) -> Dict[str, Any]:
        """Show detailed information about a model"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/show",
                    json={"name": model}
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "success",
                        "model": model,
                        "info": data
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Failed to get model info: HTTP {response.status_code}"
                    }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting model info: {str(e)}"
            }

    # =========================================================================
    # Inference Actions
    # =========================================================================

    async def _chat(self, model: str, message: str, conversation_id: Optional[str] = None,
                    stream: bool = False, temperature: float = 0.7,
                    system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Chat with a local model with conversation history"""
        try:
            # Initialize conversation if needed
            if conversation_id and conversation_id not in self.conversation_history:
                self.conversation_history[conversation_id] = []
                if system_prompt:
                    self.conversation_history[conversation_id].append({
                        "role": "system",
                        "content": system_prompt
                    })

            # Add user message to history
            if conversation_id:
                self.conversation_history[conversation_id].append({
                    "role": "user",
                    "content": message
                })
                messages = self.conversation_history[conversation_id]
            else:
                messages = [{"role": "user", "content": message}]
                if system_prompt:
                    messages.insert(0, {"role": "system", "content": system_prompt})

            # Call Ollama API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": stream,
                        "options": {
                            "temperature": temperature
                        }
                    },
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    if stream:
                        # Handle streaming response
                        full_response = ""
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    chunk = json.loads(line)
                                    if "message" in chunk:
                                        content = chunk["message"].get("content", "")
                                        full_response += content
                                except:
                                    pass

                        response_text = full_response
                    else:
                        # Handle non-streaming response
                        data = response.json()
                        response_text = data.get("message", {}).get("content", "")

                    # Add assistant response to history
                    if conversation_id:
                        self.conversation_history[conversation_id].append({
                            "role": "assistant",
                            "content": response_text
                        })

                    return {
                        "status": "success",
                        "response": response_text,
                        "model": model,
                        "conversation_id": conversation_id
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Chat failed: HTTP {response.status_code}"
                    }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Chat error: {str(e)}"
            }

    async def _generate(self, model: str, prompt: str, stream: bool = False,
                       temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """Generate text completion"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": stream,
                        "options": {
                            "temperature": temperature
                        }
                    },
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    if stream:
                        full_response = ""
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    chunk = json.loads(line)
                                    full_response += chunk.get("response", "")
                                except:
                                    pass
                        generated_text = full_response
                    else:
                        data = response.json()
                        generated_text = data.get("response", "")

                    return {
                        "status": "success",
                        "generated_text": generated_text,
                        "model": model
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Generation failed: HTTP {response.status_code}"
                    }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Generation error: {str(e)}"
            }

    async def _embeddings(self, model: str, text: str, **kwargs) -> Dict[str, Any]:
        """Generate embeddings for text"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={
                        "model": model,
                        "prompt": text
                    },
                    timeout=60.0
                )

                if response.status_code == 200:
                    data = response.json()
                    embeddings = data.get("embedding", [])

                    return {
                        "status": "success",
                        "embeddings": embeddings,
                        "dimension": len(embeddings),
                        "model": model
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Embeddings failed: HTTP {response.status_code}"
                    }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Embeddings error: {str(e)}"
            }

    # =========================================================================
    # Utility Actions
    # =========================================================================

    async def _check_status(self, **kwargs) -> Dict[str, Any]:
        """Check if Ollama is running and accessible"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")

                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])

                    return {
                        "status": "success",
                        "message": "Ollama is running",
                        "url": self.base_url,
                        "models_count": len(models)
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Ollama returned HTTP {response.status_code}"
                    }

        except httpx.ConnectError:
            return {
                "status": "error",
                "message": f"Cannot connect to Ollama at {self.base_url}. Make sure Ollama is running."
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Status check failed: {str(e)}"
            }

    # =========================================================================
    # Conversation Management
    # =========================================================================

    def clear_conversation(self, conversation_id: str):
        """Clear conversation history"""
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]

    def get_conversation(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get conversation history"""
        return self.conversation_history.get(conversation_id, [])


# Example usage
if __name__ == "__main__":
    async def test_plugin():
        plugin = Plugin()

        # Check status
        print("Checking Ollama status...")
        status = await plugin.execute(action="check_status")
        print(f"Status: {status}")

        # List models
        print("\nListing models...")
        models = await plugin.execute(action="list_models")
        print(f"Models: {models}")

        # Chat example
        if models.get("count", 0) > 0:
            model_name = models["model_names"][0]
            print(f"\nChatting with {model_name}...")
            chat_response = await plugin.execute(
                action="chat",
                model=model_name,
                message="Hello! Can you explain what you are in one sentence?",
                conversation_id="test-conv-1"
            )
            print(f"Response: {chat_response}")

    asyncio.run(test_plugin())
