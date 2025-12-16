"""
Test script to verify the backend API works
"""

import sys
import time

print("="*60)
print("Testing Windows AI Backend API")
print("="*60)

# Test 1: Import modules
print("\n[1] Testing imports...")
try:
    from fastapi import FastAPI
    from uvicorn import run
    print("    ✓ FastAPI and Uvicorn available")
except ImportError as e:
    print(f"    ✗ Failed: {e}")
    print("    Install with: pip install fastapi uvicorn")
    sys.exit(1)

# Test 2: Import Windows AI API modules
print("\n[2] Testing Windows AI API modules...")
try:
    from windows_ai.api.server import app
    from windows_ai.api.chat_routes import router as chat_router
    from windows_ai.api.frontend_routes import router as frontend_router
    print("    ✓ All API modules loaded successfully")
except ImportError as e:
    print(f"    ✗ Failed: {e}")
    sys.exit(1)

# Test 3: Check routes
print("\n[3] Checking registered routes...")
try:
    routes = [route.path for route in app.routes]
    print(f"    ✓ Found {len(routes)} routes")
    
    # Check for key routes
    key_routes = ["/health", "/chat", "/chat/stream", "/conversations", "/plugins", "/models"]
    for route in key_routes:
        if any(r.startswith(route) for r in routes):
            print(f"    ✓ {route}")
        else:
            print(f"    ✗ {route} not found")
    
except Exception as e:
    print(f"    ✗ Failed: {e}")

# Test 4: Try to start server (will be stopped immediately)
print("\n[4] Starting test server on port 8010...")
print("    Server will start in 3 seconds...")
print("    Press Ctrl+C to stop")

import asyncio
import uvicorn

try:
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=8010,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    print("\n" + "="*60)
    print("Server starting successfully!")
    print("="*60)
    print("\nYou can now test the API endpoints:")
    print("  - Health: http://127.0.0.1:8010/health")
    print("  - Docs: http://127.0.0.1:8010/docs")
    print("  - Chat: POST to http://127.0.0.1:8010/chat")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    asyncio.run(server.serve())
    
except KeyboardInterrupt:
    print("\n\nServer stopped by user")
except Exception as e:
    print(f"\n✗ Failed to start server: {e}")
    import traceback
    traceback.print_exc()
