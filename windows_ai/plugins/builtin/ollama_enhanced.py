"""
Ollama Enhanced Plugin - Production-Grade Local LLM Integration
Comprehensive integration with Ollama for local AI model management and inference

Features:
- Model management (list, pull, delete, show info)
- Chat with conversation history and streaming
- Text generation and embeddings
- Model comparison and benchmarking
- Automatic model recommendations
- Performance monitoring
- Configuration persistence

Author: Windows AI Team
Version: 3.0.0
"""

from typing import Dict, Any, List, Optional
import logging
import asyncio
import httpx
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    """Ollama configuration"""
    base_url: str = "http://localhost:11434"
    timeout: float = 120.0
    default_model: str = "llama2"
    auto_pull: bool = False
    max_concurrent_requests: int = 3


@dataclass
class ModelBenchmark:
    """Model performance benchmark results"""
    model: str
    tokens_per_second: float
    response_time_ms: float
    memory_usage_mb: float
    timestamp: str


class OllamaEnhancedPlugin(IntegrationPlugin):
    """Enhanced Ollama integration plugin with advanced features"""

    def __init__(self):
        metadata = PluginMetadata(
            id="ollama_enhanced",
            name="Ollama Enhanced",
            description="Complete Ollama integration for local AI models - chat, embeddings, model management, benchmarking",
            version="3.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            enabled=True,
            icon="🦙",
            tags=["llm", "local", "ollama", "ai", "chat", "embeddings"],
            requirements=["httpx>=0.24.0"]
        )
        super().__init__(metadata)

        # Configuration
        self.config = OllamaConfig()

        # State
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
        self.available_models: List[Dict[str, Any]] = []
        self.benchmarks: List[ModelBenchmark] = []
        self.connected = False

    async def initialize(self) -> bool:
        """Initialize the plugin and check Ollama connection"""
        try:
            logger.info("Initializing Ollama Enhanced plugin...")

            # Check if Ollama is running
            status = await self._check_status()
            if status.get("status") == "success":
                self.connected = True
                logger.info("✓ Ollama is running and accessible")

                # Load available models
                models_result = await self._list_models()
                if models_result.get("status") == "success":
                    self.available_models = models_result.get("models", [])
                    logger.info(f"✓ Found {len(self.available_models)} available models")

                return True
            else:
                logger.warning("⚠ Ollama is not running. Plugin initialized but not connected.")
                return True  # Still initialize, but mark as not connected

        except Exception as e:
            logger.error(f"Error initializing Ollama plugin: {e}")
            return False

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """
        Connect to Ollama service (configure base URL if provided)

        Args:
            credentials: Dict with optional 'base_url' key
        """
        try:
            if "base_url" in credentials:
                self.config.base_url = credentials["base_url"]

            # Verify connection
            status = await self._check_status()
            self.connected = status.get("status") == "success"

            return self.connected

        except Exception as e:
            logger.error(f"Error connecting to Ollama: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from Ollama (cleanup)"""
        try:
            self.connected = False
            self.conversation_history.clear()
            logger.info("Disconnected from Ollama")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            return False

    async def execute(
        self,
        action: str,
        parameters: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute an Ollama action

        Args:
            action: Action to perform (list_models, chat, generate, etc.)
            parameters: Action-specific parameters
            **kwargs: Additional arguments
        """
        try:
            # Merge parameters and kwargs
            params = {**parameters, **kwargs}

            # Action routing
            action_map = {
                "list_models": self._list_models,
                "pull_model": self._pull_model,
                "delete_model": self._delete_model,
                "show_model": self._show_model,
                "chat": self._chat,
                "generate": self._generate,
                "embeddings": self._embeddings,
                "check_status": self._check_status,
                "benchmark_model": self._benchmark_model,
                "compare_models": self._compare_models,
                "recommend_model": self._recommend_model,
                "get_conversation": self._get_conversation,
                "clear_conversation": self._clear_conversation,
            }

            if action not in action_map:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}. Available: {list(action_map.keys())}"
                }

            # Check connection for most actions
            if action != "check_status" and not self.connected:
                status = await self._check_status()
                if status.get("status") != "success":
                    return {
                        "success": False,
                        "error": "Ollama is not running. Please start Ollama first.",
                        "hint": "Run 'ollama serve' in a terminal"
                    }
                self.connected = True

            # Execute action
            handler = action_map[action]
            result = await handler(**params)

            # Standardize response format
            if isinstance(result, dict) and "status" in result:
                success = result["status"] == "success"
                return {
                    "success": success,
                    "data": result if success else None,
                    "error": result.get("message") if not success else None
                }

            return result

        except Exception as e:
            logger.error(f"Error executing action {action}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Execution error: {str(e)}"
            }

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for the plugin's parameters"""
        return {
            "type": "object",
            "actions": {
                "list_models": {
                    "description": "List all available Ollama models",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                },
                "pull_model": {
                    "description": "Download a model from Ollama library",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "model": {
                                "type": "string",
                                "description": "Model name (e.g., llama2, mistral, codellama)"
                            }
                        },
                        "required": ["model"]
                    }
                },
                "chat": {
                    "description": "Chat with a local model",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "model": {"type": "string"},
                            "message": {"type": "string"},
                            "conversation_id": {"type": "string"},
                            "stream": {"type": "boolean"},
                            "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                            "system_prompt": {"type": "string"}
                        },
                        "required": ["model", "message"]
                    }
                },
                "benchmark_model": {
                    "description": "Benchmark model performance",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "model": {"type": "string"},
                            "test_prompt": {"type": "string"}
                        },
                        "required": ["model"]
                    }
                },
                "compare_models": {
                    "description": "Compare multiple models",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "models": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "test_prompt": {"type": "string"}
                        },
                        "required": ["models"]
                    }
                },
                "recommend_model": {
                    "description": "Get model recommendations based on use case",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "use_case": {
                                "type": "string",
                                "enum": ["chat", "code", "reasoning", "creative", "fast"]
                            }
                        },
                        "required": ["use_case"]
                    }
                }
            }
        }

    # =========================================================================
    # Model Management
    # =========================================================================

    async def _list_models(self, **kwargs) -> Dict[str, Any]:
        """List all available local models"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.config.base_url}/api/tags")

                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])

                    self.available_models = models

                    return {
                        "status": "success",
                        "models": models,
                        "count": len(models),
                        "model_names": [m["name"] for m in models]
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
        """Pull/download a model with progress tracking"""
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    f"{self.config.base_url}/api/pull",
                    json={"name": model},
                    timeout=600.0
                )

                if response.status_code == 200:
                    progress_data = []
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                progress = json.loads(line)
                                progress_data.append(progress)

                                # Log progress
                                if "status" in progress:
                                    logger.info(f"Pull progress: {progress['status']}")
                            except:
                                pass

                    # Refresh model list
                    await self._list_models()

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
                    f"{self.config.base_url}/api/delete",
                    json={"name": model}
                )

                if response.status_code == 200:
                    # Refresh model list
                    await self._list_models()

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
                    f"{self.config.base_url}/api/show",
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
    # Inference Operations
    # =========================================================================

    async def _chat(
        self,
        model: str,
        message: str,
        conversation_id: Optional[str] = None,
        stream: bool = False,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
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

            # Add user message
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

            # Call Ollama
            start_time = time.time()
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": stream,
                        "options": {"temperature": temperature}
                    },
                    timeout=self.config.timeout
                )

                if response.status_code == 200:
                    if stream:
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
                        data = response.json()
                        response_text = data.get("message", {}).get("content", "")

                    elapsed_time = time.time() - start_time

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
                        "conversation_id": conversation_id,
                        "response_time": elapsed_time
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

    async def _generate(
        self,
        model: str,
        prompt: str,
        stream: bool = False,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text completion"""
        try:
            start_time = time.time()
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": stream,
                        "options": {"temperature": temperature}
                    },
                    timeout=self.config.timeout
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

                    elapsed_time = time.time() - start_time

                    return {
                        "status": "success",
                        "generated_text": generated_text,
                        "model": model,
                        "response_time": elapsed_time
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
                    f"{self.config.base_url}/api/embeddings",
                    json={"model": model, "prompt": text},
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
    # Status & Utility
    # =========================================================================

    async def _check_status(self, **kwargs) -> Dict[str, Any]:
        """Check if Ollama is running"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.config.base_url}/api/tags")

                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])

                    return {
                        "status": "success",
                        "message": "Ollama is running",
                        "url": self.config.base_url,
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
                "message": f"Cannot connect to Ollama at {self.config.base_url}",
                "hint": "Make sure Ollama is running (try: ollama serve)"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Status check failed: {str(e)}"
            }

    # =========================================================================
    # Enhanced Features
    # =========================================================================

    async def _benchmark_model(
        self,
        model: str,
        test_prompt: str = "Write a short story about a robot.",
        **kwargs
    ) -> Dict[str, Any]:
        """Benchmark model performance"""
        try:
            logger.info(f"Benchmarking model: {model}")

            start_time = time.time()
            result = await self._generate(
                model=model,
                prompt=test_prompt,
                stream=False,
                temperature=0.7
            )
            end_time = time.time()

            if result.get("status") == "success":
                response_time_ms = (end_time - start_time) * 1000
                text = result.get("generated_text", "")
                tokens_estimate = len(text.split())
                tokens_per_second = tokens_estimate / (response_time_ms / 1000) if response_time_ms > 0 else 0

                benchmark = ModelBenchmark(
                    model=model,
                    tokens_per_second=tokens_per_second,
                    response_time_ms=response_time_ms,
                    memory_usage_mb=0.0,  # Would need system metrics for this
                    timestamp=datetime.now().isoformat()
                )

                self.benchmarks.append(benchmark)

                return {
                    "status": "success",
                    "benchmark": asdict(benchmark),
                    "test_prompt": test_prompt,
                    "generated_tokens": tokens_estimate
                }
            else:
                return result

        except Exception as e:
            return {
                "status": "error",
                "message": f"Benchmark error: {str(e)}"
            }

    async def _compare_models(
        self,
        models: List[str],
        test_prompt: str = "Explain quantum computing in simple terms.",
        **kwargs
    ) -> Dict[str, Any]:
        """Compare performance of multiple models"""
        try:
            logger.info(f"Comparing {len(models)} models")

            comparisons = []
            for model in models:
                result = await self._benchmark_model(model=model, test_prompt=test_prompt)
                if result.get("status") == "success":
                    comparisons.append(result["benchmark"])

            # Sort by tokens per second
            comparisons.sort(key=lambda x: x["tokens_per_second"], reverse=True)

            return {
                "status": "success",
                "comparisons": comparisons,
                "fastest_model": comparisons[0]["model"] if comparisons else None,
                "test_prompt": test_prompt
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Comparison error: {str(e)}"
            }

    async def _recommend_model(self, use_case: str, **kwargs) -> Dict[str, Any]:
        """Recommend models based on use case"""
        try:
            recommendations = {
                "chat": {
                    "models": ["llama2", "mistral", "neural-chat"],
                    "reason": "Optimized for conversational interactions"
                },
                "code": {
                    "models": ["codellama", "deepseek-coder", "starcoder"],
                    "reason": "Specialized for code generation and understanding"
                },
                "reasoning": {
                    "models": ["mistral", "mixtral", "llama2:70b"],
                    "reason": "Strong logical reasoning capabilities"
                },
                "creative": {
                    "models": ["llama2", "vicuna", "nous-hermes"],
                    "reason": "Creative writing and storytelling"
                },
                "fast": {
                    "models": ["tinyllama", "phi", "orca-mini"],
                    "reason": "Fast inference with smaller models"
                }
            }

            if use_case not in recommendations:
                return {
                    "status": "error",
                    "message": f"Unknown use case: {use_case}",
                    "available_cases": list(recommendations.keys())
                }

            rec = recommendations[use_case]

            # Check which recommended models are installed
            installed = [m["name"] for m in self.available_models]
            available_recommended = [m for m in rec["models"] if any(m in inst for inst in installed)]
            not_installed = [m for m in rec["models"] if m not in available_recommended]

            return {
                "status": "success",
                "use_case": use_case,
                "recommended_models": rec["models"],
                "reason": rec["reason"],
                "installed": available_recommended,
                "not_installed": not_installed
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Recommendation error: {str(e)}"
            }

    # =========================================================================
    # Conversation Management
    # =========================================================================

    async def _get_conversation(self, conversation_id: str, **kwargs) -> Dict[str, Any]:
        """Get conversation history"""
        if conversation_id in self.conversation_history:
            return {
                "status": "success",
                "conversation_id": conversation_id,
                "messages": self.conversation_history[conversation_id]
            }
        else:
            return {
                "status": "error",
                "message": f"Conversation not found: {conversation_id}"
            }

    async def _clear_conversation(self, conversation_id: str, **kwargs) -> Dict[str, Any]:
        """Clear conversation history"""
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]
            return {
                "status": "success",
                "message": f"Conversation cleared: {conversation_id}"
            }
        else:
            return {
                "status": "error",
                "message": f"Conversation not found: {conversation_id}"
            }


# Export the plugin class
__all__ = ["OllamaEnhancedPlugin"]
