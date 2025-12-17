"""Chat and conversation API routes for Windows AI GUI"""

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

# Import unrestricted configuration
from windows_ai.config.unrestricted_config import \
  get_unrestricted_system_prompt

logger = logging.getLogger(__name__)
router = APIRouter()

# System prompt for unrestricted AI behavior
SYSTEM_PROMPT = get_unrestricted_system_prompt()

# In-memory conversation storage (replace with database in production)
conversations: Dict[str, List[Dict[str, Any]]] = {}

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    model: Optional[str] = "gpt-3.5-turbo"
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    model: str

@router.post("/chat")
async def chat(body: ChatMessage, request: Request):
    """Non-streaming chat endpoint"""
    try:
        # Get LLM provider
        components = getattr(request.app.state, "components", {})
        llm = components.get("llm")
        
        if not llm:
            raise HTTPException(status_code=503, detail="LLM provider not initialized")

        # Generate conversation ID if not provided
        conv_id = body.conversation_id or str(uuid.uuid4())
        
        # Store user message
        if conv_id not in conversations:
            conversations[conv_id] = []
        
        conversations[conv_id].append({
            "role": "user",
            "content": body.message,
            "timestamp": time.time()
        })
        
        # Prepare messages for LLM with system prompt
        history = [
            {"role": "system", "content": SYSTEM_PROMPT}  # Unrestricted system prompt first
        ]
        for msg in conversations[conv_id]:
            if msg["role"] in ["user", "assistant", "system"]:
                history.append({"role": msg["role"], "content": msg["content"]})
        
        # Handle 'auto' model
        model_id = body.model
        if model_id == "auto":
            model_id = None
            
        # Generate AI response
        try:
            response = await llm.chat(
                messages=history,
                config_name=model_id,
                temperature=body.temperature,
                stream=False
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            # Fallback for demo purposes if no API keys configured
            if "api_key" in str(e).lower() or "unauthorized" in str(e).lower():
                ai_response = f"Error: {str(e)}. Please configure your API keys in Settings."
                conversations[conv_id].append({
                    "role": "assistant",
                    "content": ai_response,
                    "timestamp": time.time()
                })
                return ChatResponse(
                    response=ai_response,
                    conversation_id=conv_id,
                    model=body.model or "unknown"
                )
            raise e
        
        ai_response = response.content
        
        # Store AI response
        conversations[conv_id].append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": time.time()
        })
        
        return ChatResponse(
            response=ai_response,
            conversation_id=conv_id,
            model=response.model
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stream")
async def chat_stream(body: ChatMessage, request: Request):
    """Streaming chat endpoint using Server-Sent Events"""
    try:
        # Get LLM provider
        components = getattr(request.app.state, "components", {})
        llm = components.get("llm")
        
        if not llm:
            raise HTTPException(status_code=503, detail="LLM provider not initialized")

        # Generate conversation ID if not provided
        conv_id = body.conversation_id or str(uuid.uuid4())
        
        # Store user message
        if conv_id not in conversations:
            conversations[conv_id] = []
        
        conversations[conv_id].append({
            "role": "user",
            "content": body.message,
            "timestamp": time.time()
        })
        
        # Prepare messages for LLM with system prompt
        history = [
            {"role": "system", "content": SYSTEM_PROMPT}  # Unrestricted system prompt first
        ]
        for msg in conversations[conv_id]:
            if msg["role"] in ["user", "assistant", "system"]:
                history.append({"role": msg["role"], "content": msg["content"]})
        
        # Handle 'auto' model
        model_id = body.model
        if model_id == "auto":
            model_id = None

        async def generate():
            """Generate streaming response"""
            full_response = ""
            try:
                generator = await llm.chat(
                    messages=history,
                    config_name=model_id,
                    temperature=body.temperature,
                    stream=True
                )
                
                async for chunk in generator:
                    full_response += chunk
                    data = {
                        "chunk": chunk,
                        "conversation_id": conv_id,
                        "done": False
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    # No sleep needed for real streaming
                
                # Send done message
                data = {
                    "chunk": "",
                    "conversation_id": conv_id,
                    "done": True
                }
                yield f"data: {json.dumps(data)}\n\n"
                
                # Store complete response
                conversations[conv_id].append({
                    "role": "assistant",
                    "content": full_response,
                    "timestamp": time.time()
                })
                
            except Exception as e:
                # Handle errors during streaming
                error_msg = f"Error: {str(e)}"
                if "api_key" in str(e).lower():
                    error_msg += " Please configure your API keys in Settings."
                
                data = {
                    "chunk": error_msg,
                    "conversation_id": conv_id,
                    "done": True,
                    "error": True
                }
                yield f"data: {json.dumps(data)}\n\n"
                
                # Store error response
                conversations[conv_id].append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": time.time()
                })
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations")
async def list_conversations():
    """List all conversations"""
    try:
        return {
            "conversations": conversations,
            "total": len(conversations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a specific conversation"""
    try:
        if conversation_id not in conversations:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "conversation_id": conversation_id,
            "messages": conversations[conversation_id]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    try:
        if conversation_id not in conversations:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        del conversations[conversation_id]
        
        return {
            "success": True,
            "message": f"Conversation {conversation_id} deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conversations")
async def delete_all_conversations():
    """Delete all conversations"""
    try:
        count = len(conversations)
        conversations.clear()
        
        return {
            "success": True,
            "message": f"Deleted {count} conversations"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
