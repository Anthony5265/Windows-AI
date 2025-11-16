"""
Agent Communication Plugin
Protocol and infrastructure for multi-agent communication
"""

from typing import Dict, Any, Optional, List
from collections import deque
import hashlib


class AgentCommunicationPlugin:
    """Plugin for agent-to-agent communication protocols"""

    name = "agent_communication"
    version = "1.0.0"
    description = "Communication protocols and message passing for multi-agent systems"
    author = "Windows AI Team"

    def __init__(self):
        self.agents = {}
        self.messages = deque(maxlen=1000)
        self.channels = {}
        self.protocols = {}
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Agent Communication plugin"""
        try:
            # Setup default protocols
            self.protocols = {
                "broadcast": self._broadcast_protocol,
                "direct": self._direct_protocol,
                "request_response": self._request_response_protocol,
                "publish_subscribe": self._pubsub_protocol,
                "blackboard": self._blackboard_protocol
            }
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Agent Communication plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Agent Communication action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "register_agent":
                return self._register_agent(params)
            elif action == "send_message":
                return self._send_message(params)
            elif action == "receive_messages":
                return self._receive_messages(params)
            elif action == "create_channel":
                return self._create_channel(params)
            elif action == "subscribe":
                return self._subscribe(params)
            elif action == "broadcast":
                return self._broadcast(params)
            elif action == "request":
                return self._request(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _register_agent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Register an agent in the communication system"""
        agent_id = params.get("agent_id", "")
        capabilities = params.get("capabilities", [])
        interests = params.get("interests", [])

        if agent_id in self.agents:
            return {"success": False, "error": f"Agent {agent_id} already registered"}

        agent = {
            "id": agent_id,
            "capabilities": capabilities,
            "interests": interests,
            "inbox": deque(maxlen=100),
            "subscriptions": [],
            "message_count": 0
        }

        self.agents[agent_id] = agent

        return {
            "success": True,
            "agent_id": agent_id,
            "total_agents": len(self.agents)
        }

    def _send_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message using specified protocol"""
        from_agent = params.get("from", "")
        to_agent = params.get("to", "")
        content = params.get("content", "")
        protocol = params.get("protocol", "direct")
        metadata = params.get("metadata", {})

        if from_agent not in self.agents:
            return {"success": False, "error": f"Sender {from_agent} not registered"}

        message = {
            "id": hashlib.md5(f"{from_agent}{to_agent}{len(self.messages)}".encode()).hexdigest()[:12],
            "from": from_agent,
            "to": to_agent,
            "content": content,
            "protocol": protocol,
            "metadata": metadata,
            "timestamp": "now",
            "status": "sent"
        }

        # Use specified protocol
        if protocol in self.protocols:
            result = self.protocols[protocol](message)
        else:
            result = self._direct_protocol(message)

        self.messages.append(message)

        return {
            "success": True,
            "message": message,
            "delivery": result
        }

    def _direct_protocol(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Direct point-to-point message delivery"""
        to_agent = message["to"]

        if to_agent not in self.agents:
            return {"delivered": False, "reason": "Recipient not found"}

        # Deliver to recipient's inbox
        self.agents[to_agent]["inbox"].append(message)
        self.agents[to_agent]["message_count"] += 1

        return {"delivered": True, "recipient": to_agent}

    def _broadcast_protocol(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Broadcast message to all agents"""
        delivered_to = []

        for agent_id, agent in self.agents.items():
            if agent_id != message["from"]:
                agent["inbox"].append(message)
                agent["message_count"] += 1
                delivered_to.append(agent_id)

        return {"delivered": True, "recipients": delivered_to, "count": len(delivered_to)}

    def _request_response_protocol(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Request-response pattern"""
        to_agent = message["to"]

        if to_agent not in self.agents:
            return {"delivered": False, "reason": "Recipient not found"}

        # Deliver request
        self.agents[to_agent]["inbox"].append(message)
        self.agents[to_agent]["message_count"] += 1

        # Simulate automatic response based on content
        response_content = f"Response to: {message['content'][:50]}..."

        response = {
            "id": hashlib.md5(f"resp_{message['id']}".encode()).hexdigest()[:12],
            "from": to_agent,
            "to": message["from"],
            "content": response_content,
            "protocol": "direct",
            "metadata": {"in_reply_to": message["id"]},
            "timestamp": "now",
            "status": "sent"
        }

        # Deliver response
        self.agents[message["from"]]["inbox"].append(response)
        self.messages.append(response)

        return {
            "delivered": True,
            "recipient": to_agent,
            "response": response
        }

    def _pubsub_protocol(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Publish-subscribe pattern"""
        topic = message["metadata"].get("topic", "general")

        if topic not in self.channels:
            return {"delivered": False, "reason": f"Topic {topic} does not exist"}

        channel = self.channels[topic]
        subscribers = channel["subscribers"]

        delivered_to = []
        for agent_id in subscribers:
            if agent_id in self.agents and agent_id != message["from"]:
                self.agents[agent_id]["inbox"].append(message)
                self.agents[agent_id]["message_count"] += 1
                delivered_to.append(agent_id)

        return {
            "delivered": True,
            "topic": topic,
            "recipients": delivered_to,
            "count": len(delivered_to)
        }

    def _blackboard_protocol(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Blackboard pattern: shared knowledge space"""
        blackboard_key = message["metadata"].get("key", "default")

        # Create blackboard if it doesn't exist
        if "blackboard" not in self.channels:
            self.channels["blackboard"] = {
                "type": "blackboard",
                "data": {}
            }

        # Write to blackboard
        self.channels["blackboard"]["data"][blackboard_key] = {
            "content": message["content"],
            "author": message["from"],
            "timestamp": message["timestamp"]
        }

        # Notify interested agents
        notified = []
        for agent_id, agent in self.agents.items():
            if blackboard_key in agent.get("interests", []) and agent_id != message["from"]:
                notification = {
                    **message,
                    "type": "blackboard_update",
                    "key": blackboard_key
                }
                agent["inbox"].append(notification)
                notified.append(agent_id)

        return {
            "delivered": True,
            "blackboard_key": blackboard_key,
            "notified": notified,
            "count": len(notified)
        }

    def _receive_messages(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve messages for an agent"""
        agent_id = params.get("agent_id", "")
        max_messages = params.get("max", 10)

        if agent_id not in self.agents:
            return {"success": False, "error": f"Agent {agent_id} not registered"}

        agent = self.agents[agent_id]
        messages = list(agent["inbox"])[-max_messages:]

        return {
            "success": True,
            "messages": messages,
            "count": len(messages),
            "total_received": agent["message_count"]
        }

    def _create_channel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a communication channel or topic"""
        channel_id = params.get("channel_id", "")
        channel_type = params.get("type", "pubsub")  # pubsub, blackboard, etc.

        if channel_id in self.channels:
            return {"success": False, "error": f"Channel {channel_id} already exists"}

        channel = {
            "id": channel_id,
            "type": channel_type,
            "subscribers": [],
            "message_count": 0
        }

        if channel_type == "blackboard":
            channel["data"] = {}

        self.channels[channel_id] = channel

        return {
            "success": True,
            "channel_id": channel_id,
            "type": channel_type
        }

    def _subscribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Subscribe an agent to a channel"""
        agent_id = params.get("agent_id", "")
        channel_id = params.get("channel_id", "")

        if agent_id not in self.agents:
            return {"success": False, "error": f"Agent {agent_id} not registered"}

        if channel_id not in self.channels:
            return {"success": False, "error": f"Channel {channel_id} not found"}

        channel = self.channels[channel_id]

        if agent_id not in channel["subscribers"]:
            channel["subscribers"].append(agent_id)
            self.agents[agent_id]["subscriptions"].append(channel_id)

        return {
            "success": True,
            "agent_id": agent_id,
            "channel_id": channel_id,
            "total_subscribers": len(channel["subscribers"])
        }

    def _broadcast(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Broadcast a message to all agents"""
        from_agent = params.get("from", "")
        content = params.get("content", "")

        message = {
            "from": from_agent,
            "to": "all",
            "content": content,
            "protocol": "broadcast",
            "metadata": {},
            "timestamp": "now"
        }

        result = self._broadcast_protocol(message)
        self.messages.append(message)

        return {
            "success": True,
            "message": message,
            "delivery": result
        }

    def _request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request and wait for response"""
        from_agent = params.get("from", "")
        to_agent = params.get("to", "")
        content = params.get("content", "")

        message = {
            "from": from_agent,
            "to": to_agent,
            "content": content,
            "protocol": "request_response",
            "metadata": {},
            "timestamp": "now"
        }

        result = self._request_response_protocol(message)
        self.messages.append(message)

        return {
            "success": True,
            "request": message,
            "response": result.get("response"),
            "delivery": result
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.agents = {}
        self.messages = deque(maxlen=1000)
        self.channels = {}
        return True
