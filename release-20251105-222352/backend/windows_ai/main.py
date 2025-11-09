"""
Windows AI - Main FastAPI Backend Application

This is the central backend service that powers the Windows AI assistant.
It provides:
- Chat API with streaming support
- Integration with LiteLLM for multiple AI models
- Agent management and task execution
- File system operations
- System integration and monitoring
- WebSocket support for real-time communication
"""

import os
import json
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx

# Import automation systems
from windows_ai.folder_watcher import (
    FolderWatcherManager, WatcherConfig, EXAMPLE_WATCHERS
)
from windows_ai.scheduler import (
    TaskScheduler, ScheduledTask, EXAMPLE_TASKS
)

# Import plugin system
from windows_ai.plugins.registry import PluginRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Windows AI Backend",
    description="Central backend service for Windows AI assistant",
    version="0.1.0"
)

# Enable CORS for Electron app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATA_DIR = Path.home() / ".windows-ai"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHAT_HISTORY_FILE = DATA_DIR / "chat_history.json"
CONFIG_FILE = DATA_DIR / "config.json"
WATCHERS_CONFIG_FILE = DATA_DIR / "watchers.json"
SCHEDULER_CONFIG_FILE = DATA_DIR / "scheduler.json"
PLUGINS_DIR = Path(__file__).parent / "plugins" / "builtin"

# Agenthub URL
AGENTHUB_URL = os.getenv("AGENTHUB_URL", "http://localhost:8000")

# Windows AI Agent URL
AGENT_URL = os.getenv("AGENT_URL", "http://localhost:3001")

# =====================================================================
# Data Models
# =====================================================================

class ChatMessage(BaseModel):
    """Chat message model"""
    id: Optional[str] = None
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: Optional[str] = None
    model: Optional[str] = None

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    conversation_id: Optional[str] = None
    model: Optional[str] = "gpt-3.5-turbo"
    stream: bool = False
    temperature: float = 0.7
    max_tokens: Optional[int] = None

class ChatResponse(BaseModel):
    """Chat response model"""
    message: ChatMessage
    conversation_id: str

class AgentTaskRequest(BaseModel):
    """Agent task execution request"""
    task: str
    agent_type: Optional[str] = "general"
    parameters: Optional[Dict[str, Any]] = {}

class SystemInfoResponse(BaseModel):
    """System information response"""
    platform: str
    version: str
    memory: Dict[str, Any]
    cpu: Dict[str, Any]
    disk: Dict[str, Any]

class ConfigUpdate(BaseModel):
    """Configuration update model"""
    key: str
    value: Any

# =====================================================================
# Chat History Management
# =====================================================================

class ChatHistory:
    """Manages chat conversation history"""

    def __init__(self):
        self.conversations: Dict[str, List[ChatMessage]] = {}
        self.load_history()

    def load_history(self):
        """Load chat history from file"""
        try:
            if CHAT_HISTORY_FILE.exists():
                with open(CHAT_HISTORY_FILE, 'r') as f:
                    data = json.load(f)
                    self.conversations = data
                logger.info(f"Loaded chat history: {len(self.conversations)} conversations")
        except Exception as e:
            logger.error(f"Error loading chat history: {e}")
            self.conversations = {}

    def save_history(self):
        """Save chat history to file"""
        try:
            with open(CHAT_HISTORY_FILE, 'w') as f:
                json.dump(self.conversations, f, indent=2, default=str)
            logger.info("Saved chat history")
        except Exception as e:
            logger.error(f"Error saving chat history: {e}")

    def add_message(self, conversation_id: str, message: ChatMessage):
        """Add a message to a conversation"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        if message.timestamp is None:
            message.timestamp = datetime.now().isoformat()

        self.conversations[conversation_id].append(message.dict())
        self.save_history()

    def get_conversation(self, conversation_id: str) -> List[ChatMessage]:
        """Get all messages in a conversation"""
        return self.conversations.get(conversation_id, [])

    def get_all_conversations(self) -> Dict[str, List[ChatMessage]]:
        """Get all conversations"""
        return self.conversations

    def clear_conversation(self, conversation_id: str):
        """Clear a specific conversation"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            self.save_history()

