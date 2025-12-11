"""Frontend-specific API routes for plugins, models, and automation"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json

router = APIRouter()

# Sample plugin marketplace data
SAMPLE_PLUGINS = [
    {
        "id": "openai-gpt",
        "name": "OpenAI GPT",
        "description": "Access GPT-3.5, GPT-4, and other OpenAI models for chat, completion, and embeddings",
        "version": "1.0.0",
        "author": "Windows AI Team",
        "type": "integration",
        "category": "AI Models",
        "tags": ["ai", "nlp", "chat", "completion"],
        "enabled": False,
        "installed": False,
        "featured": True,
        "icon": "🤖",
        "requirements": ["openai>=1.0.0"],
        "config_required": ["api_key"]
    },
    {
        "id": "anthropic-claude",
        "name": "Anthropic Claude",
        "description": "Claude 3 (Opus, Sonnet, Haiku) for advanced reasoning and long context",
        "version": "1.0.0",
        "author": "Windows AI Team",
        "type": "integration",
        "category": "AI Models",
        "tags": ["ai", "nlp", "chat", "reasoning"],
        "enabled": False,
        "installed": False,
        "featured": True,
        "icon": "🧠",
        "requirements": ["anthropic>=0.18.0"],
        "config_required": ["api_key"]
    },
    {
        "id": "google-gemini",
        "name": "Google Gemini",
        "description": "Gemini Pro and Ultra models for multimodal AI tasks",
        "version": "1.0.0",
        "author": "Windows AI Team",
        "type": "integration",
        "category": "AI Models",
        "tags": ["ai", "multimodal", "vision", "chat"],
        "enabled": False,
        "installed": False,
        "featured": True,
        "icon": "✨",
        "requirements": ["google-generativeai>=0.3.0"],
        "config_required": ["api_key"]
    },
    {
        "id": "ollama",
        "name": "Ollama Local Models",
        "description": "Run LLMs locally with Ollama (Llama 2, Mistral, CodeLlama, etc.)",
        "version": "1.0.0",
        "author": "Windows AI Team",
        "type": "tool",
        "category": "Local AI",
        "tags": ["local", "offline", "llm", "privacy"],
        "enabled": False,
        "installed": False,
        "featured": True,
        "icon": "🦙",
        "requirements": ["ollama"],
        "config_required": []
    },
    {
        "id": "stable-diffusion",
        "name": "Stable Diffusion",
        "description": "Generate images from text using Stable Diffusion models",
        "version": "1.0.0",
        "author": "Windows AI Team",
        "type": "tool",
        "category": "Image Generation",
        "tags": ["image", "generation", "diffusion", "art"],
        "enabled": False,
        "installed": False,
        "featured": True,
        "icon": "🎨",
        "requirements": ["diffusers", "transformers", "torch"],
        "config_required": []
    },
    {
        "id": "whisper",
        "name": "OpenAI Whisper",
        "description": "Speech-to-text transcription with high accuracy",
        "version": "1.0.0",
        "author": "Windows AI Team",
        "type": "tool",
        "category": "Audio",
        "tags": ["audio", "transcription", "speech", "stt"],
        "enabled": False,
        "installed": False,
        "featured": True,
        "icon": "🎤",
        "requirements": ["openai-whisper"],
        "config_required": []
    },
    {
        "id": "elevenlabs",
        "name": "ElevenLabs TTS",
        "description": "High-quality text-to-speech with natural voices",
        "version": "1.0.0",
        "author": "Windows AI Team",
        "type": "integration",
        "category": "Audio",
        "tags": ["audio", "tts", "voice", "speech"],
        "enabled": False,
        "installed": False,
        "featured": False,
        "icon": "🔊",
        "requirements": ["elevenlabs"],
        "config_required": ["api_key"]
    },
    {
        "id": "langchain",
        "name": "LangChain",
        "description": "Build LLM-powered applications with chains and agents",
        "version": "1.0.0",
        "author": "Windows AI Team",
        "type": "tool",
        "category": "Framework",
        "tags": ["framework", "llm", "chains", "agents"],
        "enabled": False,
        "installed": False,
        "featured": True,
        "icon": "⛓️",
        "requirements": ["langchain>=0.1.0"],
        "config_required": []
    },
    {
        "id": "chromadb",
        "name": "ChromaDB",
        "description": "Vector database for embeddings and semantic search",
        "version": "1.0.0",
        "author": "Windows AI Team",
        "type": "tool",
        "category": "Database",
        "tags": ["database", "vector", "embeddings", "search"],
        "enabled": False,
        "installed": False,
        "featured": False,
        "icon": "🗄️",
        "requirements": ["chromadb"],
        "config_required": []
    },
    {
        "id": "github-copilot",
        "name": "GitHub Copilot",
        "description": "AI-powered code completion and suggestions",
        "version": "1.0.0",
        "author": "Windows AI Team",
        "type": "integration",
        "category": "Code",
        "tags": ["code", "completion", "productivity", "github"],
        "enabled": False,
        "installed": False,
        "featured": True,
        "icon": "💻",
        "requirements": [],
        "config_required": ["api_key"]
    }
]

# Sample models data
SAMPLE_MODELS = [
    {
        "id": "gpt-3.5-turbo",
        "name": "GPT-3.5 Turbo",
        "provider": "OpenAI",
        "description": "Fast and efficient model for most tasks",
        "category": "general",
        "size": "N/A",
        "context_length": 16385,
        "capabilities": ["chat", "completion", "function_calling"],
        "installed": False,
        "available": True,
        "cost": "Low",
        "speed": "Fast"
    },
    {
        "id": "gpt-4",
        "name": "GPT-4",
        "provider": "OpenAI",
        "description": "Most capable model for complex reasoning",
        "category": "premium",
        "size": "N/A",
        "context_length": 8192,
        "capabilities": ["chat", "completion", "function_calling", "advanced_reasoning"],
        "installed": False,
        "available": True,
        "cost": "High",
        "speed": "Moderate"
    },
    {
        "id": "gpt-4-turbo",
        "name": "GPT-4 Turbo",
        "provider": "OpenAI",
        "description": "Faster GPT-4 with larger context window",
        "category": "recommended",
        "size": "N/A",
        "context_length": 128000,
        "capabilities": ["chat", "completion", "function_calling", "vision"],
        "installed": False,
        "available": True,
        "cost": "Medium-High",
        "speed": "Fast"
    },
    {
        "id": "claude-3-opus",
        "name": "Claude 3 Opus",
        "provider": "Anthropic",
        "description": "Most powerful Claude model for hard tasks",
        "category": "premium",
        "size": "N/A",
        "context_length": 200000,
        "capabilities": ["chat", "completion", "advanced_reasoning", "vision"],
        "installed": False,
        "available": True,
        "cost": "High",
        "speed": "Moderate"
    },
    {
        "id": "claude-3-sonnet",
        "name": "Claude 3 Sonnet",
        "provider": "Anthropic",
        "description": "Balanced performance and speed",
        "category": "recommended",
        "size": "N/A",
        "context_length": 200000,
        "capabilities": ["chat", "completion", "vision"],
        "installed": False,
        "available": True,
        "cost": "Medium",
        "speed": "Fast"
    },
    {
        "id": "ollama/llama2",
        "name": "Llama 2 7B",
        "provider": "Meta (via Ollama)",
        "description": "Open-source LLM running locally",
        "category": "lightweight",
        "size": "3.8 GB",
        "context_length": 4096,
        "capabilities": ["chat", "completion"],
        "installed": False,
        "available": True,
        "cost": "Free",
        "speed": "Variable"
    },
    {
        "id": "ollama/codellama",
        "name": "Code Llama 7B",
        "provider": "Meta (via Ollama)",
        "description": "Specialized for code generation",
        "category": "coding",
        "size": "3.8 GB",
        "context_length": 16384,
        "capabilities": ["code_generation", "completion"],
        "installed": False,
        "available": True,
        "cost": "Free",
        "speed": "Variable"
    },
    {
        "id": "ollama/mistral",
        "name": "Mistral 7B",
        "provider": "Mistral AI (via Ollama)",
        "description": "Efficient open-source model",
        "category": "lightweight",
        "size": "4.1 GB",
        "context_length": 8192,
        "capabilities": ["chat", "completion"],
        "installed": False,
        "available": True,
        "cost": "Free",
        "speed": "Fast"
    }
]

@router.get("/plugins")
async def list_plugins(
    type: Optional[str] = None,
    search: Optional[str] = None,
    installed: Optional[bool] = None
):
    """List available plugins"""
    plugins = SAMPLE_PLUGINS.copy()
    
    # Apply filters
    if type and type != "all":
        plugins = [p for p in plugins if p.get("type") == type]
    
    if search:
        search_lower = search.lower()
        plugins = [
            p for p in plugins
            if search_lower in p["name"].lower() or search_lower in p["description"].lower()
        ]
    
    if installed is not None:
        plugins = [p for p in plugins if p.get("installed") == installed]
    
    return {
        "plugins": plugins,
        "total": len(plugins),
        "installed_count": sum(1 for p in SAMPLE_PLUGINS if p.get("installed")),
        "available_count": len(SAMPLE_PLUGINS)
    }

@router.get("/plugins/{plugin_id}")
async def get_plugin(plugin_id: str):
    """Get plugin details"""
    plugin = next((p for p in SAMPLE_PLUGINS if p["id"] == plugin_id), None)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin

@router.post("/plugins/{plugin_id}/enable")
async def enable_plugin(plugin_id: str):
    """Enable a plugin"""
    plugin = next((p for p in SAMPLE_PLUGINS if p["id"] == plugin_id), None)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    # In a real implementation, this would actually enable the plugin
    plugin["enabled"] = True
    plugin["installed"] = True
    
    return {"success": True, "message": f"Plugin {plugin_id} enabled"}

@router.post("/plugins/{plugin_id}/disable")
async def disable_plugin(plugin_id: str):
    """Disable a plugin"""
    plugin = next((p for p in SAMPLE_PLUGINS if p["id"] == plugin_id), None)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    plugin["enabled"] = False
    
    return {"success": True, "message": f"Plugin {plugin_id} disabled"}

@router.get("/models")
async def list_models(request: Request, category: Optional[str] = None):
    """List available AI models"""
    # Try to surface models from the unified LLM provider if available
    models = []
    try:
        components = getattr(request.app.state, "components", None)
        if components and isinstance(components, dict) and "llm" in components:
            llm = components.get("llm")
            try:
                models = llm.list_registered_models()
            except Exception:
                models = SAMPLE_MODELS.copy()
        else:
            models = SAMPLE_MODELS.copy()
    except Exception:
        models = SAMPLE_MODELS.copy()
    
    if category and category != "all":
        models = [m for m in models if m.get("category") == category]
    
    return {
        "models": models,
        "total": len(models),
        "installed": sum(1 for m in models if m.get("installed")),
        "available": len(models)
    }

@router.get("/models/{model_id}")
async def get_model(model_id: str):
    """Get model details"""
    model = next((m for m in SAMPLE_MODELS if m["id"] == model_id), None)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model

@router.post("/models/{model_id}/download")
async def download_model(model_id: str):
    """Download/install a model"""
    model = next((m for m in SAMPLE_MODELS if m["id"] == model_id), None)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # In a real implementation, this would download the model
    model["installed"] = True
    
    return {
        "success": True,
        "message": f"Model {model_id} download started",
        "model_id": model_id
    }

@router.delete("/models/{model_id}")
async def delete_model(model_id: str):
    """Delete/uninstall a model"""
    model = next((m for m in SAMPLE_MODELS if m["id"] == model_id), None)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model["installed"] = False
    
    return {"success": True, "message": f"Model {model_id} deleted"}
