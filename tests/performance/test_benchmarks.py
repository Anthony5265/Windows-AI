"""
Final Performance Benchmark Suite
Comprehensive performance testing for Windows AI
"""
import pytest
import asyncio
import time
from windows_ai.core.orchestrator import WindowsAI
from windows_ai.plugins.builtin.windows_os import windows_search_plugin
from windows_ai.integrations.ai_providers import AIProvidersManager

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_orchestrator_startup_performance():
    """Benchmark: Orchestrator initialization time"""
    start_time = time.time()
    
    orchestrator = WindowsAI()
    await orchestrator.initialize()
    
    end_time = time.time()
    startup_time = end_time - start_time
    
    # Should initialize in under 5 seconds
    assert startup_time < 5.0, f"Startup took {startup_time:.2f}s (expected < 5s)"
    print(f"\n✓ Orchestrator startup: {startup_time:.3f}s")

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_plugin_load_performance():
    """Benchmark: Plugin loading time"""
    plugin = windows_search_plugin.plugin
    
    start_time = time.time()
    await plugin.initialize()
    end_time = time.time()
    
    load_time = end_time - start_time
    
    # Should load in under 100ms
    assert load_time < 0.1, f"Plugin load took {load_time*1000:.2f}ms (expected < 100ms)"
    print(f"\n✓ Plugin load time: {load_time*1000:.3f}ms")

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_manager_initialization_performance():
    """Benchmark: Manager initialization time"""
    manager = AIProvidersManager()
    
    start_time = time.time()
    await manager.initialize()
    end_time = time.time()
    
    init_time = end_time - start_time
    
    # Should initialize in under 1 second
    assert init_time < 1.0, f"Manager init took {init_time:.2f}s (expected < 1s)"
    print(f"\n✓ Manager initialization: {init_time:.3f}s")

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_plugin_execution_performance():
    """Benchmark: Plugin execution time"""
    plugin = windows_search_plugin.plugin
    await plugin.initialize()
    await plugin.connect({})
    
    start_time = time.time()
    result = await plugin.execute("get_status", {})
    end_time = time.time()
    
    exec_time = end_time - start_time
    
    # Should execute in under 1 second
    assert exec_time < 1.0, f"Plugin execution took {exec_time:.2f}s (expected < 1s)"
    print(f"\n✓ Plugin execution: {exec_time:.3f}s")

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_concurrent_plugin_load_performance():
    """Benchmark: Concurrent plugin loading"""
    from windows_ai.plugins.builtin.windows_os import (
        windows_defender_plugin,
        windows_firewall_plugin,
        bitlocker_automation_plugin,
        windows_hello_plugin,
        windows_search_plugin
    )
    
    plugins = [
        windows_defender_plugin.plugin,
        windows_firewall_plugin.plugin,
        bitlocker_automation_plugin.plugin,
        windows_hello_plugin.plugin,
        windows_search_plugin.plugin
    ]
    
    start_time = time.time()
    await asyncio.gather(*[p.initialize() for p in plugins])
    end_time = time.time()
    
    load_time = end_time - start_time
    
    # Should load 5 plugins concurrently in under 500ms
    assert load_time < 0.5, f"Concurrent load took {load_time*1000:.2f}ms (expected < 500ms)"
    print(f"\n✓ Concurrent plugin load (5 plugins): {load_time*1000:.3f}ms")

@pytest.mark.benchmark
def test_memory_footprint():
    """Benchmark: Memory footprint"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    # Should use less than 500MB at this point
    assert memory_mb < 500, f"Memory usage {memory_mb:.2f}MB (expected < 500MB)"
    print(f"\n✓ Memory footprint: {memory_mb:.2f}MB")

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_api_response_time():
    """Benchmark: API response time simulation"""
    # Simulate API endpoint handling
    start_time = time.time()
    
    # Simulate plugin discovery and execution
    plugin = windows_search_plugin.plugin
    await plugin.initialize()
    result = await plugin.get_schema()
    
    end_time = time.time()
    response_time = end_time - start_time
    
    # Should respond in under 100ms
    assert response_time < 0.1, f"API response took {response_time*1000:.2f}ms (expected < 100ms)"
    print(f"\n✓ API response time: {response_time*1000:.3f}ms")

@pytest.mark.benchmark
def test_import_performance():
    """Benchmark: Module import time"""
    import importlib
    import sys
    
    # Clear module cache
    if 'windows_ai' in sys.modules:
        del sys.modules['windows_ai']
    
    start_time = time.time()
    importlib.import_module('windows_ai')
    end_time = time.time()
    
    import_time = end_time - start_time
    
    # Should import in under 2 seconds
    assert import_time < 2.0, f"Import took {import_time:.2f}s (expected < 2s)"
    print(f"\n✓ Module import time: {import_time:.3f}s")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "benchmark"])