# Initialize chat history
chat_history = ChatHistory()

# =====================================================================
# Configuration Management
# =====================================================================

class ConfigManager:
    """Manages application configuration"""

    def __init__(self):
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")

        # Default configuration
        return {
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": True,
            "theme": "dark",
            "auto_start": False,
            "notifications": True,
            "local_models": {
                "enabled": False,
                "ollama_url": "http://localhost:11434"
            }
        }

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Saved configuration")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
        self.save_config()

# Initialize config manager
config_manager = ConfigManager()

# Initialize automation systems
folder_watcher_manager = FolderWatcherManager(WATCHERS_CONFIG_FILE)
task_scheduler = TaskScheduler(SCHEDULER_CONFIG_FILE)

# Initialize plugin system
plugin_registry = PluginRegistry(PLUGINS_DIR)

# =====================================================================
# Automation Callbacks
# =====================================================================

async def handle_file_event(watcher_id: str, watcher_name: str, event_type: str,
                            file_path: str, action: str, custom_prompt: Optional[str]):
    """Handle file system events from folder watchers"""
    logger.info(f"File event: {event_type} - {file_path} (watcher: {watcher_name})")

    try:
        # Prepare prompt based on action
        if action == "organize":
            prompt = custom_prompt or f"Organize this file: {file_path}. Suggest an appropriate folder structure."
        elif action == "summarize":
            prompt = custom_prompt or f"Summarize the contents of this file: {file_path}"
        elif action == "analyze":
            prompt = custom_prompt or f"Analyze this file and provide insights: {file_path}"
        else:
            prompt = custom_prompt or f"Process this file: {file_path}"

        # Create a system message with file context
        messages = [
            {"role": "system", "content": f"File event: {event_type} on {file_path}"},
            {"role": "user", "content": prompt}
        ]

        # Call AI
        response = await call_llm(messages, model="gpt-3.5-turbo")

        logger.info(f"AI response for {file_path}: {response[:100]}...")

        # TODO: Store automation results or send notification

    except Exception as e:
        logger.error(f"Error handling file event: {e}")


async def handle_scheduled_task(task_id: str, task_name: str, action: str, prompt: str):
    """Handle scheduled task execution"""
    logger.info(f"Executing scheduled task: {task_name}")

    try:
        # Prepare messages
        messages = [
            {"role": "system", "content": f"Scheduled task: {task_name} (action: {action})"},
            {"role": "user", "content": prompt}
        ]

        # Call AI
        response = await call_llm(messages, model="gpt-3.5-turbo")

        logger.info(f"Task {task_name} completed: {response[:100]}...")

        # TODO: Store task results or send notification

    except Exception as e:
        logger.error(f"Error executing scheduled task: {e}")


# Set callbacks
folder_watcher_manager.set_event_callback(handle_file_event)
task_scheduler.set_task_callback(handle_scheduled_task)

# =====================================================================
# LiteLLM Integration
# =====================================================================

async def call_llm(messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo",
                   temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
    """
    Call LLM using LiteLLM library
    Supports OpenAI, Anthropic, Ollama, and many other providers
    """
    try:
        import litellm

        response = await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content
    except ImportError:
        logger.warning("litellm not installed, using fallback response")
        return "I'm the Windows AI assistant. LiteLLM is not installed, so I'm running in demo mode. Please install litellm to enable AI responses."
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        raise HTTPException(status_code=500, detail=f"Error calling LLM: {str(e)}")

async def stream_llm(messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo",
                     temperature: float = 0.7, max_tokens: Optional[int] = None):
    """
    Stream LLM response using LiteLLM
    """
    try:
        import litellm

        response = await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )

        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except ImportError:
        yield "LiteLLM not installed. Running in demo mode."
    except Exception as e:
        logger.error(f"Error streaming LLM: {e}")
        yield f"Error: {str(e)}"

# =====================================================================
# API Endpoints
# =====================================================================

