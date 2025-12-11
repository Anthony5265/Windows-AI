"""
WebSocket Infrastructure for Real-Time Communication

Provides WebSocket support for chat streaming, progress updates, and notifications
"""

from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from typing import Dict, Set, Optional, Any, List
import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
import uuid

from windows_ai.core.error_handling import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/ws", tags=["websocket"])


class MessageType(Enum):
    """WebSocket message types"""
    # Chat messages
    CHAT_START = "chat_start"
    CHAT_CHUNK = "chat_chunk"
    CHAT_COMPLETE = "chat_complete"
    CHAT_ERROR = "chat_error"
    
    # Progress updates
    PROGRESS_UPDATE = "progress_update"
    PROGRESS_COMPLETE = "progress_complete"
    
    # Plugin events
    PLUGIN_STATUS = "plugin_status"
    PLUGIN_OUTPUT = "plugin_output"
    
    # System notifications
    NOTIFICATION = "notification"
    ERROR = "error"
    
    # Control messages
    PING = "ping"
    PONG = "pong"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting
    
    Supports multiple channels and connection management
    """
    
    def __init__(self):
        # Active connections by connection ID
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Connections subscribed to channels
        self.channel_subscriptions: Dict[str, Set[str]] = {}
        
        # Connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Connection Manager initialized")
    
    async def connect(
        self,
        websocket: WebSocket,
        connection_id: Optional[str] = None
    ) -> str:
        """
        Accept a new WebSocket connection
        
        Args:
            websocket: WebSocket connection
            connection_id: Optional connection ID (generated if not provided)
            
        Returns:
            Connection ID
        """
        await websocket.accept()
        
        if connection_id is None:
            connection_id = str(uuid.uuid4())
        
        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            'connected_at': datetime.utcnow().isoformat(),
            'last_message': None,
            'message_count': 0
        }
        
        logger.info(f"WebSocket connected: {connection_id}")
        logger.debug(f"Active connections: {len(self.active_connections)}")
        
        return connection_id
    
    def disconnect(self, connection_id: str):
        """
        Remove a WebSocket connection
        
        Args:
            connection_id: Connection ID to remove
        """
        # Remove from active connections
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from all channel subscriptions
        for channel, subscribers in self.channel_subscriptions.items():
            subscribers.discard(connection_id)
        
        # Remove metadata
        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
        logger.debug(f"Active connections: {len(self.active_connections)}")
    
    async def subscribe(self, connection_id: str, channel: str):
        """
        Subscribe a connection to a channel
        
        Args:
            connection_id: Connection ID
            channel: Channel name
        """
        if channel not in self.channel_subscriptions:
            self.channel_subscriptions[channel] = set()
        
        self.channel_subscriptions[channel].add(connection_id)
        
        logger.debug(f"Connection {connection_id} subscribed to {channel}")
    
    async def unsubscribe(self, connection_id: str, channel: str):
        """
        Unsubscribe a connection from a channel
        
        Args:
            connection_id: Connection ID
            channel: Channel name
        """
        if channel in self.channel_subscriptions:
            self.channel_subscriptions[channel].discard(connection_id)
            
            logger.debug(f"Connection {connection_id} unsubscribed from {channel}")
    
    async def send_personal_message(
        self,
        message: Dict[str, Any],
        connection_id: str
    ):
        """
        Send a message to a specific connection
        
        Args:
            message: Message data
            connection_id: Target connection ID
        """
        if connection_id not in self.active_connections:
            logger.warning(f"Connection {connection_id} not found")
            return
        
        websocket = self.active_connections[connection_id]
        
        try:
            await websocket.send_json(message)
            
            # Update metadata
            metadata = self.connection_metadata.get(connection_id)
            if metadata:
                metadata['last_message'] = datetime.utcnow().isoformat()
                metadata['message_count'] += 1
        
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            self.disconnect(connection_id)
    
    async def broadcast(
        self,
        message: Dict[str, Any],
        channel: Optional[str] = None
    ):
        """
        Broadcast a message to all connections or a specific channel
        
        Args:
            message: Message data
            channel: Optional channel name (broadcasts to all if not specified)
        """
        # Get target connections
        if channel:
            target_ids = self.channel_subscriptions.get(channel, set())
            logger.debug(f"Broadcasting to channel {channel}: {len(target_ids)} connections")
        else:
            target_ids = set(self.active_connections.keys())
            logger.debug(f"Broadcasting to all: {len(target_ids)} connections")
        
        # Send to each connection
        failed_connections = []
        for connection_id in target_ids:
            websocket = self.active_connections.get(connection_id)
            if not websocket:
                continue
            
            try:
                await websocket.send_json(message)
                
                # Update metadata
                metadata = self.connection_metadata.get(connection_id)
                if metadata:
                    metadata['last_message'] = datetime.utcnow().isoformat()
                    metadata['message_count'] += 1
            
            except Exception as e:
                logger.error(f"Failed to broadcast to {connection_id}: {e}")
                failed_connections.append(connection_id)
        
        # Clean up failed connections
        for connection_id in failed_connections:
            self.disconnect(connection_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection manager statistics"""
        return {
            'total_connections': len(self.active_connections),
            'channels': {
                channel: len(subscribers)
                for channel, subscribers in self.channel_subscriptions.items()
            }
        }


