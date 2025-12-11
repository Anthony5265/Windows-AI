"""
Server-Sent Events (SSE) for Streaming Responses

Provides SSE support as an alternative to WebSocket for streaming
"""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Optional, Dict, Any
import asyncio
import json
import logging
from datetime import datetime
from collections import defaultdict

from windows_ai.core.error_handling import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/sse", tags=["sse"])


class SSEManager:
    """
    Manages Server-Sent Events streams
    
    Provides one-way streaming from server to client
    """
    
    def __init__(self):
        # Active streams by stream ID
        self.active_streams: Dict[str, asyncio.Queue] = {}
        
        # Stream metadata
        self.stream_metadata: Dict[str, Dict[str, Any]] = {}
        
        logger.info("SSE Manager initialized")
    
    def create_stream(self, stream_id: str) -> asyncio.Queue:
        """
        Create a new SSE stream
        
        Args:
            stream_id: Stream identifier
            
        Returns:
            Queue for sending messages to the stream
        """
        if stream_id in self.active_streams:
            logger.warning(f"Stream {stream_id} already exists")
            return self.active_streams[stream_id]
        
        queue = asyncio.Queue()
        self.active_streams[stream_id] = queue
        self.stream_metadata[stream_id] = {
            'created_at': datetime.utcnow().isoformat(),
            'message_count': 0
        }
        
        logger.info(f"SSE stream created: {stream_id}")
        return queue
    
    def close_stream(self, stream_id: str):
        """
        Close an SSE stream
        
        Args:
            stream_id: Stream identifier
        """
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]
        
        if stream_id in self.stream_metadata:
            del self.stream_metadata[stream_id]
        
        logger.info(f"SSE stream closed: {stream_id}")
    
    async def send_event(
        self,
        stream_id: str,
        event: str,
        data: Dict[str, Any]
    ):
        """
        Send an event to a specific stream
        
        Args:
            stream_id: Stream identifier
            event: Event name
            data: Event data
        """
        if stream_id not in self.active_streams:
            logger.warning(f"Stream {stream_id} not found")
            return
        
        queue = self.active_streams[stream_id]
        
        try:
            await queue.put({
                'event': event,
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Update metadata
            metadata = self.stream_metadata.get(stream_id)
            if metadata:
                metadata['message_count'] += 1
        
        except Exception as e:
            logger.error(f"Failed to send event to stream {stream_id}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get SSE manager statistics"""
        return {
            'active_streams': len(self.active_streams),
            'streams': {
                stream_id: {
                    'message_count': metadata.get('message_count', 0),
                    'created_at': metadata.get('created_at')
                }
                for stream_id, metadata in self.stream_metadata.items()
            }
        }


# Global SSE manager
sse_manager = SSEManager()


def format_sse(event: str, data: Dict[str, Any], event_id: Optional[str] = None) -> str:
    """
    Format data as Server-Sent Event
    
    Args:
        event: Event name
        data: Event data
        event_id: Optional event ID
        
    Returns:
        Formatted SSE string
    """
    lines = []
    
    if event_id:
        lines.append(f"id: {event_id}")
    
    lines.append(f"event: {event}")
    
    # Format data as JSON
    json_data = json.dumps(data)
    lines.append(f"data: {json_data}")
    
    # Empty line to signal end of event
    lines.append("")
    
    return "\n".join(lines) + "\n"


async def event_generator(
    stream_id: str,
    timeout: int = 30
) -> AsyncGenerator[str, None]:
    """
    Generate Server-Sent Events from a stream
    
    Args:
        stream_id: Stream identifier
        timeout: Timeout in seconds for waiting for messages
        
    Yields:
        Formatted SSE strings
    """
    queue = sse_manager.create_stream(stream_id)
    
    try:
        # Send initial connection event
        yield format_sse(
            event="connected",
            data={'stream_id': stream_id, 'message': 'Connected to stream'}
        )
        
        # Keep stream alive with periodic heartbeats
        last_heartbeat = asyncio.get_event_loop().time()
        heartbeat_interval = 15  # seconds
        
        while True:
            try:
                # Wait for next message with timeout
                message = await asyncio.wait_for(
                    queue.get(),
                    timeout=1.0  # Short timeout to check heartbeat
                )
                
                # Send the message
                yield format_sse(
                    event=message['event'],
                    data=message['data']
                )
                
                last_heartbeat = asyncio.get_event_loop().time()
            
            except asyncio.TimeoutError:
                # Check if we need to send heartbeat
                current_time = asyncio.get_event_loop().time()
                if current_time - last_heartbeat >= heartbeat_interval:
                    # Send heartbeat to keep connection alive
                    yield format_sse(
                        event="heartbeat",
                        data={'timestamp': datetime.utcnow().isoformat()}
                    )
                    last_heartbeat = current_time
    
    except asyncio.CancelledError:
        logger.info(f"SSE stream cancelled: {stream_id}")
    except Exception as e:
        logger.error(f"SSE stream error: {e}", exc_info=True)
        yield format_sse(
            event="error",
            data={'message': str(e)}
        )
    finally:
        sse_manager.close_stream(stream_id)


@router.get("/chat/{conversation_id}")
async def chat_stream(conversation_id: str, request: Request):
    """
    Server-Sent Events endpoint for chat streaming
    
    Args:
        conversation_id: Conversation identifier
        request: FastAPI request object
    """
    logger.info(f"SSE chat stream started: {conversation_id}")
    
    return StreamingResponse(
        event_generator(f"chat_{conversation_id}"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/progress/{task_id}")
async def progress_stream(task_id: str, request: Request):
    """
    Server-Sent Events endpoint for progress updates
    
    Args:
        task_id: Task identifier
        request: FastAPI request object
    """
    logger.info(f"SSE progress stream started: {task_id}")
    
    return StreamingResponse(
        event_generator(f"progress_{task_id}"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/notifications")
async def notifications_stream(request: Request):
    """
    Server-Sent Events endpoint for system notifications
    
    Args:
        request: FastAPI request object
    """
    import uuid
    stream_id = f"notifications_{uuid.uuid4()}"
    
    logger.info(f"SSE notifications stream started: {stream_id}")
    
    return StreamingResponse(
        event_generator(stream_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# Helper functions for sending events

async def send_chat_chunk(
    conversation_id: str,
    chunk: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Send a chat chunk via SSE
    
    Args:
        conversation_id: Conversation identifier
        chunk: Text chunk
        metadata: Optional metadata
    """
    await sse_manager.send_event(
        f"chat_{conversation_id}",
        "chunk",
        {
            'chunk': chunk,
            'metadata': metadata or {}
        }
    )


async def send_chat_complete(
    conversation_id: str,
    message: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Signal chat completion via SSE
    
    Args:
        conversation_id: Conversation identifier
        message: Complete message
        metadata: Optional metadata
    """
    await sse_manager.send_event(
        f"chat_{conversation_id}",
        "complete",
        {
            'message': message,
            'metadata': metadata or {}
        }
    )


async def send_progress_update(
    task_id: str,
    progress: int,
    message: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Send progress update via SSE
    
    Args:
        task_id: Task identifier
        progress: Progress percentage (0-100)
        message: Progress message
        metadata: Optional metadata
    """
    await sse_manager.send_event(
        f"progress_{task_id}",
        "progress",
        {
            'progress': progress,
            'message': message,
            'metadata': metadata or {}
        }
    )


async def send_progress_complete(
    task_id: str,
    result: Optional[Dict[str, Any]] = None
):
    """
    Signal progress completion via SSE
    
    Args:
        task_id: Task identifier
        result: Optional result data
    """
    await sse_manager.send_event(
        f"progress_{task_id}",
        "complete",
        {
            'result': result or {}
        }
    )


async def send_notification(
    message: str,
    level: str = "info",
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Send system notification via SSE to all notification streams
    
    Args:
        message: Notification message
        level: Severity level (info, warning, error)
        metadata: Optional metadata
    """
    # Send to all notification streams
    for stream_id in list(sse_manager.active_streams.keys()):
        if stream_id.startswith("notifications_"):
            await sse_manager.send_event(
                stream_id,
                "notification",
                {
                    'message': message,
                    'level': level,
                    'metadata': metadata or {}
                }
            )


@router.get("/stats")
async def get_sse_stats():
    """
    Get SSE manager statistics
    
    Returns information about active streams
    """
    return sse_manager.get_stats()