@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "status": "running",
        "service": "Windows AI Backend",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "backend": "running",
            "agenthub": "checking...",
            "agent": "checking..."
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - process user message and return AI response
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or datetime.now().strftime("%Y%m%d%H%M%S")

        # Add user message to history
        user_message = ChatMessage(
            role="user",
            content=request.message,
            timestamp=datetime.now().isoformat()
        )
        chat_history.add_message(conversation_id, user_message)

        # Get conversation history for context
        history = chat_history.get_conversation(conversation_id)
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in history[-10:]]  # Last 10 messages

        # Get AI response
        if request.stream:
            # For streaming, we need to use SSE endpoint instead
            raise HTTPException(status_code=400, detail="Use /chat/stream endpoint for streaming responses")
        else:
            response_text = await call_llm(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )

        # Add assistant message to history
        assistant_message = ChatMessage(
            role="assistant",
            content=response_text,
            timestamp=datetime.now().isoformat(),
            model=request.model
        )
        chat_history.add_message(conversation_id, assistant_message)

        return ChatResponse(
            message=assistant_message,
            conversation_id=conversation_id
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint - returns Server-Sent Events stream
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or datetime.now().strftime("%Y%m%d%H%M%S")

        # Add user message to history
        user_message = ChatMessage(
            role="user",
            content=request.message,
            timestamp=datetime.now().isoformat()
        )
        chat_history.add_message(conversation_id, user_message)

        # Get conversation history for context
        history = chat_history.get_conversation(conversation_id)
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in history[-10:]]

        async def generate():
            """Generate streaming response"""
            full_response = ""
            async for chunk in stream_llm(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            ):
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk, 'conversation_id': conversation_id})}\n\n"

            # Add complete response to history
            assistant_message = ChatMessage(
                role="assistant",
                content=full_response,
                timestamp=datetime.now().isoformat(),
                model=request.model
            )
            chat_history.add_message(conversation_id, assistant_message)

            # Send done event
            yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Error in chat stream endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations")
async def get_conversations():
    """Get all conversations"""
    return {
        "conversations": chat_history.get_all_conversations(),
        "count": len(chat_history.conversations)
    }

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a specific conversation"""
    conversation = chat_history.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation_id": conversation_id, "messages": conversation}

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    chat_history.clear_conversation(conversation_id)
    return {"status": "deleted", "conversation_id": conversation_id}

@app.post("/agent/execute")
async def execute_agent_task(request: AgentTaskRequest):
    """
    Execute a task using the Windows AI agent
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AGENT_URL}/execute",
                json=request.dict(),
                timeout=30.0
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error executing agent task: {e}")
        return {"error": str(e), "status": "failed"}

@app.get("/system/info")
async def get_system_info():
    """Get system information"""
    try:
        from . import system_info
        info = system_info.get_system_info()
        return info
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {"error": str(e)}

@app.get("/config")
async def get_config():
    """Get current configuration"""
    return config_manager.config

@app.post("/config")
async def update_config(update: ConfigUpdate):
    """Update configuration"""
    config_manager.set(update.key, update.value)
    return {"status": "updated", "key": update.key, "value": update.value}

@app.get("/models")
async def list_models():
    """List available AI models"""
    return {
        "models": [
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "OpenAI"},
            {"id": "gpt-4", "name": "GPT-4", "provider": "OpenAI"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "OpenAI"},
            {"id": "claude-3-opus", "name": "Claude 3 Opus", "provider": "Anthropic"},
            {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet", "provider": "Anthropic"},
            {"id": "ollama/llama2", "name": "Llama 2 (Local)", "provider": "Ollama"},
            {"id": "ollama/mistral", "name": "Mistral (Local)", "provider": "Ollama"},
        ]
    }

# =====================================================================
# Folder Watcher Endpoints
# =====================================================================

@app.get("/automation/watchers")
async def list_watchers():
    """List all folder watchers"""
    return {"watchers": folder_watcher_manager.list_watchers()}

@app.get("/automation/watchers/{watcher_id}")
async def get_watcher(watcher_id: str):
    """Get specific folder watcher"""
    watcher = folder_watcher_manager.get_watcher(watcher_id)
    if not watcher:
        raise HTTPException(status_code=404, detail="Watcher not found")
    return {
        **watcher.to_dict(),
        "running": watcher_id in folder_watcher_manager.observers
    }

