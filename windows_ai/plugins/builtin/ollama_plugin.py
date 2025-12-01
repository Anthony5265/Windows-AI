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
                },
                {
                    "name": "batch_embeddings",
                    "description": "Generate embeddings for multiple texts efficiently",
                    "parameters": {
                        "model": {"type": "string", "required": True, "description": "Embedding model (e.g., nomic-embed-text)"},
                        "texts": {"type": "array", "required": True, "description": "List of texts to embed"},
                        "batch_size": {"type": "number", "required": False, "description": "Batch size (default: 10)"}
                    }
                },
                {
                    "name": "rag_query",
                    "description": "Perform RAG query on documents",
                    "parameters": {
                        "query": {"type": "string", "required": True, "description": "User query"},
                        "documents": {"type": "array", "required": True, "description": "List of documents to search"},
                        "model": {"type": "string", "required": False, "description": "LLM model (default: llama3.2:3b)"},
                        "embed_model": {"type": "string", "required": False, "description": "Embedding model (default: nomic-embed-text)"},
                        "top_k": {"type": "number", "required": False, "description": "Number of chunks to retrieve (default: 3)"}
                    }
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
                "check_status": self._check_status,
                "batch_embeddings": self.batch_embeddings,
                "rag_query": self.rag_query
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
    # Advanced Embeddings and RAG Support
    # =========================================================================

    async def batch_embeddings(self, model: str, texts: List[str],
                              batch_size: int = 10) -> Dict[str, Any]:
        """
        Generate embeddings for multiple texts efficiently

        Args:
            model: Embedding model name (e.g., nomic-embed-text)
            texts: List of texts to embed
            batch_size: Number of texts to process concurrently

        Returns:
            Dictionary with embeddings array and metadata
        """
        try:
            all_embeddings = []
            failed_indices = []

            # Process in batches to avoid overwhelming the server
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                tasks = [self._embeddings(model=model, text=text) for text in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for j, result in enumerate(results):
                    if isinstance(result, Exception):
                        failed_indices.append(i + j)
                        all_embeddings.append(None)
                    elif result.get("status") == "success":
                        all_embeddings.append(result["embeddings"])
                    else:
                        failed_indices.append(i + j)
                        all_embeddings.append(None)

            success_count = len([e for e in all_embeddings if e is not None])

            return {
                "status": "success" if success_count > 0 else "error",
                "embeddings": all_embeddings,
                "total": len(texts),
                "success_count": success_count,
                "failed_indices": failed_indices,
                "dimension": len(all_embeddings[0]) if all_embeddings and all_embeddings[0] else 0,
                "model": model
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Batch embeddings error: {str(e)}"
            }

    async def similarity_search(self, query_embedding: List[float],
                               document_embeddings: List[List[float]],
                               top_k: int = 5) -> Dict[str, Any]:
        """
        Find most similar documents using cosine similarity

        Args:
            query_embedding: Query embedding vector
            document_embeddings: List of document embedding vectors
            top_k: Number of top results to return

        Returns:
            Dictionary with top matching indices and similarity scores
        """
        try:
            import numpy as np

            query = np.array(query_embedding)
            docs = np.array(document_embeddings)

            # Compute cosine similarity
            query_norm = query / np.linalg.norm(query)
            docs_norm = docs / np.linalg.norm(docs, axis=1, keepdims=True)
            similarities = np.dot(docs_norm, query_norm)

            # Get top k indices
            top_indices = np.argsort(similarities)[::-1][:top_k]
            top_scores = similarities[top_indices]

            results = [
                {"index": int(idx), "score": float(score)}
                for idx, score in zip(top_indices, top_scores)
            ]

            return {
                "status": "success",
                "results": results,
                "top_k": len(results)
            }

        except ImportError:
            return {
                "status": "error",
                "message": "NumPy is required for similarity search. Install with: pip install numpy"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Similarity search error: {str(e)}"
            }

    async def embed_documents_for_rag(self, documents: List[str],
                                     model: str = "nomic-embed-text",
                                     chunk_size: int = 512,
                                     overlap: int = 50) -> Dict[str, Any]:
        """
        Embed documents with chunking for RAG applications

        Args:
            documents: List of document texts
            model: Embedding model to use
            chunk_size: Maximum characters per chunk
            overlap: Character overlap between chunks

        Returns:
            Dictionary with embeddings, chunks, and metadata
        """
        try:
            # Chunk documents
            all_chunks = []
            chunk_metadata = []

            for doc_idx, doc in enumerate(documents):
                # Simple chunking by character count
                chunks = []
                start = 0
                while start < len(doc):
                    end = start + chunk_size
                    chunk = doc[start:end]
                    chunks.append(chunk)
                    chunk_metadata.append({
                        "doc_index": doc_idx,
                        "chunk_index": len(chunks) - 1,
                        "start": start,
                        "end": min(end, len(doc))
                    })
                    start = end - overlap if end < len(doc) else len(doc)

                all_chunks.extend(chunks)

            # Generate embeddings for all chunks
            embed_result = await self.batch_embeddings(model, all_chunks)

            if embed_result["status"] != "success":
                return embed_result

            return {
                "status": "success",
                "embeddings": embed_result["embeddings"],
                "chunks": all_chunks,
                "metadata": chunk_metadata,
                "total_chunks": len(all_chunks),
                "total_documents": len(documents),
                "model": model,
                "dimension": embed_result.get("dimension", 0)
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Document embedding error: {str(e)}"
            }

    async def rag_query(self, query: str, documents: List[str],
                       model: str = "llama3.2:3b",
                       embed_model: str = "nomic-embed-text",
                       top_k: int = 3) -> Dict[str, Any]:
        """
        Perform RAG (Retrieval-Augmented Generation) query

        Args:
            query: User query
            documents: List of documents to search
            model: LLM model for generation
            embed_model: Embedding model for retrieval
            top_k: Number of relevant chunks to retrieve

        Returns:
            Dictionary with answer and retrieved context
        """
        try:
            # Embed query
            query_result = await self._embeddings(model=embed_model, text=query)
            if query_result["status"] != "success":
                return query_result

            query_embedding = query_result["embeddings"]

            # Embed documents
            doc_result = await self.embed_documents_for_rag(
                documents=documents,
                model=embed_model
            )
            if doc_result["status"] != "success":
                return doc_result

            doc_embeddings = [e for e in doc_result["embeddings"] if e is not None]
            chunks = doc_result["chunks"]

            # Find most relevant chunks
            search_result = await self.similarity_search(
                query_embedding=query_embedding,
                document_embeddings=doc_embeddings,
                top_k=top_k
            )

            if search_result["status"] != "success":
                return search_result

            # Build context from top chunks
            context_chunks = [
                chunks[result["index"]]
                for result in search_result["results"]
            ]
            context = "\n\n".join(context_chunks)

            # Generate answer with context
            prompt = f"""Context information:
{context}

Question: {query}

Please answer the question based on the context provided above."""

            answer_result = await self._generate(
                model=model,
                prompt=prompt,
                temperature=0.7
            )

            if answer_result["status"] != "success":
                return answer_result

            return {
                "status": "success",
                "answer": answer_result["generated_text"],
                "context": context_chunks,
                "relevant_chunks": search_result["results"],
                "model": model,
                "embed_model": embed_model
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"RAG query error: {str(e)}"
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
