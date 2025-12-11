"""
Quick test script to verify the GUI backend is working
Run this AFTER starting the API server
"""

import requests
import json

API_BASE = "http://127.0.0.1:8010"

def test_endpoint(name, method, url, data=None):
    """Test an API endpoint"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        if response.status_code < 400:
            print(f"✅ {name}: {response.status_code}")
            return True
        else:
            print(f"❌ {name}: {response.status_code}")
            print(f"   Error: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ {name}: {str(e)}")
        return False

print("="*60)
print("Windows AI Backend API Test")
print("="*60)
print("\nMake sure the API server is running:")
print("  python -m windows_ai --api")
print("\n" + "="*60)

input("\nPress Enter when server is running...")

print("\n[1] Testing Health Check...")
test_endpoint("Health Check", "GET", f"{API_BASE}/health")

print("\n[2] Testing Chat Endpoints...")
test_endpoint("Chat (non-streaming)", "POST", f"{API_BASE}/chat", {
    "message": "Hello, test message!"
})

print("\n[3] Testing Conversation Endpoints...")
test_endpoint("List Conversations", "GET", f"{API_BASE}/conversations")

print("\n[4] Testing Plugin Endpoints...")
test_endpoint("List Plugins", "GET", f"{API_BASE}/plugins")
test_endpoint("Search Plugins", "GET", f"{API_BASE}/plugins?search=openai")

print("\n[5] Testing Model Endpoints...")
test_endpoint("List Models", "GET", f"{API_BASE}/models")
test_endpoint("Filter Models", "GET", f"{API_BASE}/models?category=general")

print("\n[6] Testing API Documentation...")
test_endpoint("OpenAPI Docs", "GET", f"{API_BASE}/docs")

print("\n" + "="*60)
print("Testing Complete!")
print("="*60)

print("\n📝 Next Steps:")
print("  1. All endpoints working? Rebuild the executable:")
print("     python build_exe.py")
print("\n  2. Then run the Electron GUI:")
print("     cd apps/gui")
print("     npm start")
print("\n  3. The GUI should now fully work with the backend!")
print("\n  4. Try chatting, viewing plugins, and exploring models")
print("\n  5. To enable real AI responses:")
print("     - Go to Settings")
print("     - Add your API keys (OpenAI, Anthropic, etc.)")
print("     - Or install Ollama for local models")
print("="*60)