@app.post("/automation/watchers")
async def create_watcher(watcher: Dict[str, Any]):
    """Create a new folder watcher"""
    try:
        config = WatcherConfig(**watcher)
        success = await folder_watcher_manager.add_watcher(config)
        if success:
            return {"message": "Watcher created successfully", "id": config.id}
        else:
            raise HTTPException(status_code=400, detail="Failed to create watcher")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/automation/watchers/{watcher_id}")
async def update_watcher(watcher_id: str, updates: Dict[str, Any]):
    """Update folder watcher configuration"""
    success = await folder_watcher_manager.update_watcher(watcher_id, updates)
    if success:
        return {"message": "Watcher updated successfully"}
    else:
        raise HTTPException(status_code=404, detail="Watcher not found")

@app.delete("/automation/watchers/{watcher_id}")
async def delete_watcher(watcher_id: str):
    """Delete a folder watcher"""
    success = await folder_watcher_manager.remove_watcher(watcher_id)
    if success:
        return {"message": "Watcher deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Watcher not found")

@app.post("/automation/watchers/{watcher_id}/start")
async def start_watcher(watcher_id: str):
    """Start a folder watcher"""
    success = await folder_watcher_manager.start_watcher(watcher_id)
    if success:
        return {"message": "Watcher started successfully"}
    else:
        raise HTTPException(status_code=404, detail="Watcher not found or already running")

@app.post("/automation/watchers/{watcher_id}/stop")
async def stop_watcher(watcher_id: str):
    """Stop a folder watcher"""
    success = await folder_watcher_manager.stop_watcher(watcher_id)
    if success:
        return {"message": "Watcher stopped successfully"}
    else:
        raise HTTPException(status_code=404, detail="Watcher not found or not running")

@app.get("/automation/watchers/examples/list")
async def get_example_watchers():
    """Get example watcher configurations"""
    return {"examples": EXAMPLE_WATCHERS}

# =====================================================================
# Scheduled Tasks Endpoints
# =====================================================================

@app.get("/automation/tasks")
async def list_tasks():
    """List all scheduled tasks"""
    return {"tasks": task_scheduler.list_tasks()}

@app.get("/automation/tasks/{task_id}")
async def get_task(task_id: str):
    """Get specific scheduled task"""
    task = task_scheduler.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()

@app.post("/automation/tasks")
async def create_task(task: Dict[str, Any]):
    """Create a new scheduled task"""
    try:
        config = ScheduledTask(**task)
        success = await task_scheduler.add_task(config)
        if success:
            return {"message": "Task created successfully", "id": config.id}
        else:
            raise HTTPException(status_code=400, detail="Failed to create task")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/automation/tasks/{task_id}")
