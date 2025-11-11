# Mesh Networking Guide

Comprehensive guide for Windows-AI mesh networking and distributed AI coordination.

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Mesh Architecture](#mesh-architecture)
4. [Leader Election](#leader-election)
5. [Distributed Task Queue](#distributed-task-queue)
6. [State Synchronization](#state-synchronization)
7. [AI Agent Coordination](#ai-agent-coordination)
8. [Security](#security)
9. [Examples](#examples)

## Overview

Windows-AI mesh networking enables:
- **Distributed AI processing** across multiple nodes
- **Automatic peer discovery** on local network
- **Leader election** for coordination
- **Distributed task queue** with load balancing
- **State synchronization** across nodes
- **Secure communication** with TLS encryption
- **Failover and redundancy** for reliability

## Getting Started

### Starting a Mesh Node

```python
from windows_ai.mesh.mesh_node import MeshNode

# Create node
node = MeshNode(
    node_id="node1",
    port=8765,
    use_tls=True,
    capabilities=['ai_inference', 'rag_search']
)

# Start node
node.start()
```

### Peer Discovery

Automatically discover other nodes:

```python
from windows_ai.mesh.peer_discovery import PeerDiscovery

discovery = PeerDiscovery(
    node_id=node.node_id,
    node_port=node.port,
    capabilities=node.capabilities
)

# Start discovery
discovery.start()

# Callback for new peers
def on_peer_discovered(peer):
    print(f"Found peer: {peer['node_id']} at {peer['address']}")
    node.add_peer(**peer)

discovery.add_discovery_callback(on_peer_discovered)
```

### Complete Setup

```python
from windows_ai.mesh.mesh_node import MeshNode
from windows_ai.mesh.peer_discovery import PeerDiscovery
from windows_ai.mesh.task_queue import DistributedTaskQueue
from windows_ai.mesh.state_sync import StateSync

# Create mesh node
node = MeshNode(port=8765, use_tls=True)
node.start()

# Start peer discovery
discovery = PeerDiscovery(node.node_id, node.port)
discovery.start()

# Create distributed task queue
task_queue = DistributedTaskQueue(node)
task_queue.start()

# Start state synchronization
state_sync = StateSync(node)
state_sync.start()
```

## Mesh Architecture

### Node Roles

**Leader**
- Coordinates mesh activities
- Sends heartbeats to followers
- Manages task distribution
- Elected automatically

**Follower**
- Receives heartbeats from leader
- Executes assigned tasks
- Participates in elections

**Candidate**
- Temporary role during election
- Requests votes from peers
- Becomes leader if receives majority

### Network Topology

```
        [Leader Node]
           /   |   \
         /     |     \
        /      |      \
   [Follower] [Follower] [Follower]
```

## Leader Election

### How It Works

1. **Normal Operation**: Leader sends heartbeats every 2 seconds
2. **Timeout Detection**: Follower detects missing heartbeats (5 second timeout)
3. **Start Election**: Follower becomes candidate, increments term, votes for self
4. **Request Votes**: Candidate requests votes from all peers
5. **Win Election**: Candidate with majority votes becomes new leader

### Election Example

```python
# Node automatically handles elections
node = MeshNode(
    election_timeout=5,      # 5 seconds without heartbeat triggers election
    heartbeat_interval=2     # Leader sends heartbeat every 2 seconds
)

# Check node role
status = node.get_status()
print(f"Role: {status['role']}")  # leader, follower, or candidate
print(f"Leader: {status['leader_id']}")
```

## Distributed Task Queue

### Submitting Tasks

```python
from windows_ai.mesh.task_queue import DistributedTaskQueue

task_queue = DistributedTaskQueue(mesh_node)
task_queue.start()

# Submit task
result = task_queue.submit_task(
    task_type="ai_inference",
    payload={"prompt": "Explain quantum computing"},
    priority=5
)

print(f"Task ID: {result['task_id']}")
print(f"Assigned to: {result['assigned_node']}")
```

### Task Handlers

Register handlers for task types:

```python
def handle_inference(payload):
    prompt = payload['prompt']
    # Process AI inference
    return {"result": "Generated response..."}

task_queue.register_handler("ai_inference", handle_inference)
```

### Load Balancing

Tasks automatically distributed based on:
- Current queue size
- Node capabilities
- Node availability
- Task priority

### Task Status

```python
# Get task status
status = task_queue.get_task_status(task_id)
print(status['task']['status'])  # pending, running, completed, failed

# Get queue statistics
stats = task_queue.get_queue_status()
print(f"Pending: {stats['pending']}")
print(f"Running: {stats['running']}")
print(f"Completed: {stats['completed']}")
```

## State Synchronization

### Setting State

```python
from windows_ai.mesh.state_sync import StateSync

state_sync = StateSync(mesh_node)
state_sync.start()

# Set shared state
state_sync.set("user_preferences", {
    "theme": "dark",
    "language": "en"
})
```

### Getting State

```python
# Get value
result = state_sync.get("user_preferences")
print(result['value'])

# Get all state
all_state = state_sync.get_all()
```

### Synchronization Strategy

- **Eventual consistency**: All nodes converge to same state
- **Last-write-wins**: Conflicts resolved by version number and timestamp
- **Automatic merging**: Periodic sync every 10 seconds
- **Update broadcasting**: Changes immediately sent to all peers

## AI Agent Coordination

### Distributed AI Inference

```python
from windows_ai.mesh.agent_coordinator import AgentCoordinator

coordinator = AgentCoordinator(mesh_node, task_queue)

# Distribute AI inference
result = coordinator.distribute_inference(
    model="llama-3",
    prompt="Write a poem about networks",
    temperature=0.7
)

print(f"Task ID: {result['task_id']}")
```

### Distributed RAG Search

```python
# Search across distributed vector databases
result = coordinator.distribute_rag_search(
    query="What is mesh networking?",
    top_k=5
)
```

### Capability Broadcasting

```python
# Advertise node capabilities
coordinator.broadcast_capability("text_generation", True)
coordinator.broadcast_capability("image_generation", False)

# Get mesh-wide capabilities
caps = coordinator.get_mesh_capabilities()
print(f"Available capabilities: {caps['capabilities']}")
```

## Security

### TLS Encryption

All mesh communication encrypted with TLS 1.3:

```python
# Enable TLS
node = MeshNode(use_tls=True)

# In production, configure with proper certificates
node.ssl_context.load_cert_chain("cert.pem", "key.pem")
```

### Authentication

```python
# Peer authentication
node.register_handler('auth_request', handle_auth)

def handle_auth(message):
    api_key = message.get('api_key')
    if validate_api_key(api_key):
        return {"status": "success", "authenticated": True}
    return {"status": "error", "message": "Invalid API key"}
```

### Network Isolation

```python
# Restrict mesh to specific network
discovery = PeerDiscovery(
    node_id=node_id,
    node_port=port,
    allowed_networks=["192.168.1.0/24"]
)
```

## Monitoring and Health

### Node Status

```python
status = node.get_status()
print(f"""
Node ID: {status['node_id']}
Role: {status['role']}
Leader: {status['leader_id']}
Peers: {status['peer_count']}
Running: {status['running']}
Term: {status['election_term']}
""")
```

### Mesh Health

```python
# Check all peers
for peer_id, peer in node.peers.items():
    print(f"{peer_id}: {peer.role} - Last seen: {peer.last_seen}")
```

### Task Queue Metrics

```python
stats = task_queue.get_queue_status()
print(f"Total tasks: {stats['total_tasks']}")
print(f"Success rate: {stats['completed']}/{stats['total_tasks']}")
```

## Failover and Redundancy

### Automatic Failover

- Leader failure automatically triggers new election
- Tasks redistributed to available nodes
- State recovered from other nodes

### Manual Failover

```python
# Gracefully stop leader
if node.role == NodeRole.LEADER:
    node.stop()  # Triggers election

# Start backup node
backup_node = MeshNode(port=8766)
backup_node.start()
```

## Performance Optimization

### Tuning Parameters

```python
node = MeshNode(
    election_timeout=5,       # Balance between responsiveness and stability
    heartbeat_interval=2,     # Shorter = more traffic, faster detection
)

task_queue = DistributedTaskQueue(node)
# Adjust worker threads for concurrency

state_sync = StateSync(node)
state_sync.sync_interval = 5  # Faster sync = more network traffic
```

### Load Distribution

```python
# Distribute compute-heavy tasks
for i in range(100):
    task_queue.submit_task("heavy_compute", {"data": i}, priority=5)

# Monitor load
stats = task_queue.get_queue_status()
print(f"Queue size: {stats['local_queue_size']}")
```

## Examples

### Multi-Node AI Cluster

```python
# Node 1 (Leader)
node1 = MeshNode(port=8765)
node1.start()

task_queue1 = DistributedTaskQueue(node1)
task_queue1.start()

coordinator1 = AgentCoordinator(node1, task_queue1)

# Node 2 (Worker)
node2 = MeshNode(port=8766)
node2.start()
node2.add_peer(node1.node_id, "localhost", 8765)

task_queue2 = DistributedTaskQueue(node2)
task_queue2.start()

# Submit from any node
coordinator1.distribute_inference(model="llama-3", prompt="Hello")
```

### Resilient Task Processing

```python
# Submit tasks with retry
def submit_with_retry(task_type, payload, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = task_queue.submit_task(task_type, payload)
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

### State-Based Coordination

```python
# Coordinate using shared state
state_sync.set("active_model", "llama-3-70b")
state_sync.set("batch_size", 32)

# All nodes read same config
config = state_sync.get("active_model")
model_name = config['value']
```

## Troubleshooting

### No Peers Discovered

**Problem**: Discovery not finding other nodes

**Solutions**:
- Check firewall allows UDP multicast (port 5007)
- Verify nodes on same network subnet
- Check multicast routing enabled
- Increase discovery time

### Election Loops

**Problem**: Constant re-elections

**Solutions**:
- Increase election_timeout (reduce sensitivity)
- Check network stability
- Verify heartbeat packets arriving
- Review logs for errors

### Task Timeouts

**Problem**: Tasks not completing

**Solutions**:
- Check node capacity
- Verify task handlers registered
- Increase task timeout
- Monitor node load

### State Inconsistency

**Problem**: Nodes have different state

**Solutions**:
- Reduce sync_interval
- Check network connectivity
- Verify clocks synchronized (NTP)
- Review merge conflicts in logs

## Best Practices

1. **Use TLS** for production deployments
2. **Monitor node health** continuously
3. **Set appropriate timeouts** based on network latency
4. **Implement retry logic** for critical tasks
5. **Balance load** across nodes
6. **Log extensively** for debugging
7. **Test failover** scenarios regularly
8. **Secure peer authentication** in untrusted networks

## API Reference

### MeshNode

- `start()` - Start mesh node
- `stop()` - Stop mesh node
- `add_peer()` - Add peer to mesh
- `send_to_peer()` - Send message to peer
- `get_status()` - Get node status

### DistributedTaskQueue

- `start()` - Start task queue
- `submit_task()` - Submit task
- `register_handler()` - Register task handler
- `get_task_status()` - Get task status
- `get_queue_status()` - Get queue stats

### StateSync

- `start()` - Start state sync
- `set()` - Set state value
- `get()` - Get state value
- `get_all()` - Get all state
- `delete()` - Delete state value

## Support

For issues and questions:
- GitHub: https://github.com/anthropics/windows-ai
- Documentation: https://docs.windows-ai.com
