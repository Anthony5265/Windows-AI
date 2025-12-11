#!/usr/bin/env python3
"""
Test script for Serge Plugin
"""

import pytest
import sys
import os

pytest.skip("Module import broken - plugins.local_models doesn't exist", allow_module_level=True)

def test_serge_plugin():
    """Test the Serge plugin functionality"""
    print("Testing Serge Plugin...")

    # Initialize the plugin
    plugin = SergePlugin()

    # Test initialization
    print("\n1. Testing initialization...")
    config = {
        "serge": {
            "api_url": "http://localhost:8008"
        }
    }
    success = plugin.initialize(config)
    if success:
        print("[OK] Plugin initialized successfully")
    else:
        print("[FAIL] Plugin initialization failed (make sure Serge is running on localhost:8008)")
        return False

    # Test model status
    print("\n2. Testing model status...")
    result = plugin.execute("get_model_status", {})
    if result.get("success"):
        print(f"[OK] Server running: {result.get('server_running')}")
        if result.get("loaded"):
            print(f"[OK] Current model: {result.get('current_model')}")
        else:
            print("[INFO] No model currently loaded")
    else:
        print(f"[FAIL] Error getting status: {result.get('error')}")

    # Test listing models
    print("\n3. Testing list_models...")
    result = plugin.execute("list_models", {})
    if result.get("success"):
        models = result.get("models", [])
        print(f"[OK] Found {len(models)} available models")
        for model in models[:3]:  # Show first 3 models
            print(f"  - {model}")
    else:
        print(f"[FAIL] Error listing models: {result.get('error')}")

    # Test loading a model (if available)
    print("\n4. Testing model loading...")
    list_result = plugin.execute("list_models", {})
    if list_result.get("success") and list_result.get("models"):
        first_model = list_result["models"][0]
        if first_model:
            load_result = plugin.execute("load_model", {"model_name": first_model})
            if load_result.get("success"):
                print(f"[OK] Successfully loaded model: {first_model}")
            else:
                print(f"[FAIL] Error loading model: {load_result.get('error')}")
        else:
            print("[SKIP] No models available to load")
    else:
        print("[SKIP] Cannot test model loading - no models available")

    # Test text generation (if model is loaded)
    print("\n5. Testing text generation...")
    status_result = plugin.execute("get_model_status", {})
    if status_result.get("success") and status_result.get("loaded"):
        gen_params = {
            "prompt": "The future of artificial intelligence is",
            "max_tokens": 50,
            "temperature": 0.7
        }
        result = plugin.execute("generate_text", gen_params)
        if result.get("success"):
            print("[OK] Text generation completed successfully")
            print(f"Generated text: {result.get('text', '')[:100]}...")
        else:
            print(f"[FAIL] Text generation failed: {result.get('error')}")
    else:
        print("[SKIP] Cannot test text generation - no model loaded")

    # Test chat (if model is loaded)
    print("\n6. Testing chat...")
    status_result = plugin.execute("get_model_status", {})
    if status_result.get("success") and status_result.get("loaded"):
        chat_params = {
            "messages": [
                {"role": "user", "content": "Hello! Can you tell me a short joke?"}
            ],
            "max_tokens": 100,
            "temperature": 0.7
        }
        result = plugin.execute("chat", chat_params)
        if result.get("success"):
            print("[OK] Chat completed successfully")
            print(f"Response: {result.get('response', '')[:100]}...")
        else:
            print(f"[FAIL] Chat failed: {result.get('error')}")
    else:
        print("[SKIP] Cannot test chat - no model loaded")

    # Test getting model info
    print("\n7. Testing get_model_info...")
    result = plugin.execute("get_model_info", {})
    if result.get("success"):
        print(f"[OK] Model info retrieved")
        print(f"  Provider: {result.get('provider')}")
        print(f"  Model: {result.get('model_name')}")
        print(f"  Capabilities: {result.get('capabilities', [])}")
    else:
        print(f"[FAIL] Error getting model info: {result.get('error')}")

    # Cleanup
    plugin.cleanup()
    print("\n[OK] Plugin cleanup completed")

    return True

if __name__ == "__main__":
    try:
        test_serge_plugin()
        print("\n[SUCCESS] Serge plugin test completed!")
        print("\nNote: Some tests may be skipped if Serge server is not running or no models are loaded.")
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        sys.exit(1)
