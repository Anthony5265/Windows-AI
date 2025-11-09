"""
PrivateGPT Plugin for Windows AI
Supports private document Q&A with local LLMs
"""

import json
import requests
import asyncio
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging
import os

class PrivateGPTPlugin:
    """PrivateGPT integration plugin for document Q&A"""

    def __init__(self):
        self.name = "privategpt"
        self.version = "1.0.0"
        self.description = "PrivateGPT local document Q&A with LLMs"
        self.logger = logging.getLogger(__name__)

        # Default PrivateGPT settings
        self.default_settings = {
            "api_url": "http://localhost:8001",
            "timeout": 300,
            "use_context": True,
            "include_sources": False,
            "stream": False
        }

        self.settings = self.default_settings.copy()
        self.session = requests.Session()

    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin with configuration"""
        try:
            self.settings.update(config.get("privategpt", {}))

            # Test connection to PrivateGPT
            if self._test_connection():
                self.logger.info("PrivateGPT plugin initialized successfully")
                return True
            else:
                self.logger.warning("Could not connect to PrivateGPT server")
                return False

        except Exception as e:
            self.logger.error(f"Failed to initialize PrivateGPT plugin: {e}")
            return False

    def _test_connection(self) -> bool:
        """Test connection to PrivateGPT server"""
        try:
            response = self.session.get(f"{self.settings['api_url']}/health", timeout=10)
            return response.status_code == 200
        except:
            return False

    def ingest_file(self, file_path: str) -> Dict[str, Any]:
        """Ingest a document file"""
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }

            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                response = self.session.post(
                    f"{self.settings['api_url']}/v1/ingest/file",
                    files=files,
                    timeout=self.settings['timeout']
                )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "documents": result.get("data", []),
                    "message": f"Successfully ingested {len(result.get('data', []))} documents"
                }
            else:
                return {
                    "success": False,
                    "error": f"Ingestion failed: {response.status_code} - {response.text}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def ingest_text(self, text: str, file_name: Optional[str] = None) -> Dict[str, Any]:
        """Ingest text content"""
        try:
            data = {
                "text": text,
                "file_name": file_name or "text_document.txt"
            }

            response = self.session.post(
                f"{self.settings['api_url']}/v1/ingest/text",
                json=data,
                timeout=self.settings['timeout']
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "documents": result.get("data", []),
                    "message": f"Successfully ingested text"
                }
            else:
                return {
                    "success": False,
                    "error": f"Text ingestion failed: {response.status_code} - {response.text}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def list_ingested(self) -> Dict[str, Any]:
        """List all ingested documents"""
        try:
            response = self.session.get(
                f"{self.settings['api_url']}/v1/ingest/list",
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "documents": result.get("data", []),
                    "total": len(result.get("data", []))
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to list documents: {response.status_code}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def delete_ingested(self, doc_ids: List[str]) -> Dict[str, Any]:
        """Delete ingested documents"""
        try:
            data = {"doc_ids": doc_ids}
            response = self.session.delete(
                f"{self.settings['api_url']}/v1/ingest/delete",
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Successfully deleted {len(doc_ids)} documents"
                }
            else:
                return {
                    "success": False,
                    "error": f"Deletion failed: {response.status_code} - {response.text}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Chat completion with document context"""
        try:
            # Prepare request data
            data = {
                "messages": messages,
                "use_context": kwargs.get("use_context", self.settings["use_context"]),
                "include_sources": kwargs.get("include_sources", self.settings["include_sources"]),
                "stream": kwargs.get("stream", self.settings["stream"])
            }

            # Add context filter if provided
            if kwargs.get("context_filter"):
                data["context_filter"] = kwargs["context_filter"]

            response = self.session.post(
                f"{self.settings['api_url']}/v1/chat/completions",
                json=data,
                timeout=self.settings['timeout']
            )

            if response.status_code == 200:
                result = response.json()
                choice = result.get("choices", [{}])[0]

                return {
                    "success": True,
                    "response": choice.get("message", {}).get("content", ""),
                    "model": result.get("model", "private-gpt"),
                    "usage": result.get("usage", {}),
                    "sources": choice.get("sources", []),
                    "finish_reason": choice.get("finish_reason")
                }
            else:
                return {
                    "success": False,
                    "error": f"Chat completion failed: {response.status_code} - {response.text}"
                }

        except Exception as e:
            self.logger.error(f"Chat completion failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def stream_chat_completion(self, messages: List[Dict[str, str]], **kwargs):
        """Stream chat completion responses"""
        try:
            data = {
                "messages": messages,
                "use_context": kwargs.get("use_context", self.settings["use_context"]),
                "include_sources": kwargs.get("include_sources", self.settings["include_sources"]),
                "stream": True
            }

            if kwargs.get("context_filter"):
                data["context_filter"] = kwargs["context_filter"]

            response = self.session.post(
                f"{self.settings['api_url']}/v1/chat/completions",
                json=data,
                stream=True,
                timeout=self.settings['timeout']
            )

            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_chunk = line[6:]
                            if data_chunk != '[DONE]':
                                try:
                                    chunk = json.loads(data_chunk)
                                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                                except json.JSONDecodeError:
                                    continue
            else:
                yield f"Error: Chat completion failed {response.status_code}"

        except Exception as e:
            yield f"Error: {str(e)}"

    def get_chunks(self, text: str, **kwargs) -> Dict[str, Any]:
        """Retrieve relevant chunks for a query"""
        try:
            data = {
                "text": text,
                "limit": kwargs.get("limit", 10)
            }

            if kwargs.get("context_filter"):
                data["context_filter"] = kwargs["context_filter"]

            if kwargs.get("prev_next_chunks"):
                data["prev_next_chunks"] = kwargs["prev_next_chunks"]

            response = self.session.post(
                f"{self.settings['api_url']}/v1/chunks",
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "chunks": result.get("data", []),
                    "total": len(result.get("data", []))
                }
            else:
                return {
                    "success": False,
                    "error": f"Chunk retrieval failed: {response.status_code} - {response.text}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_model_status(self) -> Dict[str, Any]:
        """Get PrivateGPT server status"""
        try:
            response = self.session.get(f"{self.settings['api_url']}/health", timeout=10)
            if response.status_code == 200:
                return {
                    "success": True,
                    "server_running": True,
                    "status": "healthy"
                }
            else:
                return {
                    "success": False,
                    "server_running": False,
                    "error": f"Server returned {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "server_running": False,
                "error": str(e)
            }

    def update_settings(self, new_settings: Dict[str, Any]) -> bool:
        """Update plugin settings"""
        try:
            self.settings.update(new_settings)
            return True
        except Exception as e:
            self.logger.error(f"Failed to update settings: {e}")
            return False

    def get_settings(self) -> Dict[str, Any]:
        """Get current plugin settings"""
        return self.settings.copy()

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a PrivateGPT action"""
        if action == "ingest_file":
            return self.ingest_file(params.get("file_path", ""))
        elif action == "ingest_text":
            return self.ingest_text(params.get("text", ""), params.get("file_name"))
        elif action == "list_ingested":
            return self.list_ingested()
        elif action == "delete_ingested":
            return self.delete_ingested(params.get("doc_ids", []))
        elif action == "chat_completion":
            return asyncio.run(self.chat_completion(**params))
        elif action == "get_chunks":
            return self.get_chunks(**params)
        elif action == "get_model_status":
            return self.get_model_status()
        else:
            return {"error": f"Unknown action: {action}"}

    def cleanup(self):
        """Cleanup resources"""
        if self.session:
            self.session.close()

# Plugin registration
plugin = PrivateGPTPlugin()

def get_plugin():
    """Return plugin instance"""
    return plugin

def get_plugin_info():
    """Return plugin information"""
    return {
        "name": plugin.name,
        "version": plugin.version,
        "description": plugin.description,
        "type": "local_model",
        "capabilities": ["document_ingestion", "document_qa", "chat", "streaming", "context_retrieval"],
        "settings": plugin.default_settings
    }

# Plugin metadata for dynamic loading
PLUGIN_CLASS = PrivateGPTPlugin
PLUGIN_NAME = "privategpt"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "PrivateGPT local document Q&A with LLMs"
PLUGIN_ACTIONS = [
    "ingest_file", "ingest_text", "list_ingested", "delete_ingested",
    "chat_completion", "get_chunks", "get_model_status"
]