async def update_task(task_id: str, updates: Dict[str, Any]):
    """Update scheduled task configuration"""
    success = await task_scheduler.update_task(task_id, updates)
    if success:
        return {"message": "Task updated successfully"}
    else:
        raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/automation/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a scheduled task"""
    success = await task_scheduler.remove_task(task_id)
    if success:
        return {"message": "Task deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Task not found")

@app.get("/automation/tasks/examples/list")
async def get_example_tasks():
    """Get example scheduled task configurations"""
    return {"examples": EXAMPLE_TASKS}

# =====================================================================
# Plugin System Endpoints
# =====================================================================

@app.get("/plugins")
async def list_plugins():
    """List all registered plugins"""
    return {"plugins": plugin_registry.list_plugins()}

@app.get("/plugins/{plugin_id}")
async def get_plugin(plugin_id: str):
    """Get specific plugin details"""
    plugin = plugin_registry.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {
        **plugin.metadata.to_dict(),
        "initialized": plugin.metadata.id in plugin_registry._initialized_plugins,
        "schema": plugin.get_schema()
    }

@app.post("/plugins/{plugin_id}/execute")
async def execute_plugin(plugin_id: str, request: Dict[str, Any]):
    """Execute a plugin"""
    result = await plugin_registry.execute_plugin(plugin_id, **request)
    return result

@app.post("/plugins/{plugin_id}/enable")
async def enable_plugin(plugin_id: str):
    """Enable a plugin"""
    success = await plugin_registry.enable_plugin(plugin_id)
    if success:
        return {"message": "Plugin enabled successfully"}
    else:
        raise HTTPException(status_code=404, detail="Plugin not found or failed to enable")

@app.post("/plugins/{plugin_id}/disable")
async def disable_plugin(plugin_id: str):
    """Disable a plugin"""
    success = await plugin_registry.disable_plugin(plugin_id)
    if success:
        return {"message": "Plugin disabled successfully"}
    else:
        raise HTTPException(status_code=404, detail="Plugin not found or failed to disable")

@app.post("/plugins/{plugin_id}/reload")
async def reload_plugin(plugin_id: str):
    """Reload a plugin from disk"""
    success = await plugin_registry.reload_plugin(plugin_id)
    if success:
        return {"message": "Plugin reloaded successfully"}
    else:
        raise HTTPException(status_code=404, detail="Plugin not found or failed to reload")

@app.get("/plugins/types/{plugin_type}")
async def get_plugins_by_type(plugin_type: str):
    """Get all plugins of a specific type"""
    try:
        from windows_ai.plugins.base import PluginType
        ptype = PluginType(plugin_type)
        plugins = plugin_registry.get_plugins_by_type(ptype)
        return {
            "type": plugin_type,
            "plugins": [p.metadata.to_dict() for p in plugins]
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plugin type")

# =====================================================================
# WebSocket Support
# =====================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time bidirectional communication
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Handle different message types
            if message_data.get("type") == "chat":
                # Process chat message
                request = ChatRequest(**message_data.get("data", {}))

                # Send response chunks
                conversation_id = request.conversation_id or datetime.now().strftime("%Y%m%d%H%M%S")

                # Add user message
                user_message = ChatMessage(
                    role="user",
                    content=request.message,
                    timestamp=datetime.now().isoformat()
                )
                chat_history.add_message(conversation_id, user_message)

                # Get history
                history = chat_history.get_conversation(conversation_id)
                messages = [{"role": msg["role"], "content": msg["content"]} for msg in history[-10:]]

                # Stream response
                full_response = ""
                async for chunk in stream_llm(messages=messages, model=request.model):
                    full_response += chunk
                    await websocket.send_json({
                        "type": "chat_chunk",
                        "chunk": chunk,
                        "conversation_id": conversation_id
                    })

                # Save complete response
                assistant_message = ChatMessage(
                    role="assistant",
                    content=full_response,
                    timestamp=datetime.now().isoformat(),
                    model=request.model
                )
                chat_history.add_message(conversation_id, assistant_message)

                # Send done signal
                await websocket.send_json({
                    "type": "chat_done",
                    "conversation_id": conversation_id
                })

            elif message_data.get("type") == "ping":
                # Respond to ping
                await websocket.send_json({"type": "pong"})

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("WebSocket connection closed")

# =====================================================================
# Startup/Shutdown Events
# =====================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Windows AI Backend starting up...")
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info(f"Chat history loaded: {len(chat_history.conversations)} conversations")

    # Start automation systems
    logger.info("Starting automation systems...")
    await folder_watcher_manager.start_all()
    logger.info(f"Folder watchers started: {len(folder_watcher_manager.observers)} active")

    await task_scheduler.start()
    logger.info(f"Task scheduler started: {len(task_scheduler.tasks)} tasks configured")

    # Load and initialize plugins
    logger.info("Loading plugins...")
    await plugin_registry.load_plugins()
    await plugin_registry.initialize_plugins()
    logger.info(f"Plugins loaded: {len(plugin_registry.plugins)} total, {len(plugin_registry._initialized_plugins)} initialized")

    logger.info("Backend is ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    logger.info("Windows AI Backend shutting down...")

    # Stop automation systems
    logger.info("Stopping automation systems...")
    await folder_watcher_manager.stop_all()
    await task_scheduler.stop()

    # Shutdown plugins
    logger.info("Shutting down plugins...")
    await plugin_registry.shutdown_plugins()

    # Save configurations
    chat_history.save_history()
    config_manager.save_config()

    logger.info("Shutdown complete")

# =====================================================================
# Main Entry Point
# =====================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8010"))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting Windows AI Backend on {host}:{port}")

    uvicorn.run(
        "windows_ai.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
