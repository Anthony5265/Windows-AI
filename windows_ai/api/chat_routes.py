"""Chat and conversation API routes for Windows AI GUI"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import json
import time
import uuid

router = APIRouter()

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
async def chat(request: ChatMessage):
    """Non-streaming chat endpoint"""
    try:
        # Generate conversation ID if not provided
        conv_id = request.conversation_id or str(uuid.uuid4())
        
        # Store user message
        if conv_id not in conversations:
            conversations[conv_id] = []
        
        conversations[conv_id].append({
            "role": "user",
            "content": request.message,
            "timestamp": time.time()
        })
        
        # Generate AI response (placeholder - integrate with actual LLM)
        ai_response = f"This is a placeholder response to: '{request.message}'. The backend is working but not connected to an LLM yet. Please configure your API keys in Settings."
        
        # Store AI response
        conversations[conv_id].append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": time.time()
        })
        
        return ChatResponse(
            response=ai_response,
            conversation_id=conv_id,
            model=request.model
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stream")
async def chat_stream(request: ChatMessage):
    """Streaming chat endpoint using Server-Sent Events"""
    try:
        # Generate conversation ID if not provided
        conv_id = request.conversation_id or str(uuid.uuid4())
        
        # Store user message
        if conv_id not in conversations:
            conversations[conv_id] = []
        
        conversations[conv_id].append({
            "role": "user",
            "content": request.message,
            "timestamp": time.time()
        })
        
        async def generate():
            """Generate streaming response"""
            # Placeholder response - integrate with actual LLM streaming
            full_response = f"Streaming response to: '{request.message}'. The Windows AI backend is running successfully! However, to get real AI responses, you need to:\n\n1. Configure API keys in Settings\n2. Choose an AI model (OpenAI, Anthropic, Google, etc.)\n3. Or run local models using Ollama\n\nThe system supports 2500+ AI capabilities once configured properly."
            
            # Simulate streaming by sending word by word
            words = full_response.split()
            for i, word in enumerate(words):
                chunk = word + " "
                data = {
                    "chunk": chunk,
                    "conversation_id": conv_id,
                    "done": i == len(words) - 1
                }
                yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(0.05)  # Simulate processing time
            
            # Store complete response
            conversations[conv_id].append({
                "role": "assistant",
                "content": full_response,
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
