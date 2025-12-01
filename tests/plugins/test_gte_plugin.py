#!/usr/bin/env python3
"""
Test script for GTE Embedding Plugin
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.ai_models.gte_plugin import GTEPlugin

def test_gte_plugin():
    """Test the GTE plugin functionality"""
    print("Testing GTE Embedding Plugin...")

    # Initialize the plugin
    plugin = GTEPlugin()

    # Test initialization
    print("\n1. Testing initialization...")
    success = plugin.initialize()
    if success:
        print("[OK] Plugin initialized successfully")
    else:
        print("[FAIL] Plugin initialization failed (check sentence-transformers installation)")
        return False

    # Test embedding single text
    print("\n2. Testing embed single text...")
    embed_params = {
        "texts": "Hello world"
    }
    result = plugin.execute("embed", embed_params)
    if "error" not in result:
        print(f"[OK] Generated {result.get('count', 0)} embedding(s) with {result.get('dimensions', 0)} dimensions")
    else:
        print(f"[FAIL] Embedding failed: {result.get('error')}")

    # Test embedding multiple texts
    print("\n3. Testing embed multiple texts...")
    embed_params = {
        "texts": ["Hello world", "This is a test", "GTE embeddings are great"]
    }
    result = plugin.execute("embed", embed_params)
    if "error" not in result:
        print(f"[OK] Generated {result.get('count', 0)} embeddings with {result.get('dimensions', 0)} dimensions")
    else:
        print(f"[FAIL] Embedding failed: {result.get('error')}")

    # Test embed_query
    print("\n4. Testing embed_query...")
    query_params = {
        "query": "What is the capital of France?"
    }
    result = plugin.execute("embed_query", query_params)
    if "error" not in result:
        print(f"[OK] Generated query embedding with {result.get('dimensions', 0)} dimensions")
    else:
        print(f"[FAIL] Query embedding failed: {result.get('error')}")

    # Test embed_documents
    print("\n5. Testing embed_documents...")
    doc_params = {
        "documents": ["Paris is the capital of France.", "Berlin is the capital of Germany."]
    }
    result = plugin.execute("embed_documents", doc_params)
    if "error" not in result:
        print(f"[OK] Generated {result.get('count', 0)} document embeddings with {result.get('dimensions', 0)} dimensions")
    else:
        print(f"[FAIL] Document embedding failed: {result.get('error')}")

    # Cleanup
    plugin.cleanup()
    print("\n[OK] Plugin cleanup completed")

    return True

if __name__ == "__main__":
    try:
        test_gte_plugin()
        print("\n[SUCCESS] GTE plugin test completed!")
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        sys.exit(1)