# Global connection manager
manager = ConnectionManager()


@router.websocket("/chat")
async def chat_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for chat streaming
    
    Receives chat requests and streams responses back
    """
    connection_id = await manager.connect(websocket)
    
    try:
        # Subscribe to chat channel
        await manager.subscribe(connection_id, "chat")
        
        # Send welcome message
        await manager.send_personal_message(
            {
                'type': MessageType.NOTIFICATION.value,
                'message': 'Connected to chat server',
                'connection_id': connection_id
            },
            connection_id
        )
        
        # Main message loop
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message_type = data.get('type')
            
            if message_type == MessageType.PING.value:
                # Respond to ping
                await manager.send_personal_message(
                    {'type': MessageType.PONG.value},
                    connection_id
                )
            
            elif message_type == 'chat_message':
                # Handle chat message
                await handle_chat_message(data, connection_id)
            
            elif message_type == MessageType.SUBSCRIBE.value:
                # Subscribe to additional channel
                channel = data.get('channel')
                if channel:
                    await manager.subscribe(connection_id, channel)
                    await manager.send_personal_message(
                        {
                            'type': MessageType.NOTIFICATION.value,
                            'message': f'Subscribed to {channel}'
                        },
                        connection_id
                    )
            
            elif message_type == MessageType.UNSUBSCRIBE.value:
                # Unsubscribe from channel
                channel = data.get('channel')
                if channel:
                    await manager.unsubscribe(connection_id, channel)
                    await manager.send_personal_message(
                        {
                            'type': MessageType.NOTIFICATION.value,
                            'message': f'Unsubscribed from {channel}'
                        },
                        connection_id
                    )
    
    except WebSocketDisconnect:
        logger.info(f"Chat WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"Chat WebSocket error: {e}", exc_info=True)
        try:
            await manager.send_personal_message(
                {
                    'type': MessageType.ERROR.value,
                    'message': str(e)
                },
                connection_id
            )
        except:
            pass
    finally:
        manager.disconnect(connection_id)


async def handle_chat_message(data: Dict[str, Any], connection_id: str):
    """
    Handle incoming chat message and stream response
    
    Args:
        data: Message data
        connection_id: Connection ID
    """
    try:
        message = data.get('message', '')
        conversation_id = data.get('conversation_id')
        model = data.get('model', 'auto')
        
        # Send chat start notification
        await manager.send_personal_message(
            {
                'type': MessageType.CHAT_START.value,
                'conversation_id': conversation_id
            },
            connection_id
        )
        
        # Get LLM provider from app state
        from windows_ai.api.server import app
        components = getattr(app.state, "components", {})
        llm = components.get("llm")
        
        if not llm:
            # Fallback to mock response if LLM not available
            logger.warning("LLM provider not available, using mock response")
            response_text = f"Mock response to: {message}"
            words = response_text.split()
            for i, word in enumerate(words):
                await manager.send_personal_message(
                    {
                        'type': MessageType.CHAT_CHUNK.value,
                        'chunk': word + ' ',
                        'conversation_id': conversation_id
                    },
                    connection_id
                )
                await asyncio.sleep(0.1)
        else:
            # Use UnifiedLLM for real AI response with streaming
            model_id = None if model == "auto" else model
            
            try:
                # Stream response from LLM
                response_stream = await llm.chat(
                    messages=[{"role": "user", "content": message}],
                    config_name=model_id,
                    stream=True
                )
                
                # Send each chunk as it arrives
                async for chunk in response_stream:
                    if hasattr(chunk, 'content') and chunk.content:
                        await manager.send_personal_message(
                            {
                                'type': MessageType.CHAT_CHUNK.value,
                                'chunk': chunk.content,
                                'conversation_id': conversation_id
                            },
                            connection_id
                        )
            except Exception as e:
                logger.error(f"LLM streaming error: {e}")
                # Send error response
                await manager.send_personal_message(
                    {
                        'type': MessageType.CHAT_CHUNK.value,
                        'chunk': f"Error: {str(e)}",
                        'conversation_id': conversation_id
                    },
                    connection_id
                )
        
        # Send completion notification
        await manager.send_personal_message(
            {
                'type': MessageType.CHAT_COMPLETE.value,
                'conversation_id': conversation_id,
                'message': response_text
            },
            connection_id
        )
    
    except Exception as e:
        logger.error(f"Error handling chat message: {e}", exc_info=True)
        await manager.send_personal_message(
            {
                'type': MessageType.CHAT_ERROR.value,
                'error': str(e),
                'conversation_id': data.get('conversation_id')
            },
            connection_id
        )


@router.websocket("/progress")
async def progress_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for progress updates
    
    Used for long-running operations like model downloads, batch processing
    """
    connection_id = await manager.connect(websocket)
    
    try:
        await manager.subscribe(connection_id, "progress")
        
        await manager.send_personal_message(
            {
                'type': MessageType.NOTIFICATION.value,
                'message': 'Connected to progress updates'
            },
            connection_id
        )
        
        # Keep connection alive
        while True:
            data = await websocket.receive_json()
            
            if data.get('type') == MessageType.PING.value:
                await manager.send_personal_message(
                    {'type': MessageType.PONG.value},
                    connection_id
                )
    
    except WebSocketDisconnect:
        logger.info(f"Progress WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"Progress WebSocket error: {e}", exc_info=True)
    finally:
        manager.disconnect(connection_id)


@router.websocket("/notifications")
async def notifications_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for system notifications
    
    Broadcasts system-wide notifications to subscribed clients
    """
    connection_id = await manager.connect(websocket)
    
    try:
        await manager.subscribe(connection_id, "notifications")
        
        await manager.send_personal_message(
            {
                'type': MessageType.NOTIFICATION.value,
                'message': 'Connected to system notifications'
            },
            connection_id
        )
        
        # Keep connection alive
        while True:
            data = await websocket.receive_json()
            
            if data.get('type') == MessageType.PING.value:
                await manager.send_personal_message(
                    {'type': MessageType.PONG.value},
                    connection_id
                )
    
    except WebSocketDisconnect:
        logger.info(f"Notifications WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"Notifications WebSocket error: {e}", exc_info=True)
    finally:
        manager.disconnect(connection_id)


# Helper functions for broadcasting to channels

async def broadcast_progress(
    task_id: str,
    progress: int,
    message: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Broadcast progress update to all subscribed clients
    
    Args:
        task_id: Task identifier
        progress: Progress percentage (0-100)
        message: Progress message
        metadata: Optional additional data
    """
    await manager.broadcast(
        {
            'type': MessageType.PROGRESS_UPDATE.value,
            'task_id': task_id,
            'progress': progress,
            'message': message,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat()
        },
        channel="progress"
    )


async def broadcast_notification(
    message: str,
    level: str = "info",
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Broadcast system notification to all subscribed clients
    
    Args:
        message: Notification message
        level: Severity level (info, warning, error)
        metadata: Optional additional data
    """
    await manager.broadcast(
        {
            'type': MessageType.NOTIFICATION.value,
            'message': message,
            'level': level,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat()
        },
        channel="notifications"
    )


async def broadcast_plugin_status(
    plugin_id: str,
    status: str,
    message: Optional[str] = None
):
    """
    Broadcast plugin status change
    
    Args:
        plugin_id: Plugin identifier
        status: Plugin status
        message: Optional status message
    """
    await manager.broadcast(
        {
            'type': MessageType.PLUGIN_STATUS.value,
            'plugin_id': plugin_id,
            'status': status,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        },
        channel="notifications"
    )
